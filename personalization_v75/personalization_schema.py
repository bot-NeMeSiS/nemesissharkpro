
import sqlite3
from datetime import datetime

def init_personalization_tables(db_path="nemesis.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_personalization_profiles (
        user_id TEXT PRIMARY KEY,
        favorite_sport TEXT,
        favorite_league TEXT,
        favorite_market TEXT,
        risk_preference TEXT DEFAULT 'MEDIO',
        recommended_plan TEXT DEFAULT 'PRO',
        personalization_score REAL DEFAULT 0,
        updated_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        recommendation_type TEXT,
        title TEXT,
        message TEXT,
        priority TEXT DEFAULT 'NORMAL',
        status TEXT DEFAULT 'ACTIVE',
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_smart_alert_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        sport TEXT,
        league TEXT,
        market TEXT,
        min_shark_score REAL DEFAULT 75,
        channel TEXT DEFAULT 'IN_APP',
        enabled INTEGER DEFAULT 1,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_personalization_tables()
    print("V75 personalization tables initialized")
