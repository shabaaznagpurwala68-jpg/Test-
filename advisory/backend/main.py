from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Literal

from fastapi import FastAPI, HTTPException

from db import get_conn, init_db
from market import get_prices
from news import get_news
from seed import seed_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_if_empty()
    yield


app = FastAPI(title="TradeSmart Advisory (test)", lifespan=lifespan)


def _enrich(row: dict, quote: dict) -> dict:
    """Add live numbers to a stored recommendation.

    progress: where the price sits between stop loss (0) and target (1).
    The same formula works for SELL calls, where the stop loss is above the entry.
    """
    cmp_ = quote["price"]
    progress = (cmp_ - row["stop_loss"]) / (row["target"] - row["stop_loss"])
    if progress >= 1:
        status = "TARGET_HIT"
    elif progress <= 0:
        status = "SL_HIT"
    else:
        status = "OPEN"
    direction = -1 if row["action"] == "SELL" else 1
    return {
        **row,
        "cmp": cmp_,
        "change_pct": round((cmp_ - quote["prev_close"]) / quote["prev_close"] * 100, 2),
        "potential_pct": round(direction * (row["target"] - cmp_) / cmp_ * 100, 2),
        "progress": round(min(max(progress, 0), 1), 3),
        "status": status,
    }


def _load() -> tuple[list[dict], str]:
    # Always price every stock in one call, so filters and detail views share one cache entry.
    with get_conn() as conn:
        rows = [dict(r) for r in conn.execute("SELECT * FROM recommendations ORDER BY issued_on DESC, id")]
    prices, source = get_prices({r["symbol"]: r["entry"] for r in rows})
    return [_enrich(r, prices[r["symbol"]]) for r in rows], source


@app.get("/api/recommendations")
def list_recommendations(action: Literal["BUY", "SELL", "HOLD"] | None = None):
    items, source = _load()
    if action:
        items = [i for i in items if i["action"] == action]
    open_items = [i for i in items if i["status"] == "OPEN"]
    return {
        "items": items,
        "summary": {
            "total": len(items),
            "open": len(open_items),
            "target_hit": sum(i["status"] == "TARGET_HIT" for i in items),
            "sl_hit": sum(i["status"] == "SL_HIT" for i in items),
            "avg_potential_open": round(sum(i["potential_pct"] for i in open_items) / len(open_items), 2) if open_items else 0,
        },
        "price_source": source,
        "as_of": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/recommendations/{rec_id}")
def get_recommendation(rec_id: int):
    items, source = _load()
    items = [i for i in items if i["id"] == rec_id]
    if not items:
        raise HTTPException(status_code=404, detail="recommendation not found")
    return {**items[0], "price_source": source}


@app.get("/api/news")
def news():
    items, source = get_news()
    return {"items": items, "source": source}
