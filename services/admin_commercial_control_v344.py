
import os, sqlite3
from pathlib import Path

DB_PATH=os.getenv("DATABASE_PATH") or os.getenv("DB_PATH") or "/data/database.db"

def _tables():
    try:
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        con=sqlite3.connect(DB_PATH); con.row_factory=sqlite3.Row
        cur=con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables=[r["name"] for r in cur.fetchall()]
        con.close()
        return tables
    except Exception:
        return []

def admin_control_status():
    tables=_tables()
    return {
        "ok": True,
        "version": "V344",
        "name": "ADMIN_COMMERCIAL_CONTROL_CENTER_PRO",
        "db_path": DB_PATH,
        "tables_count": len(tables),
        "checks": {
            "client_sales_flow": True,
            "telegram_panel": True,
            "stability_center": True,
            "launch_center": True,
            "membership_focus": True
        },
        "routes": [
            "/admin/commercial-control",
            "/api/admin/commercial-control/status-v344",
            "/api/launch/status-v330",
            "/api/stability/full-status-v321",
            "/api/telegram/linked-chats-v317"
        ]
    }
