"""Market data: ~2 years of daily candles for every stock and index.

Live from Yahoo Finance (yfinance) when reachable, otherwise a deterministic dummy
history. One batch download covers everything and is cached for 5 minutes, so many
page loads cost one Yahoo call. The latest candle's close is the current price
(Yahoo's NSE data is delayed ~15 minutes).
"""

import logging
import math
import random
import threading
import time
from datetime import date, timedelta

from universe import INDICES, STOCKS, yahoo_ticker

logging.getLogger("yfinance").setLevel(logging.CRITICAL)

CACHE_TTL = 300
HISTORY_DAYS = 700  # 200-DMA needs ~10 months of warm-up before a 12-month backtest
_lock = threading.Lock()
_cache: dict = {"at": 0.0, "bars": None, "source": None}


def _fetch_live(keys: list[str], start: date) -> dict[str, list[dict]]:
    import yfinance as yf

    tickers = [yahoo_ticker(k) for k in keys]
    df = yf.download(tickers, start=start.isoformat(), interval="1d", progress=False,
                     auto_adjust=False, threads=True, timeout=20)
    if df is None or df.empty:
        return {}
    out = {}
    for key, t in zip(keys, tickers):
        try:
            frame = df[[("Open", t), ("High", t), ("Low", t), ("Close", t), ("Volume", t)]]
        except KeyError:
            continue
        frame = frame.dropna(subset=[("Close", t)])
        if frame.empty:
            continue
        out[key] = [
            {"date": idx.date().isoformat(), "open": round(float(o), 2), "high": round(float(h), 2),
             "low": round(float(l), 2), "close": round(float(c), 2),
             "volume": 0 if v != v else int(v)}  # v != v is True for NaN
            for idx, (o, h, l, c, v) in zip(frame.index, frame.itertuples(index=False))
        ]
    return out


def _dummy_history(key: str, start: date) -> list[dict]:
    """Deterministic random walk: the same instrument gives the same history on every run,
    so charts and call outcomes stay consistent between restarts."""
    if key in STOCKS:
        base, vol, base_volume = STOCKS[key]["base"], STOCKS[key]["vol"], 2_000_000
    else:
        _, _, _, base, vol = INDICES[key]
        base_volume = 0
    rng = random.Random(key)
    days = [start + timedelta(d) for d in range((date.today() - start).days + 1)]
    days = [d for d in days if d.weekday() < 5]
    price = base
    drift = rng.gauss(0.0003, 0.0004)
    bars = []
    for d in days:
        o = price * (1 + rng.gauss(0, vol / 3))
        c = o * (1 + rng.gauss(drift, vol))
        h = max(o, c) * (1 + abs(rng.gauss(0, vol / 2)))
        l = min(o, c) * (1 - abs(rng.gauss(0, vol / 2)))
        # Volume: log-normal around the base, bigger on big-move days.
        v = int(base_volume * math.exp(rng.gauss(0, 0.35)) * (1 + 25 * abs(c / o - 1))) if base_volume else 0
        bars.append({"date": d.isoformat(), "open": round(o, 2), "high": round(h, 2),
                     "low": round(l, 2), "close": round(c, 2), "volume": v})
        price = c
    # Anchor: rescale so the latest close lands within ~5% of the base price. Scaling every
    # price by one factor keeps all the daily moves (and so every indicator signal) intact.
    factor = base * math.exp(rng.gauss(0, 0.04)) / bars[-1]["close"]
    for b in bars:
        for f in ("open", "high", "low", "close"):
            b[f] = round(b[f] * factor, 2)
    return bars


def get_market() -> tuple[dict[str, list[dict]], str]:
    """({key: daily bars oldest→newest}, source) — source is live | mixed | dummy."""
    with _lock:  # one download at a time, even if several requests arrive together
        if _cache["bars"] is not None and time.time() - _cache["at"] < CACHE_TTL:
            return _cache["bars"], _cache["source"]

        start = date.today() - timedelta(days=HISTORY_DAYS)
        keys = list(STOCKS) + list(INDICES)
        try:
            live = _fetch_live(keys, start)
        except Exception:
            live = {}

        bars = {k: live.get(k) or _dummy_history(k, start) for k in keys}
        live_stocks = sum(k in live for k in STOCKS)
        source = "live" if live_stocks == len(STOCKS) else "mixed" if live else "dummy"
        _cache.update(at=time.time(), bars=bars, source=source)
        return bars, source


def quote(bars: list[dict]) -> dict:
    last, prev = bars[-1], bars[-2] if len(bars) > 1 else bars[-1]
    return {"price": last["close"], "prev_close": prev["close"]}
