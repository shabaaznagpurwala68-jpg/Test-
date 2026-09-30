"""Technical setups: fixed checklists run on every stock, every trading day.

A setup fires when ALL its checks pass on a day's close. Levels come from rules:
  entry     = that day's close
  stop loss = entry − 2 × ATR(14)      (adapts to how much the stock normally moves)
  target    = entry + 2 × (entry − SL) (a fixed 1:2 risk-reward)
  horizon   = 60 days
One open call per stock at a time, and a 5-day cooling-off after a call closes.

The same engine builds the 12-month track record (replaying past days) and issues
new calls as new candles arrive, so the track record measures exactly this method.
"""

import json
from datetime import date, datetime, timedelta, timezone

from db import get_conn, get_meta, set_meta
from evaluator import close_finished_calls, evaluate
from fmt import inr
from universe import STOCKS

HORIZON_DAYS = 60
BACKTEST_DAYS = 365
ATR_MULTIPLE = 2
REWARD_MULTIPLE = 2
COOLDOWN_BARS = 5
IST = timezone(timedelta(hours=5, minutes=30))

SETUPS = {
    "TREND_BREAKOUT": {
        "name": "Trend Breakout",
        "idea": "A stock already in an uptrend breaks above its recent range on strong volume — "
                "buyers are pushing into new territory.",
        "rules": ["Close above the highest high of the prior 20 days",
                  "Price above 50-DMA, and 50-DMA above 200-DMA (uptrend)",
                  "Volume at least 1.5× its 20-day average",
                  "RSI(14) between 55 and 75 (momentum, not yet overbought)"],
        "risk_note": "Trend-following. Works best in trending markets; false breakouts are the main risk.",
    },
    "MACD_MOMENTUM": {
        "name": "MACD Momentum",
        "idea": "Short-term momentum turns up (MACD crosses above its signal line) while the "
                "long-term trend is still up.",
        "rules": ["MACD crossed above its signal line within the last 3 days",
                  "Price above its 200-DMA (long-term uptrend)",
                  "RSI(14) above 50"],
        "risk_note": "Momentum. Crossovers in sideways markets can whipsaw.",
    },
    "OVERSOLD_BOUNCE": {
        "name": "Oversold Bounce",
        "idea": "A stock in a long-term uptrend falls sharply (RSI below 30), then starts recovering — "
                "buying a dip within an uptrend.",
        "rules": ["RSI(14) was below 30 and crossed back above 30 within the last 3 days",
                  "Price still above its 200-DMA (long-term uptrend intact)"],
        "risk_note": "Counter-trend: buys into weakness, so it is rated one risk level higher.",
    },
}


def _chk(label: str, value: str, requirement: str, passed: bool) -> dict:
    return {"label": label, "value": value, "requirement": requirement, "passed": bool(passed)}


def _checks(setup: str, ind: dict, i: int) -> list[dict] | None:
    """The setup's checklist evaluated on bar i, or None if there isn't enough history yet."""
    c, s50, s200, r = ind["close"][i], ind["sma50"][i], ind["sma200"][i], ind["rsi"][i]
    if None in (s50, s200, r, ind["atr"][i]) or i < 3:
        return None

    if setup == "TREND_BREAKOUT":
        h20, va, v = ind["high20"][i], ind["vol_avg20"][i], ind["volume"][i]
        if h20 is None or not va:
            return None
        return [
            _chk("Breakout above 20-day high", f"{inr(c)} vs {inr(h20)}", "Close > prior 20-day high", c > h20),
            _chk("Uptrend", f"{inr(c, 0)} > {inr(s50, 0)} > {inr(s200, 0)}", "Price > 50-DMA > 200-DMA", c > s50 > s200),
            _chk("Volume surge", f"{v / va:.1f}× average", "≥ 1.5× 20-day average", v >= 1.5 * va),
            _chk("RSI(14)", f"{r:.1f}", "55 to 75", 55 <= r <= 75),
        ]

    if setup == "MACD_MOMENTUM":
        m, sg = ind["macd"], ind["macd_signal"]
        if None in (m[i - 3], sg[i - 3]):
            return None
        cross_ago = next((i - j for j in (i, i - 1, i - 2) if m[j] > sg[j] and m[j - 1] <= sg[j - 1]), None)
        crossed = cross_ago is not None and m[i] > sg[i]
        when = "today" if cross_ago == 0 else f"{cross_ago} day{'s' if cross_ago > 1 else ''} ago" if crossed else "no recent cross"
        return [
            _chk("MACD bullish crossover", f"{when} (MACD {m[i]:.2f} vs signal {sg[i]:.2f})", "Within the last 3 days", crossed),
            _chk("Long-term uptrend", f"{inr(c, 0)} vs 200-DMA {inr(s200, 0)}", "Price > 200-DMA", c > s200),
            _chk("RSI(14)", f"{r:.1f}", "Above 50", r > 50),
        ]

    if setup == "OVERSOLD_BOUNCE":
        rs = ind["rsi"]
        if None in rs[i - 3:i + 1]:
            return None
        crossed = any(rs[j - 1] < 30 <= rs[j] for j in (i, i - 1, i - 2)) and r >= 30
        low = min(rs[i - 3:i + 1])
        return [
            _chk("RSI recovered from oversold", f"{low:.1f} → {r:.1f}", "Was below 30, back above 30 (last 3 days)", crossed),
            _chk("Long-term uptrend intact", f"{inr(c, 0)} vs 200-DMA {inr(s200, 0)}", "Price > 200-DMA", c > s200),
        ]
    raise ValueError(setup)


