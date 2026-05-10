
"""
NeMeSiS SHARK PRO V72
Launch Readiness + Beta System schema
"""

import sqlite3
from datetime import datetime


def init_launch_tables(db_path="nemesis.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS beta_invites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        invite_code TEXT UNIQUE,
        plan_granted TEXT DEFAULT 'PRO',
        status TEXT DEFAULT 'PENDING',
        used_by_user_id TEXT,
        created_at TEXT,
        used_at TEXT,
        notes TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS launch_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT,
        status TEXT,
        message TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS launch_settings (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at TEXT
    )
    """)

    defaults = {
        "BETA_MODE": "true",
        "MAINTENANCE_MODE": "false",
        "PUBLIC_REGISTRATION": "false",
        "LAUNCH_STAGE": "PRIVATE_BETA",
        "MAX_BETA_USERS": "100",
    }

    for key, value in defaults.items():
        cur.execute("""
        INSERT OR IGNORE INTO launch_settings (key, value, updated_at)
        VALUES (?, ?, ?)
        """, (key, value, datetime.utcnow().isoformat()))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_launch_tables()
    print("V72 launch tables initialized")
