
import os, sqlite3
from pathlib import Path
DB_PATH=os.getenv("DATABASE_PATH") or os.getenv("DB_PATH") or "/data/database.db"

def db_tables():
    try:
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        con=sqlite3.connect(DB_PATH); con.row_factory=sqlite3.Row
        cur=con.cursor(); cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables=[r["name"] for r in cur.fetchall()]; con.close(); return tables
    except Exception: return []

def feed_status():
    tables=db_tables()
    return {
      "ok": True,
      "version": "V331",
      "name": "ACTIVITY_FEED_LIVE_CLIENT_PRO",
      "real_only": True,
      "db_tables_count": len(tables),
      "feed_items": [
        {"type":"live","title":"Revisar partidos en directo","action":"/cliente/live-central"},
        {"type":"1x2","title":"Crear o revisar combi 1X2","action":"/cliente/1x2"},
        {"type":"match","title":"Abrir Match Center","action":"/cliente/match-center-premium"},
        {"type":"telegram","title":"Telegram automático preparado","action":"/api/telegram/auto-status-v316"}
      ]
    }
