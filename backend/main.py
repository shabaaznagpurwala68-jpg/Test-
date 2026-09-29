from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from db import get_conn, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Stock Watchlist", lifespan=lifespan)


class StockIn(BaseModel):
    symbol: str
    quantity: float = Field(gt=0)
    buy_price: float = Field(gt=0)

    @field_validator("symbol")
    @classmethod
    def clean_symbol(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("symbol must not be empty")
        return v


class Stock(StockIn):
    id: int


@app.get("/api/stocks", response_model=list[Stock])
def list_stocks():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM stocks ORDER BY id").fetchall()
    return [dict(r) for r in rows]


@app.post("/api/stocks", response_model=Stock, status_code=201)
def add_stock(stock: StockIn):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO stocks (symbol, quantity, buy_price) VALUES (?, ?, ?)",
            (stock.symbol, stock.quantity, stock.buy_price),
        )
    return {"id": cur.lastrowid, **stock.model_dump()}


@app.delete("/api/stocks/{stock_id}", status_code=204)
def delete_stock(stock_id: int):
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM stocks WHERE id = ?", (stock_id,))
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="stock not found")


@app.get("/api/stocks/total")
def total_invested():
    with get_conn() as conn:
        total = conn.execute(
            "SELECT COALESCE(SUM(quantity * buy_price), 0) FROM stocks"
        ).fetchone()[0]
    return {"total_invested": round(total, 2)}
