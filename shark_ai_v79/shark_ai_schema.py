
"""
NeMeSiS SHARK PRO V79
SHARK AI Real Evolution schema
"""

import sqlite3
from datetime import datetime


def init_shark_ai_v79_tables(db_path="nemesis.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS shark_ai_predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pick_id TEXT,
        sport TEXT,
        league TEXT,
        match_name TEXT,
        market TEXT,
        selection TEXT,
        odds REAL,
        base_score REAL,
        adaptive_score REAL,
        value_score REAL,
        risk_score REAL,
        confidence_level TEXT,
        prediction_label TEXT,
        prediction_probability REAL,
        ai_reason TEXT,
        model_version TEXT DEFAULT 'V79_RULE_BASED_EVOLUTION',
        result TEXT,
        profit_loss REAL DEFAULT 0,
        created_at TEXT,
        settled_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS shark_ai_pattern_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pattern_key TEXT UNIQUE,
        pattern_type TEXT,
        sample_size INTEGER DEFAULT 0,
        wins INTEGER DEFAULT 0,
        losses INTEGER DEFAULT 0,
        voids INTEGER DEFAULT 0,
        avg_odds REAL DEFAULT 0,
        avg_score REAL DEFAULT 0,
        win_rate REAL DEFAULT 0,
        roi REAL DEFAULT 0,
        reliability TEXT DEFAULT 'UNKNOWN',
        score_adjustment REAL DEFAULT 0,
        updated_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS shark_ai_model_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model_version TEXT,
        dataset_size INTEGER DEFAULT 0,
        prediction_count INTEGER DEFAULT 0,
        accuracy REAL DEFAULT 0,
        roi REAL DEFAULT 0,
        reliability_score REAL DEFAULT 0,
        best_pattern TEXT,
        worst_pattern TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS shark_ai_rejected_signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        signal_type TEXT,
        sport TEXT,
        league TEXT,
        market TEXT,
        reason TEXT,
        risk_score REAL,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_shark_ai_v79_tables()
    print("V79 SHARK AI tables initialized")
