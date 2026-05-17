
import os, sqlite3
from pathlib import Path
DB_PATH=os.getenv("DATABASE_PATH") or os.getenv("DB_PATH") or "/data/database.db"
def status():
    try:
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        con=sqlite3.connect(DB_PATH); con.row_factory=sqlite3.Row
        cur=con.cursor(); cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables=[r["name"] for r in cur.fetchall()]; con.close()
        return {"ok":True,"version":"V327","db_tables_count":len(tables),"home_density":"ready","real_only":True}
    except Exception as e:
        return {"ok":False,"version":"V327","error":str(e),"real_only":True}
