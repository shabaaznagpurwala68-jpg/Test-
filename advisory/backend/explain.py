"""Plain-language explanation of a technical call, built from its own numbers.

Rule-based, not AI: the same call always gets the same explanation, and it only
restates what the call's checklist and levels already say.
"""

import math
from datetime import date

from fmt import inr
from technical import ATR_MULTIPLE, REWARD_MULTIPLE, SETUPS


def _why(setup: str, v: dict) -> str:
    if setup == "TREND_BREAKOUT":
        return (f"Why now: the price closed above its highest level of the previous 20 days while the 50-day "
                f"average ({inr(v['sma50'], 0)}) was above the 200-day average ({inr(v['sma200'], 0)}) — the uptrend "
                f"is intact. Volume was {v['vol_ratio']:.1f}× normal, a sign of real buying interest, and RSI of "
                f"{v['rsi']:.0f} shows momentum without being overbought (above 70–75).")
    if setup == "MACD_MOMENTUM":
        return (f"Why now: MACD ({v['macd']:.2f}) crossed above its signal line ({v['macd_signal']:.2f}), which means "
                f"the short-term average started rising faster than the longer one — momentum turning up. The price "
                f"is above its 200-day average ({inr(v['sma200'], 0)}), so this is in the direction of the long-term "
                f"trend, and RSI of {v['rsi']:.0f} confirms buyers have the edge.")
    return (f"Why now: RSI fell below 30 (oversold — the stock dropped fast) and has recovered to {v['rsi']:.0f}, "
            f"suggesting selling pressure is easing. The price is still above its 200-day average "
            f"({inr(v['sma200'], 0)}), so the long-term uptrend hasn't broken. Buying a dip is riskier than buying "
            f"strength, which is why this setup is rated one risk level higher.")


def explain(c: dict, setup_stats: dict | None) -> list[str]:
    v = c["signal"]["values"]
    entry, tgt, sl = c["entry"], c["target"], c["stop_loss"]
    setup_name = SETUPS[c["setup"]]["name"]
    reward_pct = (tgt - entry) / entry * 100
    risk_pct = (entry - sl) / entry * 100
    out = [
        f"This is a BUY call on {c['name']} from our {setup_name} setup. It suggests buying near {inr(entry)}, "
        f"with a target of {inr(tgt)} (about {reward_pct:.1f}% higher) within {c['horizon']}.",
        _why(c["setup"], v),
        f"How the stop loss is set: ATR — the stock's average daily range over 14 days — was {inr(v['atr'])}. "
        f"The stop loss sits {ATR_MULTIPLE} × ATR below the entry at {inr(sl)} (about {risk_pct:.1f}%), so normal "
        f"day-to-day noise shouldn't trigger it, but a real reversal will.",
        f"How the target is set: {REWARD_MULTIPLE} × the risk above the entry, a fixed risk-reward of "
        f"1:{REWARD_MULTIPLE}. At 1:{REWARD_MULTIPLE}, the method breaks even if about "
        f"{100 / (1 + REWARD_MULTIPLE):.0f}% of calls hit their target (a bit more after charges).",
    ]
    if setup_stats and setup_stats["calls"]:
        out.append(f"Track record of this setup over the last 12 months: {setup_stats['calls']} closed calls, "
                   f"{setup_stats['win_rate']:.0f}% profitable, average {setup_stats['avg_return_pct']:+.2f}% per call.")
    daily = c["volatility"] / math.sqrt(252)
    out.append(f"{c['name']} has moved about {c['volatility']:.0f}% a year, roughly {daily:.1f}% on a typical day. "
               f"That puts this call in the {c['risk_level']} risk bucket.")
    qty = int(100_000 // entry)
    if qty:
        out.append(f"Example: with ₹1,00,000 you could buy {qty} shares. If the stop loss is hit, the loss would be "
                   f"about {inr(qty * (entry - sl), 0)}; if the target is hit, the gain would be about "
                   f"{inr(qty * (tgt - entry), 0)} (before brokerage and taxes).")
    if c["status"] == "OPEN":
        out.append(f"Right now the price is {inr(c['cmp'])}, {c['progress'] * 100:.0f}% of the way from the stop "
                   f"loss to the target.")
    else:
        verb = {"TARGET_HIT": "hit its target", "SL_HIT": "hit its stop loss", "EXPIRED": "reached its time limit"}[c["status"]]
        out.append(f"This call is closed: it {verb} on {date.fromisoformat(c['closed_on']):%d %b %Y}, exiting at "
                   f"{inr(c['exit_price'])} ({c['return_pct']:+.2f}%).")
    return out
