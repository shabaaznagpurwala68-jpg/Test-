"""Plain-language explanation of a call, built from its own numbers.

Rule-based, not AI: the same call always gets the same explanation, and it can
only restate what the call already says — it never adds a view of its own.
"""

import math
from datetime import date


def _inr(x: float) -> str:
    s = f"{x:,.2f}"
    whole, frac = s.split(".")
    digits = whole.replace(",", "")
    if len(digits) > 3:  # Indian grouping: 1,00,000
        head, tail = digits[:-3], digits[-3:]
        head = ",".join([head[max(i - 2, 0):i] for i in range(len(head), 0, -2)][::-1])
        whole = f"{head},{tail}"
    return f"₹{whole}.{frac}"


def explain(c: dict) -> list[str]:
    name, horizon = c["name"], c["horizon"]
    entry, tgt, sl = c["entry"], c["target"], c["stop_loss"]
    reward_pct = abs(tgt - entry) / entry * 100
    risk_pct = abs(entry - sl) / entry * 100
    rr = abs(tgt - entry) / abs(entry - sl)
    out = []

    if c["action"] == "BUY":
        out.append(f"This is a BUY call on {name}. It suggests buying near {_inr(entry)}, expecting the price "
                   f"to rise to {_inr(tgt)} (about {reward_pct:.1f}% higher) within {horizon}.")
        out.append(f"The stop loss at {_inr(sl)} is the exit point if the view turns out wrong. Exiting there "
                   f"limits the loss to about {risk_pct:.1f}% of the amount invested.")
    elif c["action"] == "SELL":
        out.append(f"This is a SELL call on {name}. The view is that the price may fall from {_inr(entry)} to "
                   f"{_inr(tgt)} (about {reward_pct:.1f}% lower) within {horizon}. If you hold the stock, it's "
                   f"a signal to consider exiting; traders may take a short position through futures.")
        out.append(f"The stop loss at {_inr(sl)} is above the entry: if the price rises there instead, the view "
                   f"is wrong and a short position should be closed, limiting the loss to about {risk_pct:.1f}%.")
    else:
        out.append(f"This is a HOLD call on {name}. If you already own it, the view is to stay invested, with a "
                   f"target of {_inr(tgt)} (about {reward_pct:.1f}% above {_inr(entry)}) within {horizon}. "
                   f"It is not a signal to buy more.")
        out.append(f"If the price falls to {_inr(sl)} (about {risk_pct:.1f}% below the entry), the stop loss "
                   f"says exit to protect your capital.")

    quality = "favourable" if rr >= 2 else "reasonable" if rr >= 1.5 else "thin"
    out.append(f"For every ₹1 at risk, the potential reward is ₹{rr:.2f} (risk-reward 1:{rr:.1f}), "
               f"which is {quality}.")

    daily = c["volatility"] / math.sqrt(252)
    out.append(f"{name} has moved about {c['volatility']:.0f}% a year (annualised volatility), roughly "
               f"{daily:.1f}% on a typical day. That puts this call in the {c['risk_level']} risk bucket.")

    qty = int(100_000 // entry)
    if qty:
        out.append(f"Example: with ₹1,00,000 you could take {qty} shares. If the stop loss is hit, the loss "
                   f"would be about {_inr(qty * abs(entry - sl))}; if the target is hit, the gain would be about "
                   f"{_inr(qty * abs(tgt - entry))} (before brokerage and taxes).")

    if c["status"] == "OPEN":
        out.append(f"Right now the price is {_inr(c['cmp'])}, {c['progress'] * 100:.0f}% of the way from the "
                   f"stop loss to the target.")
    else:
        verb = {"TARGET_HIT": "hit its target", "SL_HIT": "hit its stop loss", "EXPIRED": "expired"}[c["status"]]
        out.append(f"This call is closed: it {verb} on {date.fromisoformat(c['closed_on']):%d %b %Y}, exiting at {_inr(c['exit_price'])} "
                   f"({c['return_pct']:+.2f}%).")
    return out
