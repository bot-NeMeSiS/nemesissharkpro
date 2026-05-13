
import sqlite3
from datetime import datetime

def init_community_tables(db_path="nemesis.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS community_activity (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        activity_type TEXT,
        user_id TEXT,
        title TEXT,
        message TEXT,
        visibility TEXT DEFAULT 'PUBLIC',
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS popular_picks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pick_id TEXT,
        sport TEXT,
        match_name TEXT,
        market TEXT,
        views INTEGER DEFAULT 0,
        favorites INTEGER DEFAULT 0,
        heat_score REAL DEFAULT 0,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_leaderboard_stats (
        user_id TEXT PRIMARY KEY,
        display_name TEXT,
        roi REAL DEFAULT 0,
        win_rate REAL DEFAULT 0,
        picks_count INTEGER DEFAULT 0,
        streak INTEGER DEFAULT 0,
        rank_score REAL DEFAULT 0,
        updated_at TEXT
    )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_community_tables()
    print("V76 community tables initialized")
