
import os
from datetime import datetime

def build_product_state():
    modules = [
        {"name": "Cliente PRO", "href": "/cliente/home-pro", "status": "VISIBLE"},
        {"name": "Picks reales", "href": "/cliente/picks", "status": "REAL CORE"},
        {"name": "Partidos reales", "href": "/cliente/partidos", "status": "REAL CORE"},
        {"name": "Live Ultra", "href": "/live-ultra", "status": "PREPARADO"},
        {"name": "SHARK AI", "href": "/cliente/shark-ai", "status": "PREPARADO"},
        {"name": "Mi cuenta", "href": "/cuenta", "status": "VISIBLE"},
        {"name": "Planes", "href": "/planes", "status": "VISIBLE"},
        {"name": "Telegram PRO", "href": "/admin/telegram-pro", "status": "CONTROLADO"},
        {"name": "Real Data Sync", "href": "/admin/real-data-sync", "status": "NO FAKE"},
        {"name": "Admin Center", "href": "/admin", "status": "CONTROL"},
    ]
    env = {
        "THE_ODDS_API_KEY": bool(os.environ.get("THE_ODDS_API_KEY")),
        "TELEGRAM_BOT_TOKEN": bool(os.environ.get("TELEGRAM_BOT_TOKEN")),
        "TELEGRAM_CHAT_ID": bool(os.environ.get("TELEGRAM_CHAT_ID")),
        "DATABASE_PATH": bool(os.environ.get("DATABASE_PATH")),
        "DB_PATH": bool(os.environ.get("DB_PATH")),
    }
    score = min(100, 72 + sum(2 for _ in modules) + sum(1 for v in env.values() if v))
    return {
        "version": "V119_PRODUCT_CONTROL_CENTER",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "score": score,
        "modules": modules,
        "env": env,
        "policy": {
            "no_fake_matches": True,
            "no_fake_picks": True,
            "client_first": True,
            "admin_controlled": True,
            "render_ready": True,
        },
        "next": [
            "V120 arquitectura split real de app.py",
            "V121 cierre automático de picks",
            "V122 Stripe final",
        ],
    }
