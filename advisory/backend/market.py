"""Market data: 13 months of daily candles per stock.

Live from Yahoo Finance (yfinance) when reachable, otherwise a dummy random-walk
history. One batch download covers all stocks and is cached for 5 minutes, so
many page loads cost one Yahoo call. The latest candle's close is the current
price (Yahoo's own quotes are delayed ~15 min for NSE).
"""

import logging
import math
import random
import threading
import time
from datetime import date, timedelta

from universe import UNIVERSE

logging.getLogger("yfinance").setLevel(logging.CRITICAL)

CACHE_TTL = 300
HISTORY_DAYS = 400
_lock = threading.Lock()
_cache: dict = {"at": 0.0, "bars": None, "source": None}


def _fetch_live(symbols: list[str], start: date) -> dict[str, list[dict]]:
    import yfinance as yf

    tickers = [f"{s}.NS" for s in symbols]  # NSE listing on Yahoo
    df = yf.download(tickers, start=start.isoformat(), interval="1d", progress=False,
                     auto_adjust=False, threads=True, timeout=10)
    if df is None or df.empty:
        return {}
    out = {}
    for sym, t in zip(symbols, tickers):
        try:
            frame = df[[("Open", t), ("High", t), ("Low", t), ("Close", t)]].dropna()
        except KeyError:
            continue
        if frame.empty:
            continue
        out[sym] = [
            {"date": idx.date().isoformat(), "open": round(float(o), 2), "high": round(float(h), 2),
             "low": round(float(l), 2), "close": round(float(c), 2)}
            for idx, (o, h, l, c) in zip(frame.index, frame.itertuples(index=False))
        ]
    return out


def _dummy_history(symbol: str, start: date) -> list[dict]:
    """Deterministic random walk: the same stock gives the same history on every run,
    so charts and call outcomes stay consistent between restarts."""
    info = UNIVERSE[symbol]
    rng = random.Random(symbol)
    vol = info["vol"]
    days = [start + timedelta(d) for d in range((date.today() - start).days + 1)]
    days = [d for d in days if d.weekday() < 5]
    # Walk backwards-anchored: end near the base price.
    price = info["base"] * math.exp(-rng.gauss(0.06, 0.12))
    bars = []
    for d in days:
        o = price * (1 + rng.gauss(0, vol / 3))
        c = o * (1 + rng.gauss(0.0004, vol))
        h = max(o, c) * (1 + abs(rng.gauss(0, vol / 2)))
        l = min(o, c) * (1 - abs(rng.gauss(0, vol / 2)))
        bars.append({"date": d.isoformat(), "open": round(o, 2), "high": round(h, 2),
                     "low": round(l, 2), "close": round(c, 2)})
        price = c
    return bars


def get_market() -> tuple[dict[str, list[dict]], str]:
    """Returns ({symbol: daily bars oldest→newest}, source) with source live|mixed|dummy."""
    with _lock:  # one download at a time, even if several requests arrive together
        if _cache["bars"] is not None and time.time() - _cache["at"] < CACHE_TTL:
            return _cache["bars"], _cache["source"]

        start = date.today() - timedelta(days=HISTORY_DAYS)
        symbols = list(UNIVERSE)
        try:
            live = _fetch_live(symbols, start)
        except Exception:
            live = {}

        bars = {s: live.get(s) or _dummy_history(s, start) for s in symbols}
        source = "live" if len(live) == len(symbols) else "mixed" if live else "dummy"
        _cache.update(at=time.time(), bars=bars, source=source)
        return bars, source


def quote(bars: list[dict]) -> dict:
    last, prev = bars[-1], bars[-2] if len(bars) > 1 else bars[-1]
    return {"price": last["close"], "prev_close": prev["close"]}


def annual_volatility(bars: list[dict], lookback: int = 126) -> float:
    """Annualised volatility (%) from the last ~6 months of daily closes."""
    closes = [b["close"] for b in bars[-(lookback + 1):]]
    rets = [math.log(b / a) for a, b in zip(closes, closes[1:]) if a > 0]
    if len(rets) < 2:
        return 0.0
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
    return round(math.sqrt(var) * math.sqrt(252) * 100, 1)
