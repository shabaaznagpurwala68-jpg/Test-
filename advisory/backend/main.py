from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone, date
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from db import get_conn, init_db
from evaluator import close_finished_calls
from explain import explain
from market import annual_volatility, get_market, quote
from news import get_news
from performance import summarize, trade_result
from risk import QUESTIONS, risk_level, score
from seed import seed_if_empty
from universe import UNIVERSE

HORIZONS = {30: "1 month", 60: "2 months", 90: "3 months", 180: "6 months"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_if_empty()
    yield


app = FastAPI(title="TradeSmart Advisory (test)", lifespan=lifespan)


def _enrich(row: dict, bars: list[dict]) -> dict:
    """Add stock info and live numbers to a stored call.

    progress: where the price sits between stop loss (0) and target (1).
    The same formula works for SELL calls, where the stop loss is above the entry.
    """
    info = UNIVERSE[row["symbol"]]
    q = quote(bars)
    vol = annual_volatility(bars)
    c = {
        **row,
        "name": info["name"],
        "sector": info["sector"],
        "horizon": HORIZONS.get(row["horizon_days"], f"{row['horizon_days']} days"),
        "cmp": q["price"],
        "change_pct": round((q["price"] - q["prev_close"]) / q["prev_close"] * 100, 2),
        "volatility": vol,
        "risk_level": risk_level(vol, row["action"]),
    }
    if row["status"] == "OPEN":
        direction = -1 if row["action"] == "SELL" else 1
        progress = (q["price"] - row["stop_loss"]) / (row["target"] - row["stop_loss"])
        c["potential_pct"] = round(direction * (row["target"] - q["price"]) / q["price"] * 100, 2)
        c["progress"] = round(min(max(progress, 0), 1), 3)
    else:
        c.update(trade_result(row))
    return c


def _load() -> tuple[list[dict], str, dict]:
    """Every call, checked against the latest candles. Newly finished calls are closed and saved."""
    market, source = get_market()
    close_finished_calls(market)
    with get_conn() as conn:
        rows = [dict(r) for r in conn.execute("SELECT * FROM recommendations ORDER BY issued_on DESC, id DESC")]
    return [_enrich(r, market[r["symbol"]]) for r in rows], source, market


def _one(rec_id: int) -> tuple[dict, str, dict]:
    calls, source, market = _load()
    for c in calls:
        if c["id"] == rec_id:
            return c, source, market
    raise HTTPException(status_code=404, detail="recommendation not found")


@app.get("/api/recommendations")
def list_recommendations(
    status: Literal["open", "closed", "all"] = "open",
    action: Literal["BUY", "SELL", "HOLD"] | None = None,
):
    calls, source, _ = _load()
    closed = [c for c in calls if c["status"] != "OPEN"]
    items = {"open": [c for c in calls if c["status"] == "OPEN"], "closed": closed, "all": calls}[status]
    if action:
        items = [c for c in items if c["action"] == action]
    open_items = [c for c in items if c["status"] == "OPEN"]
    wins = sum(trade_result(c)["net_pnl"] > 0 for c in closed)
    return {
        "items": items,
        "summary": {
            "open": len(open_items),
            "avg_potential_open": round(sum(c["potential_pct"] for c in open_items) / len(open_items), 2) if open_items else 0,
            "closed": len(closed),
            "win_rate": round(wins / len(closed) * 100, 1) if closed else 0,
        },
        "price_source": source,
        "as_of": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/recommendations/{rec_id}")
def get_recommendation(rec_id: int):
    c, source, _ = _one(rec_id)
    return {**c, "price_source": source}


@app.get("/api/recommendations/{rec_id}/candles")
def get_candles(rec_id: int):
    """Daily candles around the call: from 60 days before issue to today (open) or 30 days after exit (closed)."""
    c, source, market = _one(rec_id)
    start = (date.fromisoformat(c["issued_on"]) - timedelta(days=60)).isoformat()
    end = c["closed_on"] and (date.fromisoformat(c["closed_on"]) + timedelta(days=30)).isoformat()
    bars = [b for b in market[c["symbol"]] if b["date"] >= start and (not end or b["date"] <= end)]
    return {"bars": bars, "source": source}


@app.get("/api/recommendations/{rec_id}/explain")
def get_explanation(rec_id: int):
    c, _, _ = _one(rec_id)
    return {"paragraphs": explain(c)}


@app.get("/api/performance")
def performance():
    calls, source, _ = _load()
    return {**summarize([c for c in calls if c["status"] != "OPEN"]), "price_source": source}


@app.get("/api/news")
def news(symbol: str | None = None):
    items, source = get_news(symbol)
    return {"items": items, "source": source}


class RiskAnswers(BaseModel):
    answers: list[int] = Field(min_length=len(QUESTIONS), max_length=len(QUESTIONS))


@app.get("/api/risk/questions")
def risk_questions():
    return [{"id": i, "question": q, "options": opts} for i, (q, opts) in enumerate(QUESTIONS)]


@app.post("/api/risk/score")
def risk_score(body: RiskAnswers):
    for i, a in enumerate(body.answers):
        if not 0 <= a < len(QUESTIONS[i][1]):
            raise HTTPException(status_code=422, detail=f"answer {i + 1} is out of range")
    return score(body.answers)
