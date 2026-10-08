import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "advisory.db"
SCHEMA_VERSION = 3  # bump when tables change; old test data is then rebuilt


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        if conn.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION:
            for table in ("recommendations", "calls", "meta"):
                conn.execute(f"DROP TABLE IF EXISTS {table}")
            conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL CHECK (length(symbol) > 0),
                setup TEXT NOT NULL CHECK (setup IN ('TREND_BREAKOUT', 'MACD_MOMENTUM', 'OVERSOLD_BOUNCE')),
                action TEXT NOT NULL CHECK (action IN ('BUY', 'SELL')),
                entry REAL NOT NULL CHECK (entry > 0),
                target REAL NOT NULL CHECK (target > 0),
                stop_loss REAL NOT NULL CHECK (stop_loss > 0),
                horizon_days INTEGER NOT NULL CHECK (horizon_days > 0),
                issued_on TEXT NOT NULL,
                signal TEXT NOT NULL,          -- JSON: the checklist and indicator values at issue time
                status TEXT NOT NULL DEFAULT 'OPEN'
                    CHECK (status IN ('OPEN', 'TARGET_HIT', 'SL_HIT', 'EXPIRED')),
                exit_price REAL,
                closed_on TEXT
            )
            """
        )
        conn.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        # Newsletter sign-ups. Added without a schema-version bump so existing calls are kept.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                frequency TEXT NOT NULL CHECK (frequency IN ('WEEKLY', 'EVENTS')),
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )


def get_meta(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row[0] if row else None


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute("INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                 (key, value))
