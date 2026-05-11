
import os, sqlite3
from datetime import datetime
FAKE_TERMS=['TEAM A','TEAM B','DEMO','TEST','EXAMPLE','MOCK','LIVERPOOL','CHELSEA','RAYO VALLECANO','GIRONA','TONDELA','MOREIRENSE','CF ESTRELA','NACIONAL','TOTTENHAM','LEEDS','NAPOLI','BOLOGNA','AUGSBURG','BORUSSIA','VFB STUTTGART','BAYER LEVERKUSEN','09/05/2026','11/05/2026','2026','H MADRID','MONDAY']
BAD_SOURCES=['','manual','demo','fallback','mock','seed','sample','test']
def get_db_path(): return os.getenv('DB_PATH') or os.getenv('SQLITE_DB_PATH') or 'nemesis.db'
def get_real_feed(force=False):
    try:
        from real_match_v89.real_match_engine import get_real_feed as gf
        return gf(force=force)
    except Exception as e:
        return {'ok':False,'source':'none','message':'No hay datos reales disponibles. V90 bloquea demos/fallbacks.','error':str(e),'matches':[],'buckets':{'live':[],'today':[],'upcoming':[]},'counts':{'total':0,'live':0,'today':0,'upcoming':0},'generated_at':datetime.utcnow().isoformat()}
def real_feed_or_empty(force=False):
    feed=get_real_feed(force)
    if not feed or not feed.get('ok'):
        return {'ok':False,'source':'none','message':feed.get('message') if isinstance(feed,dict) else 'No hay datos reales disponibles.','error':feed.get('error') if isinstance(feed,dict) else None,'matches':[],'buckets':{'live':[],'today':[],'upcoming':[]},'counts':{'total':0,'live':0,'today':0,'upcoming':0},'generated_at':datetime.utcnow().isoformat(),'v90_safe_empty':True}
    feed['v90_safe_empty']=False
    return feed
def purge_legacy_db():
    db=get_db_path(); rep={'db_path':db,'ok':False,'tables_checked':[],'updates':[],'error':None}
    try:
        if not os.path.exists(db): rep['error']='DB no encontrada'; return rep
        con=sqlite3.connect(db); cur=con.cursor(); cur.execute("SELECT name FROM sqlite_master WHERE type='table'"); tables=[r[0] for r in cur.fetchall()]; rep['tables_checked']=tables
        for table in tables:
            if not any(x in table.lower() for x in ['pick','match','event','fixture']): continue
            cur.execute(f'PRAGMA table_info({table})'); cols=[r[1] for r in cur.fetchall()]; low={c.lower():c for c in cols}
            text_cols=[c for c in cols if any(k in c.lower() for k in ['title','team','home','away','league','date','time','kickoff','match','pick','name'])]
            active=low.get('active'); status=low.get('status'); source=low.get('source')
            if not text_cols: continue
            cond=[]; params=[]
            for term in FAKE_TERMS:
                sub=[]; like=f'%{term}%'
                for c in text_cols: sub.append(f"UPPER(COALESCE({c},'')) LIKE ?"); params.append(like)
                cond.append('('+' OR '.join(sub)+')')
            if source:
                sub=[]
                for s in BAD_SOURCES: sub.append(f"LOWER(COALESCE({source},'')) = ?"); params.append(s)
                cond.append('('+' OR '.join(sub)+')')
            sets=[]
            if active: sets.append(f'{active}=0')
            if status: sets.append(f"{status}='blocked_v90'")
            if sets:
                cur.execute(f"UPDATE {table} SET {', '.join(sets)} WHERE ({' OR '.join(cond)})",params)
                rep['updates'].append({'table':table,'rows':cur.rowcount})
        con.commit(); con.close(); rep['ok']=True
    except Exception as e: rep['error']=str(e)
    return rep
def build_view_model(page='inicio',force=False):
    feed=real_feed_or_empty(force); c=feed.get('counts',{})
    return {'page':page,'feed':feed,'total':c.get('total',0),'live':c.get('live',0),'today':c.get('today',0),'upcoming':c.get('upcoming',0),'matches':feed.get('matches',[]),'safe_empty':not feed.get('ok'),'generated_at':feed.get('generated_at')}
def status():
    feed=real_feed_or_empty(False)
    return {'version':'V90','status':'REAL DATA PURGE ACTIVO','strict_real_only':True,'public_pages_protected':['/','/inicio','/picks','/partidos','/hoy','/partido/<id>'],'no_demo_fallback':True,'feed':feed,'db_path':get_db_path(),'modules':['Hard kill legacy cards','Inicio real-only','Picks real-only','Partidos real-only','Detalle protegido','Sin demos si falla API','Purge DB legacy fake','Single card system']}
