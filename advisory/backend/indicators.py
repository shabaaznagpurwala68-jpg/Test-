"""Technical indicators, computed from daily candles with standard definitions.

- SMA(n): average of the last n closes.
- EMA(n): exponential average, smoothing 2/(n+1), seeded with the SMA of the first n values.
- RSI(14): Wilder's method — average gain vs average loss over 14 days, on a 0–100 scale.
- MACD(12, 26, 9): EMA12 − EMA26; signal line = EMA9 of MACD; histogram = MACD − signal.
- ATR(14): Wilder's average of the true range (the day's full range including any gap).
Every series lines up with the bars; values are None until there is enough history.
"""

import math


def sma(values: list[float], n: int) -> list[float | None]:
    out, total = [None] * len(values), 0.0
    for i, v in enumerate(values):
        total += v
        if i >= n:
            total -= values[i - n]
        if i >= n - 1:
            out[i] = total / n
    return out


def ema(values: list[float | None], n: int) -> list[float | None]:
    out = [None] * len(values)
    first = next((i for i, v in enumerate(values) if v is not None), None)
    if first is None or len(values) - first < n:
        return out
    k = 2 / (n + 1)
    e = sum(values[first:first + n]) / n
    out[first + n - 1] = e
    for i in range(first + n, len(values)):
        e = values[i] * k + e * (1 - k)
        out[i] = e
    return out


def _wilder(values: list[float], n: int, start: int) -> list[float | None]:
    """Wilder smoothing of values[start:], seeded with a simple average of the first n."""
    out = [None] * len(values)
    if len(values) - start < n:
        return out
    avg = sum(values[start:start + n]) / n
    out[start + n - 1] = avg
    for i in range(start + n, len(values)):
        avg = (avg * (n - 1) + values[i]) / n
        out[i] = avg
    return out


def rsi(closes: list[float], n: int = 14) -> list[float | None]:
    gains = [0.0] + [max(closes[i] - closes[i - 1], 0) for i in range(1, len(closes))]
    losses = [0.0] + [max(closes[i - 1] - closes[i], 0) for i in range(1, len(closes))]
    ag, al = _wilder(gains, n, 1), _wilder(losses, n, 1)
    out = [None] * len(closes)
    for i in range(len(closes)):
        if ag[i] is not None:
            out[i] = 100.0 if al[i] == 0 else 100 - 100 / (1 + ag[i] / al[i])
    return out


def macd(closes: list[float], fast: int = 12, slow: int = 26, signal: int = 9):
    ef, es = ema(closes, fast), ema(closes, slow)
    line = [f - s if f is not None and s is not None else None for f, s in zip(ef, es)]
    sig = ema(line, signal)
    hist = [m - s if m is not None and s is not None else None for m, s in zip(line, sig)]
    return line, sig, hist


def atr(bars: list[dict], n: int = 14) -> list[float | None]:
    tr = [bars[0]["high"] - bars[0]["low"]] + [
        max(b["high"] - b["low"], abs(b["high"] - p["close"]), abs(b["low"] - p["close"]))
        for p, b in zip(bars, bars[1:])
    ]
    return _wilder(tr, n, 0)


def _prior(values: list[float], n: int, fn) -> list[float | None]:
    """fn over the n values BEFORE each bar (today excluded) — for breakout and volume checks."""
    return [fn(values[i - n:i]) if i >= n else None for i in range(len(values))]


def compute(bars: list[dict]) -> dict[str, list]:
    closes = [b["close"] for b in bars]
    volumes = [b["volume"] for b in bars]
    line, sig, hist = macd(closes)
    return {
        "date": [b["date"] for b in bars],
        "close": closes,
        "high": [b["high"] for b in bars],
        "low": [b["low"] for b in bars],
        "volume": volumes,
        "sma20": sma(closes, 20),
        "sma50": sma(closes, 50),
        "sma200": sma(closes, 200),
        "rsi": rsi(closes),
        "macd": line,
        "macd_signal": sig,
        "macd_hist": hist,
        "atr": atr(bars),
        "vol_avg20": _prior(volumes, 20, lambda w: sum(w) / len(w)),
        "high20": _prior([b["high"] for b in bars], 20, max),
        "high252": _prior([b["high"] for b in bars], 252, max),
        "low252": _prior([b["low"] for b in bars], 252, min),
    }


def annual_volatility(closes: list[float], lookback: int = 126) -> float:
    """Annualised volatility (%) from the last ~6 months of daily closes."""
    window = closes[-(lookback + 1):]
    rets = [math.log(b / a) for a, b in zip(window, window[1:]) if a > 0]
    if len(rets) < 2:
        return 0.0
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
    return round(math.sqrt(var) * math.sqrt(252) * 100, 1)
