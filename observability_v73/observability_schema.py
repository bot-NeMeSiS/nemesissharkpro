
"""
NeMeSiS SHARK PRO V73
Observability + Error Tracking Pro schema
"""

import sqlite3
from datetime import datetime


def init_observability_tables(db_path="nemesis.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS app_error_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        error_type TEXT,
        endpoint TEXT,
        method TEXT,
        status_code INTEGER,
        message TEXT,
        traceback TEXT,
        user_id TEXT,
        ip TEXT,
        user_agent TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS app_health_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT,
        status TEXT,
        message TEXT,
        response_time_ms REAL,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS app_performance_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        total_requests INTEGER DEFAULT 0,
        total_errors INTEGER DEFAULT 0,
        error_rate REAL DEFAULT 0,
        avg_response_time_ms REAL DEFAULT 0,
        telegram_pending INTEGER DEFAULT 0,
        push_pending INTEGER DEFAULT 0,
        db_status TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_observability_tables()
    print("V73 observability tables initialized")
