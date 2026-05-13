
import os
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = "nemesis.db"

def check_file(path):
    return Path(path).exists()

def get_env_bool(name):
    return os.getenv(name, "").lower() in ("1", "true", "yes", "on")

def safe_count(table, db_path=DB_PATH):
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        conn.close()
        return count
    except Exception:
        return None

def db_integrity(db_path=DB_PATH):
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("PRAGMA integrity_check")
        result = cur.fetchone()[0]
        conn.close()
        return "OK" if result == "ok" else result
    except Exception as exc:
        return f"ERROR: {exc}"

def get_launch_candidate_status():
    checks = []

    file_checks = [
        ("App principal", "app.py"),
        ("Env example", ".env.example"),
        ("Requirements", "requirements.txt"),
        ("UI V70", "static/css/v70_premium_ui.css"),
        ("Retention V74", "retention_v74/retention_engine.py"),
        ("Personalization V75", "personalization_v75/personalization_engine.py"),
        ("Community V76", "community_v76/community_engine.py"),
        ("Performance V77", "performance_v77/performance_engine.py"),
    ]

    for label, path in file_checks:
        ok = check_file(path)
        checks.append({"area": label, "status": "OK" if ok else "REVISAR", "description": path})

    env_checks = [
        "SECRET_KEY",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "STABILITY_HARD_MODE",
        "PERFORMANCE_SAFE_MODE",
        "V73_OBSERVABILITY_ENABLED",
        "V74_RETENTION_ENGINE_ENABLED",
        "V75_PERSONALIZATION_ENABLED",
        "V76_COMMUNITY_ENABLED",
        "V77_PERFORMANCE_OPTIMIZATION_ENABLED",
    ]

    missing_env = []
    for key in env_checks:
        if not os.getenv(key):
            missing_env.append(key)

    checks.append({
        "area": "Variables Render",
        "status": "OK" if not missing_env else "REVISAR",
        "description": "OK" if not missing_env else "Faltan: " + ", ".join(missing_env),
    })

    integrity = db_integrity()
    checks.append({"area": "SQLite integrity", "status": "OK" if integrity == "OK" else "REVISAR", "description": integrity})

    tables = [
        "telegram_queue", "push_queue", "shark_ml_dataset", "user_retention_profiles",
        "user_personalization_profiles", "community_activity", "app_error_events"
    ]
    table_status = []
    for table in tables:
        count = safe_count(table)
        table_status.append({"table": table, "count": count})

    blocked = len([c for c in checks if c["status"] != "OK"])
    score = max(100 - blocked * 8 - min(len(missing_env) * 2, 20), 0)

    return {
        "status": "LAUNCH CANDIDATE READY" if score >= 85 else "REVISAR ANTES DE LANZAR",
        "launch_candidate_score": score,
        "blocked_checks": blocked,
        "missing_env": missing_env,
        "checks": checks,
        "tables": table_status,
        "stripe_status": "BLOQUEADO INTENCIONADAMENTE",
        "next_step": "Beta privada real con usuarios controlados. Stripe después de feedback.",
        "generated_at": datetime.utcnow().isoformat(),
    }
