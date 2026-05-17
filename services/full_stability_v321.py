
import os, sqlite3
from pathlib import Path
DB_PATH=os.getenv("DATABASE_PATH") or os.getenv("DB_PATH") or "/data/database.db"
def db_status():
    try:
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        con=sqlite3.connect(DB_PATH); con.row_factory=sqlite3.Row
        cur=con.cursor(); cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables=[r["name"] for r in cur.fetchall()]; con.close()
        return {"ok":True,"db_path":DB_PATH,"tables_count":len(tables),"tables":tables[:80]}
    except Exception as e:
        return {"ok":False,"db_path":DB_PATH,"error":str(e)}
def telegram_status():
    token=os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN") or ""
    admin=os.getenv("TELEGRAM_ADMIN_CHAT_ID") or os.getenv("ADMIN_TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID") or ""
    linked=0
    try:
        from services.telegram_linking_v317 import ensure_telegram_tables,count_linked_chats
        ensure_telegram_tables(); linked=count_linked_chats()
    except Exception: pass
    return {"token_present":bool(token),"admin_chat_present":bool(admin),"linked_chats":linked,"auto_enabled":os.getenv("TELEGRAM_AUTO_BROADCAST_ENABLED","true").lower() in ["1","true","yes","on"],"interval_seconds":os.getenv("TELEGRAM_AUTO_BROADCAST_INTERVAL_SECONDS","3600")}
def one_x2_status():
    try:
        from services.smart_1x2_engine_v319 import discover_real_1x2_matches, build_combi_summary
        data=discover_real_1x2_matches(limit=10); data["combi"]=build_combi_summary(data.get("matches",[])); return data
    except Exception as e:
        return {"ok":False,"error":str(e),"matches":[],"low_data":True,"real_only":True}
def full_status():
    return {"ok":True,"version":"V321","name":"FULL_STABILITY_CLIENT_LIVE_TELEGRAM_1X2_FINAL","db":db_status(),"telegram":telegram_status(),"one_x2":one_x2_status(),"live":{"real_only":True,"score_fields":["home_score","away_score","score.home","score.away"],"minute_fields":["minute","elapsed","time","status_minute"],"crest_fields":["crest","logo","badge","image","team_logo"],"fallback":"LOW_DATA"}}
