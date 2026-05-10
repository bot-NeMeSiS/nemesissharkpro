
"""
NeMeSiS SHARK PRO V74
UX Automation + Retention Engine schema
"""

import sqlite3
from datetime import datetime


def init_retention_tables(db_path="nemesis.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_engagement_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        event_type TEXT,
        event_value TEXT,
        page TEXT,
        source TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_retention_profiles (
        user_id TEXT PRIMARY KEY,
        engagement_score REAL DEFAULT 0,
        retention_risk TEXT DEFAULT 'UNKNOWN',
        current_streak INTEGER DEFAULT 0,
        last_seen_at TEXT,
        last_pick_seen_at TEXT,
        onboarding_completed INTEGER DEFAULT 0,
        preferred_sport TEXT,
        preferred_plan TEXT,
        updated_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS retention_actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        action_type TEXT,
        status TEXT DEFAULT 'PENDING',
        priority TEXT DEFAULT 'NORMAL',
        title TEXT,
        message TEXT,
        channel TEXT DEFAULT 'IN_APP',
        created_at TEXT,
        delivered_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS onboarding_steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        step_key TEXT,
        status TEXT DEFAULT 'PENDING',
        completed_at TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_retention_tables()
    print("V74 retention tables initialized")
