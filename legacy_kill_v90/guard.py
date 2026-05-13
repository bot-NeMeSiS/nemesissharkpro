
from datetime import datetime

def get_real_feed_safe(force=False):
    try:
        from real_match_v89.real_match_engine import get_real_feed
        return get_real_feed(force=force)
    except Exception as e:
        return {"ok":False,"source":"none","message":"Real Match Engine no disponible. No se muestran demos.","error":str(e),"matches":[],"buckets":{"live":[],"today":[],"upcoming":[]},"counts":{"total":0,"live":0,"today":0,"upcoming":0},"generated_at":datetime.utcnow().isoformat()}

def find_real_match(match_id):
    feed=get_real_feed_safe(False); wanted=str(match_id)
    for m in feed.get("matches",[]):
        if str(m.get("id"))==wanted or str(m.get("legacy_id",""))==wanted:
            return m, feed
    return None, feed

def purge_fake_db(get_db_func=None):
    if not get_db_func: return {"ok":False,"reason":"get_db no disponible"}
    fake=["LIVERPOOL","CHELSEA","ELCHE","ALAVES","ALAVÉS","NAPOLI","BOLOGNA","RAYO","GIRONA","TONDELA","MOREIRENSE","DEMO","TEST","TEAM A","TEAM B","09/05/2026","11/05/2026"]
    try:
        conn=get_db_func(); cur=conn.cursor(); affected=0
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'"); tables=[r[0] for r in cur.fetchall()]
        for table in ["picks","matches","events","fixtures","games"]:
            if table not in tables: continue
            for term in fake:
                like=f"%{term}%"
                for cols in [("title","pick","league","kickoff_time"),("home_team","away_team","league","commence_time"),("home","away","league","date")]:
                    try:
                        cond=' OR '.join([f"UPPER(COALESCE({c},'')) LIKE ?" for c in cols])
                        cur.execute(f"UPDATE {table} SET active=0 WHERE ({cond})", tuple([like]*len(cols)))
                        affected += max(cur.rowcount or 0,0)
                    except Exception: pass
        conn.commit(); conn.close(); return {"ok":True,"affected":affected}
    except Exception as e: return {"ok":False,"error":str(e)}
