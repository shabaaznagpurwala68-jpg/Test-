"""Markets dashboard: index snapshots, breadth, scanners and a technical stock table.

All figures are calculated from daily candles. Breadth and scanners cover our 50-stock
universe (approximately the Nifty 50), not the whole market.
"""

from universe import INDICES, STOCKS


def _pct(a: float, b: float | None) -> float | None:
    return round((a - b) / b * 100, 2) if b else None


def _cross(fast: list, slow: list, i: int, lookback: int, up: bool) -> bool:
    for j in range(i - lookback + 1, i + 1):
        if None in (fast[j], slow[j], fast[j - 1], slow[j - 1]):
            continue
        if up and fast[j] > slow[j] and fast[j - 1] <= slow[j - 1]:
            return True
        if not up and fast[j] < slow[j] and fast[j - 1] >= slow[j - 1]:
            return True
    return False


def snapshot(bars: list[dict], ind: dict) -> dict:
    i = len(bars) - 1
    c = bars[i]["close"]
    year_start = next((b["close"] for b in reversed(bars) if b["date"][:4] < bars[i]["date"][:4]), None)
    hi = max(b["high"] for b in bars[-252:])
    lo = min(b["low"] for b in bars[-252:])
    r, s50, s200 = ind["rsi"][i], ind["sma50"][i], ind["sma200"][i]
    return {
        "last": c,
        "date": bars[i]["date"],
        "chg_1d": _pct(c, bars[i - 1]["close"]),
        "chg_1w": _pct(c, bars[i - 5]["close"]),
        "chg_1m": _pct(c, bars[i - 21]["close"]),
        "chg_ytd": _pct(c, year_start),
        "rsi": r and round(r, 1),
        "vs_sma50": _pct(c, s50),
        "vs_sma200": _pct(c, s200),
        "high_52w": hi,
        "low_52w": lo,
        "from_high": _pct(c, hi),
        "from_low": _pct(c, lo),
        "trend": ("Uptrend" if c > s50 > s200 else "Downtrend" if c < s50 < s200 else "Sideways") if s50 and s200 else None,
        "spark": [b["close"] for b in bars[-90:]],
    }


SCANNERS = {
    "HIGH_52W": ("52-week high breakout", "Today's high is above every high of the past year."),
    "NEAR_LOW_52W": ("Near 52-week low", "Closing within 5% of the lowest price of the past year."),
    "GOLDEN_CROSS": ("Golden cross", "50-DMA crossed above 200-DMA in the last 5 days — a long-term bullish signal."),
    "DEATH_CROSS": ("Death cross", "50-DMA crossed below 200-DMA in the last 5 days — a long-term bearish signal."),
    "RSI_OVERBOUGHT": ("RSI overbought", "RSI(14) above 70: strong run-up, may be stretched."),
    "RSI_OVERSOLD": ("RSI oversold", "RSI(14) below 30: sharp fall, may be stretched to the downside."),
    "VOLUME_SURGE": ("Volume surge", "Volume at least 2× its 20-day average."),
    "MACD_BULLISH": ("MACD bullish crossover", "MACD crossed above its signal line in the last 3 days."),
    "MACD_BEARISH": ("MACD bearish crossover", "MACD crossed below its signal line in the last 3 days."),
}


def dashboard(market: dict[str, list[dict]], indicators: dict[str, dict]) -> dict:
    indices = [{"key": k, "name": name, "group": group, **snapshot(market[k], indicators[k])}
               for k, (_, name, group, _, _) in INDICES.items()]

    stocks, hits = [], {k: [] for k in SCANNERS}
    for sym, info in STOCKS.items():
        bars, ind = market[sym], indicators[sym]
        i = len(bars) - 1
        s = snapshot(bars, ind)
        va = ind["vol_avg20"][i]
        vol_ratio = round(bars[i]["volume"] / va, 2) if va else None
        row = {"symbol": sym, "name": info["name"], "sector": info["sector"], **s, "vol_ratio": vol_ratio}
        row.pop("spark")
        stocks.append(row)

        item = {"symbol": sym, "name": info["name"], "last": s["last"], "chg_1d": s["chg_1d"]}
        r = s["rsi"]
        if ind["high252"][i] and bars[i]["high"] > ind["high252"][i]:
            hits["HIGH_52W"].append({**item, "metric": f"52W high ₹{s['high_52w']:,.2f}"})
        if s["from_low"] is not None and s["from_low"] <= 5:
            hits["NEAR_LOW_52W"].append({**item, "metric": f"{s['from_low']:.1f}% above 52W low"})
        if _cross(ind["sma50"], ind["sma200"], i, 5, up=True):
            hits["GOLDEN_CROSS"].append({**item, "metric": "50-DMA above 200-DMA"})
        if _cross(ind["sma50"], ind["sma200"], i, 5, up=False):
            hits["DEATH_CROSS"].append({**item, "metric": "50-DMA below 200-DMA"})
        if r is not None and r > 70:
            hits["RSI_OVERBOUGHT"].append({**item, "metric": f"RSI {r:.1f}"})
        if r is not None and r < 30:
            hits["RSI_OVERSOLD"].append({**item, "metric": f"RSI {r:.1f}"})
        if vol_ratio and vol_ratio >= 2:
            hits["VOLUME_SURGE"].append({**item, "metric": f"{vol_ratio:.1f}× avg volume"})
        if _cross(ind["macd"], ind["macd_signal"], i, 3, up=True):
            hits["MACD_BULLISH"].append({**item, "metric": "MACD above signal"})
        if _cross(ind["macd"], ind["macd_signal"], i, 3, up=False):
            hits["MACD_BEARISH"].append({**item, "metric": "MACD below signal"})

    n = len(stocks)
    breadth = {
        "total": n,
        "advances": sum((s["chg_1d"] or 0) > 0 for s in stocks),
        "declines": sum((s["chg_1d"] or 0) < 0 for s in stocks),
        "unchanged": sum((s["chg_1d"] or 0) == 0 for s in stocks),
        "above_sma50_pct": round(sum((s["vs_sma50"] or 0) > 0 for s in stocks) / n * 100, 1),
        "above_sma200_pct": round(sum((s["vs_sma200"] or 0) > 0 for s in stocks) / n * 100, 1),
        "new_highs": len(hits["HIGH_52W"]),
        "near_lows": len(hits["NEAR_LOW_52W"]),
        "avg_rsi": round(sum(s["rsi"] or 50 for s in stocks) / n, 1),
    }
    scanners = [{"key": k, "title": t, "description": d, "items": hits[k]} for k, (t, d) in SCANNERS.items()]
    return {"indices": indices, "breadth": breadth, "scanners": scanners, "stocks": stocks}