def _tick(x: float) -> float:
    """Round to the NSE tick size of ₹0.05."""
    return round(round(x * 20) / 20, 2)


def _make_call(symbol: str, setup: str, ind: dict, i: int, checks: list[dict]) -> dict | None:
    entry = _tick(ind["close"][i])
    atr_v = ind["atr"][i]
    stop = _tick(entry - ATR_MULTIPLE * atr_v)
    if stop <= 0 or stop >= entry:
        return None
    target = _tick(entry + REWARD_MULTIPLE * (entry - stop))
    va = ind["vol_avg20"][i]
    values = {
        "close": ind["close"][i], "atr": round(atr_v, 2), "rsi": round(ind["rsi"][i], 1),
        "sma20": ind["sma20"][i] and round(ind["sma20"][i], 2), "sma50": round(ind["sma50"][i], 2),
        "sma200": round(ind["sma200"][i], 2), "macd": ind["macd"][i] and round(ind["macd"][i], 2),
        "macd_signal": ind["macd_signal"][i] and round(ind["macd_signal"][i], 2),
        "vol_ratio": round(ind["volume"][i] / va, 2) if va else None,
    }
    return {"symbol": symbol, "setup": setup, "action": "BUY", "entry": entry, "target": target,
            "stop_loss": stop, "horizon_days": HORIZON_DAYS, "issued_on": ind["date"][i],
            "signal": json.dumps({"checks": checks, "values": values})}


def scan_stock(symbol: str, bars: list[dict], ind: dict, after: str, until: str, blocked_until_idx: int) -> list[dict]:
    """New calls for one stock on days after `after` up to `until`, replaying each call's outcome
    so the next call can't start until the previous one has closed (plus cooling-off)."""
    calls = []
    dates = ind["date"]
    for i in range(len(bars)):
        if dates[i] <= after or dates[i] > until or i <= blocked_until_idx:
            continue
        for setup in SETUPS:
            checks = _checks(setup, ind, i)
            if not checks or not all(ch["passed"] for ch in checks):
                continue
            call = _make_call(symbol, setup, ind, i, checks)
            if call is None:
                continue
            status, exit_price, closed_on = evaluate(call, bars)
            call.update(status=status, exit_price=exit_price, closed_on=closed_on)
            calls.append(call)
            blocked_until_idx = len(bars) if closed_on is None else dates.index(closed_on) + COOLDOWN_BARS
            break
    return calls


def _last_complete_day(bars_by_key: dict[str, list[dict]]) -> str:
    """Today's candle is still forming until the NSE close (3:30 pm IST); don't issue calls on it."""
    now = datetime.now(IST)
    latest = max(b[-1]["date"] for k, b in bars_by_key.items() if k in STOCKS)
    if latest == now.date().isoformat() and (now.hour, now.minute) < (15, 30):
        return (now.date() - timedelta(days=1)).isoformat()
    return latest


def sync_calls(market: dict[str, list[dict]], source: str, indicators: dict[str, dict]) -> None:
    """Keep the calls table up to date with the market data.

    First run: replay the last 12 months. Later runs: close finished calls, then scan only
    the new days. Calls built on dummy data are rebuilt once live data is available, and
    dummy data is never mixed into a live track record.
    """
    until = _last_complete_day(market)
    with get_conn() as conn:
        seed_source = get_meta(conn, "seed_source")
        rebuild = seed_source is None or (source == "live" and seed_source != "live")
        if rebuild:
            conn.execute("DELETE FROM calls")
            after = (date.fromisoformat(until) - timedelta(days=BACKTEST_DAYS)).isoformat()
        elif source != seed_source:
            return  # e.g. a live track record while Yahoo is temporarily unreachable
        else:
            after = get_meta(conn, "scanned_through")
            if after >= until:
                close_finished_calls(market)
                return

    if not rebuild:
        close_finished_calls(market)

    with get_conn() as conn:
        for symbol in STOCKS:
            bars, ind = market[symbol], indicators[symbol]
            blocked = -1
            if not rebuild:
                row = conn.execute("SELECT status, closed_on FROM calls WHERE symbol = ? ORDER BY issued_on DESC LIMIT 1",
                                   (symbol,)).fetchone()
                if row and row["status"] == "OPEN":
                    continue
                if row and row["closed_on"] in ind["date"]:
                    blocked = ind["date"].index(row["closed_on"]) + COOLDOWN_BARS
            for call in scan_stock(symbol, bars, ind, after, until, blocked):
                conn.execute(
                    """INSERT INTO calls (symbol, setup, action, entry, target, stop_loss, horizon_days, issued_on,
                                          signal, status, exit_price, closed_on)
                       VALUES (:symbol, :setup, :action, :entry, :target, :stop_loss, :horizon_days, :issued_on,
                               :signal, :status, :exit_price, :closed_on)""", call)
        set_meta(conn, "seed_source", source if rebuild else seed_source)
        set_meta(conn, "scanned_through", until)
