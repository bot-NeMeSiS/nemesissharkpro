
import os
import sqlite3
from datetime import datetime
from pathlib import Path

def _db_candidates():
    return [
        os.environ.get("DATABASE_PATH"),
        os.environ.get("DB_PATH"),
        "/data/app.db",
        "/data/database.db",
        "app.db",
        "database.db",
    ]

def _existing_db():
    for item in _db_candidates():
        if not item:
            continue
        p = Path(item)
        if p.exists():
            return str(p)
    return None

def _safe_count_users(db_path):
    if not db_path:
        return None
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        # Try common table names
        for table in ["users", "user", "clientes", "clients"]:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                value = cur.fetchone()[0]
                con.close()
                return value
            except Exception:
                continue
        con.close()
    except Exception:
        pass
    return None

def _env_status(name):
    value = os.environ.get(name)
    return {
        "name": name,
        "configured": bool(value),
        "preview": "OK" if value else "MISSING"
    }

def build_admin_center_status():
    db_path = _existing_db()
    users_count = _safe_count_users(db_path)

    envs = [
        _env_status("THE_ODDS_API_KEY"),
        _env_status("TELEGRAM_BOT_TOKEN"),
        _env_status("TELEGRAM_CHAT_ID"),
        _env_status("OPENAI_API_KEY"),
        _env_status("DATABASE_PATH"),
        _env_status("DB_PATH"),
    ]

    configured = sum(1 for e in envs if e["configured"])
    total = len(envs)

    modules = [
        {"name": "Real Core Engine", "status": "ACTIVO", "route": "/admin/real-core"},
        {"name": "Cliente PRO", "status": "ACTIVO", "route": "/cliente"},
        {"name": "Picks reales", "status": "ACTIVO", "route": "/cliente/picks"},
        {"name": "Partidos reales", "status": "ACTIVO", "route": "/cliente/partidos"},
        {"name": "Live Center", "status": "ACTIVO", "route": "/en-directo"},
        {"name": "Historial / banca", "status": "ACTIVO", "route": "/cliente/rendimiento"},
        {"name": "SHARK AI Ultra", "status": "PREPARADO", "route": "/api/v100/shark-ai-ultra/health"},
        {"name": "Live Trading", "status": "PREPARADO", "route": "/api/v101/live-trading/health"},
        {"name": "Analytics PRO", "status": "PREPARADO", "route": "/api/v102/analytics/health"},
        {"name": "Mobile/PWA", "status": "PREPARADO", "route": "/manifest.webmanifest"},
        {"name": "Auto Pick Engine", "status": "ACTIVO", "route": "/auto-pick-engine"},
    ]

    warnings = []
    if not db_path:
        warnings.append("No se detecta base de datos persistente. Revisa /data/app.db o DATABASE_PATH.")
    if not any(e["name"] == "THE_ODDS_API_KEY" and e["configured"] for e in envs):
        warnings.append("The Odds API no está configurada en variables de entorno.")
    if not any(e["name"] == "TELEGRAM_BOT_TOKEN" and e["configured"] for e in envs):
        warnings.append("Telegram no está configurado todavía.")
    if users_count is None:
        warnings.append("No se pudo leer tabla de usuarios; puede ser normal si el esquema usa otro nombre.")

    health_score = 65
    if db_path:
        health_score += 10
    health_score += int((configured / total) * 20)
    if not warnings:
        health_score += 5
    health_score = min(100, health_score)

    return {
        "version": "V105_ADMIN_PRO_CENTER",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "health_score": health_score,
        "database": {
            "detected": bool(db_path),
            "path": db_path or "NO_DETECTED",
            "users_count": users_count if users_count is not None else "UNKNOWN"
        },
        "env": envs,
        "modules": modules,
        "warnings": warnings,
        "quick_links": [
            {"label": "Panel cliente", "href": "/cliente"},
            {"label": "Picks", "href": "/cliente/picks"},
            {"label": "Partidos", "href": "/cliente/partidos"},
            {"label": "Directo", "href": "/en-directo"},
            {"label": "Real Core", "href": "/admin/real-core"},
            {"label": "Auto Pick", "href": "/auto-pick-engine"},
            {"label": "Status API", "href": "/api/v105/admin/center"},
        ]
    }
