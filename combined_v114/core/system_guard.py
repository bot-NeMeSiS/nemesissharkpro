
from datetime import datetime
from pathlib import Path
import os

def build_system_guard():
    checks = [
        {"name": "app.py", "ok": Path("app.py").exists()},
        {"name": "templates", "ok": Path("templates").exists()},
        {"name": "static", "ok": Path("static").exists()},
        {"name": "V112 Picks Manager", "ok": Path("combined_v114/core/picks_manager.py").exists()},
        {"name": "V113 Live UI Ultra", "ok": Path("templates/live_ultra_v113.html").exists()},
        {"name": "V114 Routes", "ok": Path("combined_v114/routes/combined_routes.py").exists()},
    ]
    env = {
        "THE_ODDS_API_KEY": bool(os.environ.get("THE_ODDS_API_KEY")),
        "TELEGRAM_BOT_TOKEN": bool(os.environ.get("TELEGRAM_BOT_TOKEN")),
        "TELEGRAM_CHAT_ID": bool(os.environ.get("TELEGRAM_CHAT_ID")),
        "DATABASE_PATH": bool(os.environ.get("DATABASE_PATH")),
        "DB_PATH": bool(os.environ.get("DB_PATH")),
    }
    score = 70 + sum(3 for c in checks if c["ok"]) + sum(2 for v in env.values() if v)
    return {
        "version": "V114_SYSTEM_GUARD",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "score": min(100, score),
        "checks": checks,
        "env": env,
        "message": "V114 consolida Picks Manager, Live UI Ultra, planes, cuenta/logout y arquitectura de control."
    }
