"""V97 Admin PRO SaaS Center.
Panel de control sin demos: lee Real Core, variables de entorno y SQLite si está disponible.
"""
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from core.real_core_engine import RealCoreEngine

DB_CANDIDATES = [
    os.getenv("DATABASE_PATH"),
    os.getenv("SQLITE_DB_PATH"),
    "instance/nemesis.db",
    "nemesis.db",
    "app.db",
]


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _env_status():
    token = bool(os.getenv("TELEGRAM_BOT_TOKEN"))
    chat = bool(os.getenv("TELEGRAM_CHAT_ID"))
    odds = bool(os.getenv("ODDS_API_KEY") or os.getenv("THE_ODDS_API_KEY"))
    flask_secret = bool(os.getenv("SECRET_KEY") or os.getenv("FLASK_SECRET_KEY"))
    return {
        "telegram_bot_token": token,
        "telegram_chat_id": chat,
        "telegram_ready": token and chat,
        "odds_api_ready": odds,
        "secret_key_ready": flask_secret,
        "render_detected": bool(os.getenv("RENDER") or os.getenv("RENDER_SERVICE_ID") or os.getenv("RENDER_EXTERNAL_URL")),
        "render_service": os.getenv("RENDER_SERVICE_NAME") or os.getenv("RENDER_SERVICE_ID") or "No detectado localmente",
        "environment": os.getenv("FLASK_ENV") or os.getenv("ENV") or "production-ready",
    }


def _db_path():
    for candidate in DB_CANDIDATES:
        if not candidate:
            continue
        p = Path(candidate)
        if p.exists():
            return p
    return None


def _safe_count(cur, sql, params=()):
    try:
        cur.execute(sql, params)
        row = cur.fetchone()
        return int(row[0] or 0)
    except Exception:
        return 0


def _user_stats():
    path = _db_path()
    empty = {
        "db_found": False,
        "db_path": "No detectada en este entorno",
        "total_users": 0,
        "free": 0,
        "pro": 0,
        "elite": 0,
        "admin": 0,
        "telegram_connected": 0,
        "suspended": 0,
    }
    if not path:
        return empty
    try:
        con = sqlite3.connect(str(path))
        cur = con.cursor()
        stats = {
            "db_found": True,
            "db_path": str(path),
            "total_users": _safe_count(cur, "SELECT COUNT(*) FROM users"),
            "free": _safe_count(cur, "SELECT COUNT(*) FROM users WHERE UPPER(COALESCE(plan,''))='FREE'"),
            "pro": _safe_count(cur, "SELECT COUNT(*) FROM users WHERE UPPER(COALESCE(plan,''))='PRO'"),
            "elite": _safe_count(cur, "SELECT COUNT(*) FROM users WHERE UPPER(COALESCE(plan,''))='ELITE'"),
            "admin": _safe_count(cur, "SELECT COUNT(*) FROM users WHERE LOWER(COALESCE(role,''))='admin'"),
            "telegram_connected": _safe_count(cur, "SELECT COUNT(*) FROM users WHERE COALESCE(telegram_chat_id,'')<>'' OR COALESCE(telegram_alerts_enabled,0)=1"),
            "suspended": _safe_count(cur, "SELECT COUNT(*) FROM users WHERE COALESCE(suspended,0)=1"),
        }
        con.close()
        return stats
    except Exception as exc:
        empty["db_path"] = f"Error leyendo DB: {exc}"
        return empty


def _feed_stats(force=False):
    feed = RealCoreEngine.fetch(force=force)
    matches = feed.get("matches") or []
    buckets = feed.get("buckets") or {}
    return {
        "ok": bool(feed.get("ok")),
        "message": feed.get("message") or "Real Core consultado",
        "source": feed.get("source") or "Real Core",
        "total_matches": len(matches),
        "live": len(buckets.get("live") or []),
        "today": len(buckets.get("today") or []),
        "upcoming": len(buckets.get("upcoming") or []),
        "top_score": max([int(m.get("shark_score") or 0) for m in matches] or [0]),
        "strong_picks": len([m for m in matches if int(m.get("shark_score") or 0) >= 80]),
        "last_checked": _now_iso(),
    }


def build_admin_center(force=False):
    env = _env_status()
    users = _user_stats()
    feed = _feed_stats(force=force)
    checks = [
        {"name": "Real Core", "ok": feed["ok"], "detail": f"{feed['total_matches']} partidos reales"},
        {"name": "Odds API", "ok": env["odds_api_ready"], "detail": "Clave configurada" if env["odds_api_ready"] else "Falta ODDS_API_KEY / THE_ODDS_API_KEY"},
        {"name": "Telegram", "ok": env["telegram_ready"], "detail": "Bot y chat listos" if env["telegram_ready"] else "Faltan variables Telegram"},
        {"name": "Base de usuarios", "ok": users["db_found"], "detail": users["db_path"]},
        {"name": "Render", "ok": env["render_detected"], "detail": env["render_service"]},
        {"name": "Secret key", "ok": env["secret_key_ready"], "detail": "Configurada" if env["secret_key_ready"] else "Recomendado configurar SECRET_KEY"},
    ]
    health_score = round(sum(1 for c in checks if c["ok"]) / len(checks) * 100)
    return {
        "ok": True,
        "version": "V97",
        "title": "Admin PRO SaaS Center",
        "health_score": health_score,
        "checks": checks,
        "env": env,
        "users": users,
        "feed": feed,
        "actions": [
            {"label": "Refrescar Real Core", "url": "/admin-pro-saas?force=true"},
            {"label": "Estado Telegram", "url": "/api/v95/telegram/status"},
            {"label": "Live Center", "url": "/live-center-pro"},
            {"label": "SHARK AI", "url": "/shark-ai-pro"},
        ],
        "next_step": "V98 Historial real ROI/winrate + cierre de picks",
    }
