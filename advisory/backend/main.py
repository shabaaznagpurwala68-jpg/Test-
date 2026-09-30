import json
import threading
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from db import get_conn, init_db
from explain import explain
from fundamentals import (PICK_SCORE, PICK_UPSIDE, STOP_LOSS_PCT, TARGET_CAP, evaluate_all as evaluate_fundamentals,
                          narrative)
from indicators import annual_volatility, compute
from market import get_market, quote
from markets import dashboard
from news import get_news
from performance import summarize, trade_result
from risk import QUESTIONS, risk_level, score
from technical import HORIZON_DAYS, SETUPS, sync_calls
from universe import INDICES, STOCKS

_lock = threading.Lock()
_ind_cache: dict = {"market_id": None, "indicators": None}


def _state():
    """Market data, its indicators (computed once per data refresh), and an up-to-date calls table."""
    market, source = get_market()
    with _lock:
        if _ind_cache["market_id"] != id(market):
            indicators = {k: compute(bars) for k, bars in market.items()}
            sync_calls(market, source, indicators)
            _ind_cache.update(market_id=id(market), indicators=indicators)
    return market, source, _ind_cache["indicators"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    _state()  # download data and build the 12-month track record before the first request
    yield


app = FastAPI(title="TradeSmart Advisory (test)", lifespan=lifespan)


def _enrich(row: dict, market: dict) -> dict:
    """Stock info and live numbers for a stored call.

    progress: where the price sits between stop loss (0) and target (1).
    """
    info, bars = STOCKS[row["symbol"]], market[row["symbol"]]
    q = quote(bars)
    vol = annual_volatility([b["close"] for b in bars])
    c = {
        **row,
        "signal": json.loads(row["signal"]),
        "name": info["name"],
        "sector": info["sector"],
        "setup_name": SETUPS[row["setup"]]["name"],
        "horizon": f"{row['horizon_days'] // 30} months" if row["horizon_days"] % 30 == 0 else f"{row['horizon_days']} days",
        "cmp": q["price"],
        "change_pct": round((q["price"] - q["prev_close"]) / q["prev_close"] * 100, 2),
        "volatility": vol,
        "risk_level": risk_level(vol, row["setup"]),
    }
    if row["status"] == "OPEN":
        progress = (q["price"] - row["stop_loss"]) / (row["target"] - row["stop_loss"])
        c["potential_pct"] = round((row["target"] - q["price"]) / q["price"] * 100, 2)
        c["progress"] = round(min(max(progress, 0), 1), 3)
    else:
        c.update(trade_result(row))
    return c


def _calls(market) -> list[dict]:
    with get_conn() as conn:
        rows = [dict(r) for r in conn.execute("SELECT * FROM calls ORDER BY issued_on DESC, id DESC")]
    return [_enrich(r, market) for r in rows]


def _one(call_id: int):
    market, source, indicators = _state()
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM calls WHERE id = ?", (call_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="call not found")
    return _enrich(dict(row), market), market, source, indicators


def _setup_stats(calls: list[dict]) -> dict[str, dict]:
    closed = [c for c in calls if c["status"] != "OPEN"]
    by = summarize(closed)["by_setup"]
    stats = {k: {"calls": 0, "win_rate": 0, "avg_return_pct": 0, "net_pnl": 0} for k in SETUPS}
    for g in by:
        key = next(k for k, s in SETUPS.items() if s["name"] == g["setup"])
        stats[key] = g
    for k in SETUPS:
        stats[k]["open"] = sum(c["status"] == "OPEN" and c["setup"] == k for c in calls)
    return stats


@app.get("/api/setups")
def setups():
    market, source, _ = _state()
    stats = _setup_stats(_calls(market))
    return [{"key": k, **s, "stats": stats[k], "levels": {
        "entry": "The day's closing price", "stop_loss": "Entry − 2 × ATR(14)",
        "target": "Entry + 2 × (Entry − Stop loss) → risk-reward 1:2", "horizon": f"{HORIZON_DAYS} days"}}
        for k, s in SETUPS.items()]


@app.get("/api/calls")
def list_calls(
    status: Literal["open", "closed", "all"] = "open",
    setup: Literal["TREND_BREAKOUT", "MACD_MOMENTUM", "OVERSOLD_BOUNCE"] | None = None,
):
    market, source, _ = _state()
    calls = _calls(market)
    closed = [c for c in calls if c["status"] != "OPEN"]
    items = {"open": [c for c in calls if c["status"] == "OPEN"], "closed": closed, "all": calls}[status]
    if setup:
        items = [c for c in items if c["setup"] == setup]
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


@app.get("/api/calls/{call_id}")
def get_call(call_id: int):
    c, _, source, _ = _one(call_id)
    return {**c, "price_source": source}


def _chart(key: str, market: dict, indicators: dict, start: str, end: str | None) -> dict:
    bars, ind = market[key], indicators[key]
    idx = [i for i, b in enumerate(bars) if b["date"] >= start and (not end or b["date"] <= end)]
    pick = lambda name: [{"time": ind["date"][i], "value": round(ind[name][i], 4)} for i in idx if ind[name][i] is not None]
    return {
        "bars": [bars[i] for i in idx],
        "sma20": pick("sma20"), "sma50": pick("sma50"), "sma200": pick("sma200"),
        "rsi": pick("rsi"), "macd": pick("macd"), "macd_signal": pick("macd_signal"), "macd_hist": pick("macd_hist"),
    }


@app.get("/api/calls/{call_id}/chart")
def call_chart(call_id: int):
    """Candles and indicators from 90 days before issue to today (open) or 30 days after exit (closed)."""
    c, market, _, indicators = _one(call_id)
    start = (date.fromisoformat(c["issued_on"]) - timedelta(days=90)).isoformat()
    end = c["closed_on"] and (date.fromisoformat(c["closed_on"]) + timedelta(days=30)).isoformat()
    return _chart(c["symbol"], market, indicators, start, end)


@app.get("/api/chart/{key}")
def instrument_chart(key: str, days: int = 180):
    if key not in STOCKS and key not in INDICES:
        raise HTTPException(status_code=404, detail="unknown instrument")
    market, _, indicators = _state()
    start = (date.today() - timedelta(days=min(max(days, 30), 600))).isoformat()
    return _chart(key, market, indicators, start, None)


@app.get("/api/calls/{call_id}/explain")
def call_explanation(call_id: int):
    c, market, _, _ = _one(call_id)
    return {"paragraphs": explain(c, _setup_stats(_calls(market))[c["setup"]])}


@app.get("/api/performance")
def performance():
    market, source, _ = _state()
    closed = [c for c in _calls(market) if c["status"] != "OPEN"]
    return {**summarize(closed), "price_source": source}


@app.get("/api/markets")
def markets():
    market, source, indicators = _state()
    return {**dashboard(market, indicators), "price_source": source,
            "as_of": datetime.now(timezone.utc).isoformat()}


FUNDAMENTAL_METHOD = {
    "pillars": [
        {"name": "Valuation", "points": 25, "factors": ["PE vs peer-group median (10)", "PB vs peer-group median (7)", "PEG — PE ÷ EPS growth (8)"]},
        {"name": "Quality", "points": 25, "factors": ["ROE (9)", "ROCE (8)", "Debt / equity (8)", "Financials: ROE (13) + ROA (12) instead"]},
        {"name": "Growth", "points": 25, "factors": ["3-year revenue CAGR (12)", "3-year EPS CAGR (13)"]},
        {"name": "Shareholder", "points": 25, "factors": ["Dividend yield (8)", "Promoter holding (8)", "Promoter pledge (9)"]},
    ],
    "fair_value": "Forward EPS × blended PE. Forward EPS = EPS × (1 + EPS growth, capped at 15%). "
                  "Blended PE = ½ peer-group median PE + ½ the stock's own PE.",
    "rules": [f"PICK: score ≥ {PICK_SCORE} and fair value ≥ {PICK_UPSIDE}% above the price",
              f"WATCH: score ≥ {PICK_SCORE}, but less than {PICK_UPSIDE}% upside",
              f"NEUTRAL: score 50 – {PICK_SCORE - 1}", "WEAK: score below 50"],
    "levels": {"target": f"Fair value, capped at +{TARGET_CAP}% for a 12-month view",
               "stop_loss": f"{STOP_LOSS_PCT}% below the current price, reviewed quarterly", "horizon": "12 months"},
    "data_note": "Fundamentals (EPS, ROE, growth, holdings…) are SAMPLE values for demonstration. "
                 "PE, PB, dividend yield and market cap use the live price.",
}


@app.get("/api/fundamentals")
def fundamentals():
    market, source, _ = _state()
    result = evaluate_fundamentals(market)
    for it in result["items"]:
        it.pop("factors")
    return {**result, "method": FUNDAMENTAL_METHOD, "price_source": source,
            "as_of": datetime.now(timezone.utc).isoformat()}


@app.get("/api/fundamentals/{symbol}")
def fundamental_detail(symbol: str):
    market, source, _ = _state()
    result = evaluate_fundamentals(market)
    item = next((i for i in result["items"] if i["symbol"] == symbol), None)
    if item is None:
        raise HTTPException(status_code=404, detail="unknown stock")
    group = next(g for g in result["peer_groups"] if g["group"] == item["peer_group"])
    peers = [{k: i[k] for k in ("symbol", "pe", "pb", "roe", "score", "verdict")}
             for i in result["items"] if i["peer_group"] == item["peer_group"]]
    return {**item, "narrative": narrative(item), "peer": group, "peers": peers, "method": FUNDAMENTAL_METHOD,
            "price_source": source}


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
