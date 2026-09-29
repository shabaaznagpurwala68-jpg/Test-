"""Sample calls replayed over the last 12 months. None of this is research or advice.

Each call is issued at the real closing price on its issue date (or the dummy
history's price when Yahoo is unreachable), then the evaluator walks the actual
daily candles forward to decide how it ended. The calls are samples; the outcomes
are what the market (or the dummy history) actually did.
"""

import random
from datetime import date, timedelta

from db import get_conn
from evaluator import evaluate
from market import get_market
from universe import UNIVERSE

RATIONALES = {
    "BUY": [
        "Sample: breakout above a multi-week range with rising volumes.",
        "Sample: earnings momentum and improving margins.",
        "Sample: sector tailwinds with valuation below its 5-year average.",
        "Sample: strong order book gives earnings visibility.",
        "Sample: price holding above its 200-day average after a pullback.",
    ],
    "SELL": [
        "Sample: breakdown below support with weak volumes on up days.",
        "Sample: margin pressure and slowing volume growth.",
        "Sample: valuation stretched versus peers amid earnings downgrades.",
    ],
    "HOLD": [
        "Sample: fundamentals intact, but limited near-term triggers.",
        "Sample: quality franchise; wait for a better entry to add.",
    ],
}
LEVELS = {  # (target % range, stop-loss % range, horizons in days)
    "BUY": ((8, 16), (4, 7), [60, 90, 180]),
    "SELL": ((6, 11), (4, 6), [30, 60]),
    "HOLD": ((5, 8), (4, 6), [90, 180]),
}


def tick(x: float) -> float:
    """Round to the NSE tick size of ₹0.05."""
    return round(round(x * 20) / 20, 2)


def _bar_on_or_before(bars: list[dict], day: str) -> dict | None:
    eligible = [b for b in bars if b["date"] <= day]
    return eligible[-1] if eligible else None


def seed_if_empty() -> None:
    with get_conn() as conn:
        if conn.execute("SELECT COUNT(*) FROM recommendations").fetchone()[0]:
            return

        market, _ = get_market()
        rng = random.Random(2026)
        today = date.today()
        # ~40 older calls spread over a year, ~22 recent ones (most of these are still open).
        offsets = [round(360 - i * 300 / 39) for i in range(40)] + [round(58 - i * 56 / 21) for i in range(22)]
        busy_until: dict[str, str] = {}  # one live call per stock at a time

        for offset in offsets:
            day = (today - timedelta(days=offset)).isoformat()
            free = [s for s in UNIVERSE if busy_until.get(s, "") < day]
            if not free:
                continue
            symbol = rng.choice(free)
            bar = _bar_on_or_before(market[symbol], day)
            if bar is None:
                continue

            action = rng.choices(["BUY", "SELL", "HOLD"], weights=[75, 15, 10])[0]
            (t_lo, t_hi), (s_lo, s_hi), horizons = LEVELS[action]
            t_pct, s_pct = rng.uniform(t_lo, t_hi) / 100, rng.uniform(s_lo, s_hi) / 100
            entry = tick(bar["close"])
            if action == "SELL":
                target, stop = tick(entry * (1 - t_pct)), tick(entry * (1 + s_pct))
            else:
                target, stop = tick(entry * (1 + t_pct)), tick(entry * (1 - s_pct))

            call = {"symbol": symbol, "action": action, "entry": entry, "target": target, "stop_loss": stop,
                    "horizon_days": rng.choice(horizons), "rationale": rng.choice(RATIONALES[action]),
                    "issued_on": bar["date"]}
            status, exit_price, closed_on = evaluate(call, market[symbol])
            busy_until[symbol] = closed_on or "9999-12-31"
            conn.execute(
                """INSERT INTO recommendations
                   (symbol, action, entry, target, stop_loss, horizon_days, rationale, issued_on,
                    status, exit_price, closed_on)
                   VALUES (:symbol, :action, :entry, :target, :stop_loss, :horizon_days, :rationale,
                           :issued_on, :status, :exit_price, :closed_on)""",
                {**call, "status": status, "exit_price": exit_price, "closed_on": closed_on},
            )
