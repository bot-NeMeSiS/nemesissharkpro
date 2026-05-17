
import os, sqlite3
from pathlib import Path
DB_PATH=os.getenv("DATABASE_PATH") or os.getenv("DB_PATH") or "/data/database.db"

def db_tables():
    try:
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        con=sqlite3.connect(DB_PATH); con.row_factory=sqlite3.Row
        cur=con.cursor(); cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        t=[r["name"] for r in cur.fetchall()]; con.close(); return t
    except Exception: return []

def status():
    tables=db_tables()
    return {
      "ok":True,
      "version":"V326",
      "real_only":True,
      "db_tables_count":len(tables),
      "match_center":{
        "sections":["estado","live","1x2","shark","alertas","recap"],
        "fallback":"LOW_DATA si faltan datos reales"
      }
    }
