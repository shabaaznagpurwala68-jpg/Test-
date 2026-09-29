import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "watchlist.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL CHECK (length(symbol) > 0),
                quantity REAL NOT NULL CHECK (quantity > 0),
                buy_price REAL NOT NULL CHECK (buy_price > 0)
            )
            """
        )
