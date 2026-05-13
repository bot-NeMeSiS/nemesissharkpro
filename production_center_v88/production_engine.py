
"""
NeMeSiS SHARK PRO V88
Admin Production Center

Objetivo:
- Centro único de control de producción.
- Health checks.
- Variables críticas.
- DB status.
- Telegram/OpenAI/Odds API status básico.
- Render readiness.
"""

import os
import sqlite3
import time
from datetime import datetime


CRITICAL_ENV = [
    "SECRET_KEY",
    "ODDS_API_KEY",
    "THE_ODDS_API_KEY",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "OPENAI_API_KEY",
]

RENDER_ENV = [
    "RENDER",
    "RENDER_SERVICE_ID",
    "RENDER_EXTERNAL_URL",
    "PORT",
]

FEATURE_FLAGS = [
    "ENABLE_ODDS_API",
    "ENABLE_PRO_ALERTS",
    "ENABLE_OPENAI",
    "ENABLE_PUSH_NOTIFICATIONS",
    "STABILITY_HARD_MODE",
    "PERFORMANCE_SAFE_MODE",
    "V86_LIVE_DATA_REAL_ENGINE_ENABLED",
    "V87_SHARK_AI_PICK_QUALITY_ENABLED",
    "V88_ADMIN_PRODUCTION_CENTER_ENABLED",
]


def mask_value(value):
    if not value:
        return None
    value = str(value)
    if len(value) <= 8:
        return "***"
    return value[:3] + "***" + value[-3:]


def bool_env(name, default=False):
    raw = os.getenv(name)
    if raw is None:
        return default
    return str(raw).lower() in ("1", "true", "yes", "on")


def get_db_path():
    return os.getenv("DB_PATH") or os.getenv("SQLITE_DB_PATH") or "nemesis.db"


def check_db():
    db_path = get_db_path()
    start = time.time()
    payload = {
        "name": "SQLite DB",
        "status": "UNKNOWN",
        "db_path": db_path,
        "latency_ms": None,
        "tables": [],
        "error": None,
    }

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        payload["tables"] = [row[0] for row in cur.fetchall()]
        cur.execute("SELECT 1")
        conn.close()
        payload["status"] = "OK"
    except Exception as e:
        payload["status"] = "WARN"
        payload["error"] = str(e)

    payload["latency_ms"] = round((time.time() - start) * 1000, 2)
    return payload


def check_env():
    items = []
    for key in CRITICAL_ENV:
        value = os.getenv(key)
        items.append({
            "key": key,
            "present": bool(value),
            "masked": mask_value(value),
            "status": "OK" if value else "MISSING",
        })

    flags = []
    for key in FEATURE_FLAGS:
        raw = os.getenv(key)
        flags.append({
            "key": key,
            "value": raw if raw is not None else "",
            "enabled": bool_env(key, False),
        })

    render = []
    for key in RENDER_ENV:
        value = os.getenv(key)
        render.append({
            "key": key,
            "present": bool(value),
            "masked": mask_value(value),
        })

    return {
        "critical": items,
        "feature_flags": flags,
        "render": render,
    }


def check_services():
    env = check_env()
    critical = {x["key"]: x["present"] for x in env["critical"]}

    odds_ok = critical.get("ODDS_API_KEY") or critical.get("THE_ODDS_API_KEY")
    telegram_ok = critical.get("TELEGRAM_BOT_TOKEN") and critical.get("TELEGRAM_CHAT_ID")
    openai_ok = critical.get("OPENAI_API_KEY")

    return [
        {
            "service": "The Odds API",
            "status": "OK" if odds_ok else "MISSING_KEY",
            "description": "Fuente principal de partidos, cuotas y mercados.",
        },
        {
            "service": "Telegram",
            "status": "OK" if telegram_ok else "MISSING_CONFIG",
            "description": "Alertas de picks y comunicación premium.",
        },
        {
            "service": "OpenAI / SHARK AI",
            "status": "OK" if openai_ok else "OPTIONAL_DISABLED",
            "description": "Análisis SHARK AI avanzado.",
        },
        {
            "service": "Render",
            "status": "OK" if os.getenv("RENDER") or os.getenv("PORT") else "LOCAL_OR_UNKNOWN",
            "description": "Entorno cloud / deploy.",
        },
    ]


def check_files():
    expected = [
        "app.py",
        "requirements.txt",
        "runtime.txt",
        "Procfile",
        ".env.example",
        "templates",
        "static",
    ]

    out = []
    for item in expected:
        exists = os.path.exists(item)
        out.append({
            "path": item,
            "exists": exists,
            "status": "OK" if exists else "MISSING",
        })
    return out


def production_score():
    db = check_db()
    env = check_env()
    services = check_services()
    files = check_files()

    score = 100

    if db["status"] != "OK":
        score -= 15

    missing_critical = len([x for x in env["critical"] if not x["present"] and x["key"] in ("SECRET_KEY",)])
    score -= missing_critical * 20

    missing_files = len([x for x in files if not x["exists"]])
    score -= missing_files * 8

    service_warn = len([x for x in services if x["status"] not in ("OK", "OPTIONAL_DISABLED", "LOCAL_OR_UNKNOWN")])
    score -= service_warn * 8

    score = max(0, min(100, score))

    if score >= 90:
        label = "PRODUCCIÓN FUERTE"
    elif score >= 75:
        label = "PRODUCCIÓN OK"
    elif score >= 55:
        label = "REVISAR"
    else:
        label = "RIESGO"

    return {
        "score": score,
        "label": label,
    }


def get_production_status():
    return {
        "version": "V88",
        "status": "ADMIN PRODUCTION CENTER ACTIVO",
        "generated_at": datetime.utcnow().isoformat(),
        "score": production_score(),
        "db": check_db(),
        "env": check_env(),
        "services": check_services(),
        "files": check_files(),
        "quick_actions": [
            {"name": "Health check", "url": "/health"},
            {"name": "Production status API", "url": "/api/production-center/status"},
            {"name": "Live data quality", "url": "/admin/live-data-quality"},
            {"name": "SHARK quality", "url": "/admin/shark-quality"},
            {"name": "Telegram status", "url": "/api/telegram-status"},
        ],
    }


def health_payload():
    status = get_production_status()
    return {
        "ok": status["score"]["score"] >= 55,
        "status": status["score"]["label"],
        "score": status["score"]["score"],
        "version": "V88",
        "time": datetime.utcnow().isoformat(),
    }
