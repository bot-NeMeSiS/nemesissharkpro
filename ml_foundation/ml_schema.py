
"""
NeMeSiS SHARK PRO V69
Machine Learning Foundation - SQLite schema helpers
"""

import sqlite3
from datetime import datetime


def init_ml_tables(db_path="nemesis.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS shark_ml_dataset (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pick_id TEXT,
        sport TEXT,
        league TEXT,
        match_name TEXT,
        market TEXT,
        selection TEXT,
        odds REAL,
        shark_score REAL,
        confidence_level TEXT,
        volatility_level TEXT,
        live_intensity REAL,
        live_pressure TEXT,
        heat_level TEXT,
        result TEXT,
        profit_loss REAL DEFAULT 0,
        roi REAL DEFAULT 0,
        created_at TEXT,
        settled_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS shark_learning_patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pattern_type TEXT,
        pattern_key TEXT,
        total_picks INTEGER DEFAULT 0,
        wins INTEGER DEFAULT 0,
        losses INTEGER DEFAULT 0,
        voids INTEGER DEFAULT 0,
        win_rate REAL DEFAULT 0,
        roi REAL DEFAULT 0,
        confidence_adjustment REAL DEFAULT 0,
        risk_adjustment REAL DEFAULT 0,
        updated_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS shark_ai_training_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dataset_size INTEGER DEFAULT 0,
        global_accuracy REAL DEFAULT 0,
        global_roi REAL DEFAULT 0,
        best_sport TEXT,
        best_league TEXT,
        best_market TEXT,
        worst_sport TEXT,
        worst_league TEXT,
        worst_market TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS shark_rejected_pick_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pick_id TEXT,
        sport TEXT,
        league TEXT,
        market TEXT,
        reason TEXT,
        shark_score REAL,
        risk_level TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_ml_tables()
    print("V69 ML tables initialized")
