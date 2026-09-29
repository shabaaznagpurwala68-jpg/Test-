import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "advisory.db"
SCHEMA_VERSION = 2  # bump when the table changes; old test data is then rebuilt


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        if conn.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION:
            conn.execute("DROP TABLE IF EXISTS recommendations")
            conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL CHECK (length(symbol) > 0),
                action TEXT NOT NULL CHECK (action IN ('BUY', 'SELL', 'HOLD')),
                entry REAL NOT NULL CHECK (entry > 0),
                target REAL NOT NULL CHECK (target > 0),
                stop_loss REAL NOT NULL CHECK (stop_loss > 0),
                horizon_days INTEGER NOT NULL CHECK (horizon_days > 0),
                rationale TEXT NOT NULL,
                issued_on TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'OPEN'
                    CHECK (status IN ('OPEN', 'TARGET_HIT', 'SL_HIT', 'EXPIRED')),
                exit_price REAL,
                closed_on TEXT
            )
            """
        )
