"""Decides when an open call is closed, candle by candle.

Rules (checked on each trading day after the issue day):
- Gap: if the day OPENS beyond the stop loss or target, the call exits at the open price.
- Both levels inside one candle: we can't know which came first, so we assume the
  stop loss (the conservative choice — it never flatters the track record).
- Horizon over and neither level hit: EXPIRED at that day's close.
SELL calls are the mirror image: target below entry, stop loss above.
"""

from datetime import date, timedelta

from db import get_conn


def evaluate(call: dict, bars: list[dict]) -> tuple[str, float | None, str | None]:
    sell = call["action"] == "SELL"
    tgt, sl = call["target"], call["stop_loss"]
    expiry = (date.fromisoformat(call["issued_on"]) + timedelta(days=call["horizon_days"])).isoformat()

    for b in bars:
        if b["date"] <= call["issued_on"]:
            continue
        if sell:
            if b["open"] >= sl:
                return "SL_HIT", b["open"], b["date"]
            if b["open"] <= tgt:
                return "TARGET_HIT", b["open"], b["date"]
            if b["high"] >= sl:
                return "SL_HIT", sl, b["date"]
            if b["low"] <= tgt:
                return "TARGET_HIT", tgt, b["date"]
        else:
            if b["open"] <= sl:
                return "SL_HIT", b["open"], b["date"]
            if b["open"] >= tgt:
                return "TARGET_HIT", b["open"], b["date"]
            if b["low"] <= sl:
                return "SL_HIT", sl, b["date"]
            if b["high"] >= tgt:
                return "TARGET_HIT", tgt, b["date"]
        if b["date"] >= expiry:
            return "EXPIRED", b["close"], b["date"]
    return "OPEN", None, None


def close_finished_calls(market: dict[str, list[dict]]) -> int:
    """Checks every open call against its candles and saves any that closed. Returns how many."""
    closed = 0
    with get_conn() as conn:
        for row in conn.execute("SELECT * FROM calls WHERE status = 'OPEN'").fetchall():
            call = dict(row)
            status, exit_price, closed_on = evaluate(call, market[call["symbol"]])
            if status != "OPEN":
                conn.execute("UPDATE calls SET status = ?, exit_price = ?, closed_on = ? WHERE id = ?",
                             (status, exit_price, closed_on, call["id"]))
                closed += 1
    return closed
