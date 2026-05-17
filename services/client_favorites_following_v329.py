
import os, sqlite3
from pathlib import Path
DB_PATH=os.getenv("DATABASE_PATH") or os.getenv("DB_PATH") or "/data/database.db"

def connect():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    con=sqlite3.connect(DB_PATH); con.row_factory=sqlite3.Row
    return con

def ensure_tables():
    con=connect(); cur=con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS client_favorites (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT,
      item_type TEXT NOT NULL DEFAULT 'team',
      item_name TEXT NOT NULL,
      item_key TEXT,
      source TEXT DEFAULT 'client',
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(user_id,item_type,item_name)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS client_following_matches (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT,
      match_id TEXT,
      home_team TEXT,
      away_team TEXT,
      league TEXT,
      status TEXT DEFAULT 'watch',
      notify_telegram INTEGER DEFAULT 1,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(user_id,match_id)
    )
    """)
    con.commit(); con.close()

def status():
    ensure_tables()
    con=connect(); cur=con.cursor()
    cur.execute("SELECT COUNT(*) AS n FROM client_favorites")
    fav=int(cur.fetchone()["n"])
    cur.execute("SELECT COUNT(*) AS n FROM client_following_matches")
    fol=int(cur.fetchone()["n"])
    con.close()
    return {"ok":True,"version":"V329","favorites_count":fav,"following_count":fol,"real_only":True}

def list_demo_safe():
    ensure_tables()
    con=connect(); cur=con.cursor()
    cur.execute("SELECT item_type,item_name,item_key,created_at FROM client_favorites ORDER BY created_at DESC LIMIT 25")
    fav=[dict(r) for r in cur.fetchall()]
    cur.execute("SELECT match_id,home_team,away_team,league,status,notify_telegram,created_at FROM client_following_matches ORDER BY created_at DESC LIMIT 25")
    fol=[dict(r) for r in cur.fetchall()]
    con.close()
    return {"ok":True,"version":"V329","favorites":fav,"following":fol,"real_only":True}
