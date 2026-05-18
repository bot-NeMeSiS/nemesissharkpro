
import os, sqlite3
from pathlib import Path

DB_PATH = os.getenv("DATABASE_PATH") or os.getenv("DB_PATH") or "/data/database.db"

CORE_ROUTES = [
    "/cliente/pro",
    "/cliente/1x2",
    "/cliente/live-command-center",
    "/cliente/match-center-premium",
    "/cliente/favorites-following",
    "/cliente/membresia",
    "/admin/commercial-control",
    "/api/stability/full-status-v321",
    "/api/launch/status-v330",
    "/api/telegram/linked-chats-v317",
]

def _db_status():
    try:
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r["name"] for r in cur.fetchall()]
        con.close()
        return {"ok": True, "path": DB_PATH, "tables_count": len(tables), "tables_sample": tables[:40]}
    except Exception as exc:
        return {"ok": False, "path": DB_PATH, "error": str(exc)}

def hardening_status():
    return {
        "ok": True,
        "version": "V345",
        "name": "PRODUCT_HARDENING_CLEANUP_PRO",
        "db": _db_status(),
        "core_routes": CORE_ROUTES,
        "cleanup": {
            "hide_old_injections": True,
            "dedupe_membership_1x2": True,
            "scroll_unlock": True,
            "technical_noise_hidden": True,
            "commercial_stable_base": True
        },
        "recommended_next": "Real data/live pipeline consolidation"
    }
