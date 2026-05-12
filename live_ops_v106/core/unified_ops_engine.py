
import os
import sqlite3
from pathlib import Path
from datetime import datetime

def _env(name):
    return os.environ.get(name)

def _db_candidates():
    return [
        _env("DATABASE_PATH"),
        _env("DB_PATH"),
        "/data/app.db",
        "/data/database.db",
        "app.db",
        "database.db",
    ]

def detect_db():
    for candidate in _db_candidates():
        if not candidate:
            continue
        p = Path(candidate)
        if p.exists():
            return str(p)
    return None

def _safe_query_count(db_path, tables):
    if not db_path:
        return None
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        for table in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                value = cur.fetchone()[0]
                con.close()
                return value
            except Exception:
                continue
        con.close()
    except Exception:
        return None
    return None

def _safe_recent_rows(db_path, tables, limit=12):
    if not db_path:
        return []
    try:
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        for table in tables:
            try:
                cur.execute(f"SELECT * FROM {table} LIMIT ?", (limit,))
                rows = [dict(r) for r in cur.fetchall()]
                con.close()
                return rows
            except Exception:
                continue
        con.close()
    except Exception:
        return []
    return []

def env_status():
    keys = [
        "THE_ODDS_API_KEY",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "OPENAI_API_KEY",
        "DATABASE_PATH",
        "DB_PATH",
        "RENDER_EXTERNAL_URL",
    ]
    return [
        {
            "name": key,
            "configured": bool(_env(key)),
            "status": "OK" if _env(key) else "MISSING",
        }
        for key in keys
    ]

def module_status():
    return [
        {"name": "Real Core Engine", "status": "ACTIVO", "priority": "critical", "href": "/admin/real-core"},
        {"name": "Cliente PRO", "status": "ACTIVO", "priority": "critical", "href": "/cliente"},
        {"name": "Picks reales", "status": "ACTIVO", "priority": "critical", "href": "/cliente/picks"},
        {"name": "Partidos reales", "status": "ACTIVO", "priority": "critical", "href": "/cliente/partidos"},
        {"name": "Live seguro", "status": "ACTIVO", "priority": "high", "href": "/en-directo"},
        {"name": "Admin PRO Center", "status": "ACTIVO", "priority": "critical", "href": "/admin"},
        {"name": "Auto Pick Engine", "status": "ACTIVO", "priority": "high", "href": "/auto-pick-engine"},
        {"name": "SHARK AI Ultra", "status": "PREPARADO", "priority": "high", "href": "/api/v100/shark-ai-ultra/health"},
        {"name": "Live Trading", "status": "PREPARADO", "priority": "high", "href": "/api/v101/live-trading/health"},
        {"name": "Analytics PRO", "status": "PREPARADO", "priority": "medium", "href": "/api/v102/analytics/health"},
        {"name": "Mobile/PWA", "status": "PREPARADO", "priority": "medium", "href": "/manifest.webmanifest"},
        {"name": "Telegram Alerts", "status": "PREPARADO" if _env("TELEGRAM_BOT_TOKEN") else "PENDIENTE", "priority": "high", "href": "/admin/live-ops"},
    ]

def build_live_ops_status():
    db = detect_db()
    envs = env_status()
    modules = module_status()

    users_count = _safe_query_count(db, ["users", "user", "clientes", "clients"])
    picks_count = _safe_query_count(db, ["picks", "pick", "bets", "apuestas"])
    matches_count = _safe_query_count(db, ["matches", "partidos", "fixtures", "events"])

    configured_envs = sum(1 for e in envs if e["configured"])
    active_modules = sum(1 for m in modules if m["status"] in ["ACTIVO", "PREPARADO"])

    warnings = []
    if not db:
        warnings.append("No se detecta base de datos persistente. Revisa /data/app.db o DATABASE_PATH.")
    if not _env("THE_ODDS_API_KEY"):
        warnings.append("THE_ODDS_API_KEY falta: los feeds reales pueden quedar limitados.")
    if not _env("TELEGRAM_BOT_TOKEN"):
        warnings.append("Telegram no está configurado: las alertas quedan preparadas pero OFF.")
    if users_count is None:
        warnings.append("Tabla de usuarios no detectada con nombres comunes.")
    if picks_count is None:
        warnings.append("Tabla de picks no detectada con nombres comunes.")
    if matches_count is None:
        warnings.append("Tabla de partidos no detectada con nombres comunes.")

    health = 60
    if db:
        health += 10
    health += min(20, int((configured_envs / max(len(envs), 1)) * 20))
    health += min(10, int((active_modules / max(len(modules), 1)) * 10))
    health -= min(15, len(warnings) * 2)
    health = max(0, min(100, health))

    return {
        "version": "V106_UNIFIED_LIVE_OPERATIONS",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "health_score": health,
        "database": {
            "detected": bool(db),
            "path": db or "NO_DETECTED",
            "users_count": users_count if users_count is not None else "UNKNOWN",
            "picks_count": picks_count if picks_count is not None else "UNKNOWN",
            "matches_count": matches_count if matches_count is not None else "UNKNOWN",
        },
        "env": envs,
        "modules": modules,
        "warnings": warnings,
        "quick_actions": [
            {"label": "Panel cliente", "href": "/cliente", "type": "link"},
            {"label": "Picks reales", "href": "/cliente/picks", "type": "link"},
            {"label": "Partidos", "href": "/cliente/partidos", "type": "link"},
            {"label": "En directo", "href": "/en-directo", "type": "link"},
            {"label": "Real Core", "href": "/admin/real-core", "type": "link"},
            {"label": "Auto Pick", "href": "/auto-pick-engine", "type": "link"},
            {"label": "Live Ops API", "href": "/api/v106/live-ops/status", "type": "api"},
            {"label": "Telegram Test", "href": "/api/v106/live-ops/telegram/test", "type": "api"},
        ],
    }

def build_visible_routes_map():
    return {
        "cliente": [
            {"name": "Inicio cliente", "href": "/cliente"},
            {"name": "Picks", "href": "/cliente/picks"},
            {"name": "Partidos", "href": "/cliente/partidos"},
            {"name": "En directo", "href": "/en-directo"},
            {"name": "Rendimiento", "href": "/cliente/rendimiento"},
        ],
        "admin": [
            {"name": "Admin Center", "href": "/admin"},
            {"name": "Admin Live Ops", "href": "/admin/live-ops"},
            {"name": "Real Core", "href": "/admin/real-core"},
            {"name": "Auto Pick Engine", "href": "/auto-pick-engine"},
            {"name": "Admin PRO SaaS", "href": "/admin-pro-saas"},
        ],
        "api": [
            {"name": "V106 Status", "href": "/api/v106/live-ops/status"},
            {"name": "V106 Routes", "href": "/api/v106/live-ops/routes"},
            {"name": "V106 Modules", "href": "/api/v106/live-ops/modules"},
            {"name": "V106 Telegram Test", "href": "/api/v106/live-ops/telegram/test"},
        ],
    }
