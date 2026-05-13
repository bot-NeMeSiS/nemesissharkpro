
import os
from datetime import datetime

def business_admin_payload():
    env = {
        "THE_ODDS_API_KEY": bool(os.environ.get("THE_ODDS_API_KEY")),
        "TELEGRAM_BOT_TOKEN": bool(os.environ.get("TELEGRAM_BOT_TOKEN")),
        "TELEGRAM_CHAT_ID": bool(os.environ.get("TELEGRAM_CHAT_ID")),
        "OPENAI_API_KEY": bool(os.environ.get("OPENAI_API_KEY")),
        "DATABASE_PATH": bool(os.environ.get("DATABASE_PATH")),
        "DB_PATH": bool(os.environ.get("DB_PATH")),
    }

    modules = [
        {"name": "Usuarios", "status": "PREPARADO", "href": "/admin"},
        {"name": "Membresías", "status": "PREPARADO", "href": "/planes"},
        {"name": "Picks", "status": "ACTIVO", "href": "/admin/closing-picks"},
        {"name": "Telegram", "status": "ACTIVO", "href": "/admin/telegram-pro"},
        {"name": "Real Data", "status": "ACTIVO", "href": "/admin/real-data-sync"},
        {"name": "Live Ops", "status": "ACTIVO", "href": "/admin/live-ops"},
        {"name": "Arquitectura", "status": "ACTIVO", "href": "/admin/architecture"},
    ]

    score = min(100, 78 + sum(2 for v in env.values() if v))

    return {
        "version": "V130_BUSINESS_ADMIN_CENTER",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "business_score": score,
        "env": env,
        "modules": modules,
        "safe_mode": True,
        "stripe_deferred": True,
        "no_fake_policy": True
    }
