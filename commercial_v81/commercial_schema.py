
"""
NeMeSiS SHARK PRO V81
App Top Comercial schema
"""

import sqlite3
from datetime import datetime


def init_commercial_tables(db_path="nemesis.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS public_profiles (
        user_id TEXT PRIMARY KEY,
        display_name TEXT,
        avatar_emoji TEXT DEFAULT '🦈',
        bio TEXT,
        public_roi REAL DEFAULT 0,
        public_win_rate REAL DEFAULT 0,
        public_picks INTEGER DEFAULT 0,
        public_streak INTEGER DEFAULT 0,
        reputation_score REAL DEFAULT 0,
        is_public INTEGER DEFAULT 1,
        created_at TEXT,
        updated_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS shared_picks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        share_code TEXT UNIQUE,
        pick_id TEXT,
        user_id TEXT,
        title TEXT,
        match_name TEXT,
        market TEXT,
        odds REAL,
        shark_score REAL,
        confidence TEXT,
        share_text TEXT,
        views INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS commercial_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT,
        source TEXT,
        title TEXT,
        metadata TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS onboarding_commercial_steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        step_key TEXT,
        title TEXT,
        status TEXT DEFAULT 'PENDING',
        completed_at TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_commercial_tables()
    print("V81 commercial tables initialized")
