"""Stock prices: live from Yahoo Finance (yfinance) with a dummy fallback.

yfinance is unofficial and rate-limited, so results are cached for 5 minutes:
many page loads cost one Yahoo call. Any symbol Yahoo can't return gets a dummy
price, and the response says which source was used.
"""

import logging
import random
import time

logging.getLogger("yfinance").setLevel(logging.CRITICAL)

CACHE_TTL = 300
_cache: dict = {"at": 0.0, "key": None, "prices": None, "source": None}


def _yahoo_symbol(symbol: str) -> str:
    return f"{symbol}.NS"  # NSE listing on Yahoo


def _fetch_live(symbols: list[str]) -> dict:
    import yfinance as yf

    tickers = [_yahoo_symbol(s) for s in symbols]
    df = yf.download(tickers, period="5d", interval="1d", progress=False,
                     auto_adjust=False, threads=True, timeout=8)
    if df is None or df.empty:
        return {}
    closes = df["Close"]
    out = {}
    for sym, t in zip(symbols, tickers):
        if t not in closes:
            continue
        col = closes[t].dropna()
        if col.empty:
            continue
        last = float(col.iloc[-1])
        prev = float(col.iloc[-2]) if len(col) > 1 else last
        out[sym] = {"price": round(last, 2), "prev_close": round(prev, 2)}
    return out


def _dummy(symbol: str, base: float) -> dict:
    # Moves every 5 minutes, repeatable within a window, so the page "ticks" in fallback mode.
    rng = random.Random(f"{symbol}-{int(time.time() // CACHE_TTL)}")
    price = base * (1 + rng.uniform(-0.07, 0.09))
    prev = price / (1 + rng.uniform(-0.02, 0.02))
    return {"price": round(price, 2), "prev_close": round(prev, 2)}


def get_prices(fallback: dict[str, float]) -> tuple[dict, str]:
    """fallback maps symbol -> base price for dummy mode. Returns (prices, source)."""
    key = tuple(sorted(fallback))
    if _cache["key"] == key and time.time() - _cache["at"] < CACHE_TTL:
        return _cache["prices"], _cache["source"]

    try:
        live = _fetch_live(list(fallback))
    except Exception:
        live = {}

    prices = {s: live.get(s) or _dummy(s, base) for s, base in fallback.items()}
    if len(live) == len(fallback):
        source = "live"
    elif live:
        source = "mixed"
    else:
        source = "dummy"

    _cache.update(at=time.time(), key=key, prices=prices, source=source)
    return prices, source
