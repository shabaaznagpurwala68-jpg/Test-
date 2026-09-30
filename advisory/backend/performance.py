"""Track record statistics for closed calls.

Assumes ₹1,00,000 put into every call (whole shares only), and deducts TradeSmart
brokerage of ₹15 per executed order — ₹30 per call (entry + exit). Taxes and
statutory charges are not included.
"""

from collections import defaultdict
from datetime import date

CAPITAL = 100_000
BROKERAGE_PER_CALL = 30  # ₹15 × 2 orders


def trade_result(call: dict) -> dict:
    direction = -1 if call["action"] == "SELL" else 1
    qty = int(CAPITAL // call["entry"])
    gross = direction * (call["exit_price"] - call["entry"]) * qty
    return {
        "return_pct": round(direction * (call["exit_price"] - call["entry"]) / call["entry"] * 100, 2),
        "qty": qty,
        "net_pnl": round(gross - BROKERAGE_PER_CALL, 2),
        "days_held": (date.fromisoformat(call["closed_on"]) - date.fromisoformat(call["issued_on"])).days,
    }


def _group_stats(trades: list[dict]) -> dict:
    wins = [t for t in trades if t["net_pnl"] > 0]
    return {
        "calls": len(trades),
        "win_rate": round(len(wins) / len(trades) * 100, 1) if trades else 0,
        "avg_return_pct": round(sum(t["return_pct"] for t in trades) / len(trades), 2) if trades else 0,
        "net_pnl": round(sum(t["net_pnl"] for t in trades), 2),
    }


def summarize(closed_calls: list[dict]) -> dict:
    trades = [{**c, **trade_result(c)} for c in closed_calls]
    trades.sort(key=lambda t: (t["closed_on"], t["id"]))

    wins = [t for t in trades if t["net_pnl"] > 0]
    losses = [t for t in trades if t["net_pnl"] <= 0]
    avg_win = sum(t["return_pct"] for t in wins) / len(wins) if wins else 0
    avg_loss = sum(t["return_pct"] for t in losses) / len(losses) if losses else 0

    # Equity curve: cumulative net P&L, one point per closing day.
    curve, running = {}, 0.0
    for t in trades:
        running += t["net_pnl"]
        curve[t["closed_on"]] = round(running, 2)
    peak, max_dd = 0.0, 0.0
    for v in curve.values():
        peak = max(peak, v)
        max_dd = max(max_dd, peak - v)

    by_sector, by_setup = defaultdict(list), defaultdict(list)
    for t in trades:
        by_sector[t["sector"]].append(t)
        by_setup[t["setup_name"]].append(t)

    return {
        "stats": {
            **_group_stats(trades),
            "target_hit": sum(t["status"] == "TARGET_HIT" for t in trades),
            "sl_hit": sum(t["status"] == "SL_HIT" for t in trades),
            "expired": sum(t["status"] == "EXPIRED" for t in trades),
            "avg_win_pct": round(avg_win, 2),
            "avg_loss_pct": round(avg_loss, 2),
            "win_loss_ratio": round(avg_win / abs(avg_loss), 2) if avg_loss else None,
            "avg_days_held": round(sum(t["days_held"] for t in trades) / len(trades), 1) if trades else 0,
            "max_drawdown": round(max_dd, 2),
            "capital_per_call": CAPITAL,
            "brokerage_per_call": BROKERAGE_PER_CALL,
        },
        "equity_curve": [{"time": d, "value": v} for d, v in curve.items()],
        "by_sector": sorted(({"sector": k, **_group_stats(v)} for k, v in by_sector.items()),
                            key=lambda g: -g["net_pnl"]),
        "by_setup": sorted(({"setup": k, **_group_stats(v)} for k, v in by_setup.items()), key=lambda g: -g["net_pnl"]),
        "closed_calls": sorted(trades, key=lambda t: (t["closed_on"], t["id"]), reverse=True),
    }
