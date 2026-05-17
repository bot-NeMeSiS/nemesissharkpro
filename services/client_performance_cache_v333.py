
import os, sqlite3, time
from pathlib import Path
DB_PATH=os.getenv("DATABASE_PATH") or os.getenv("DB_PATH") or "/data/database.db"

def ensure_tables():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    con=sqlite3.connect(DB_PATH); cur=con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS app_cache_status (
      cache_key TEXT PRIMARY KEY,
      cache_group TEXT,
      last_update TEXT,
      ttl_seconds INTEGER DEFAULT 900,
      status TEXT DEFAULT 'ready'
    )
    """)
    con.commit(); con.close()

def status():
    ensure_tables()
    return {
      "ok": True,
      "version": "V333",
      "name": "CLIENT_PERFORMANCE_CACHE_READINESS_PRO",
      "real_only": True,
      "cache_ready": True,
      "groups": ["live","fixtures","1x2","telegram","match_center"],
      "goal": "más velocidad visual y base para ahorrar API"
    }
