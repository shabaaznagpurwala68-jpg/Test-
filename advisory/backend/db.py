import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "advisory.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL CHECK (length(symbol) > 0),
                name TEXT NOT NULL,
                sector TEXT NOT NULL,
                action TEXT NOT NULL CHECK (action IN ('BUY', 'SELL', 'HOLD')),
                entry REAL NOT NULL CHECK (entry > 0),
                target REAL NOT NULL CHECK (target > 0),
                stop_loss REAL NOT NULL CHECK (stop_loss > 0),
                horizon TEXT NOT NULL,
                rationale TEXT NOT NULL,
                issued_on TEXT NOT NULL
            )
            """
        )
