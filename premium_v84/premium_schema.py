
"""
NeMeSiS SHARK PRO V84
Premium Engagement Experience schema
"""

import sqlite3
from datetime import datetime


def init_premium_v84_tables(db_path="nemesis.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_xp_profiles (
        user_id TEXT PRIMARY KEY,
        xp INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        streak_days INTEGER DEFAULT 0,
        last_activity_at TEXT,
        badge_count INTEGER DEFAULT 0,
        updated_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_badges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        badge_key TEXT,
        badge_title TEXT,
        badge_description TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ux_missions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        mission_key TEXT,
        title TEXT,
        description TEXT,
        xp_reward INTEGER DEFAULT 10,
        status TEXT DEFAULT 'PENDING',
        created_at TEXT,
        completed_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS premium_experience_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT,
        user_id TEXT,
        title TEXT,
        metadata TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_premium_v84_tables()
    print("V84 premium tables initialized")
