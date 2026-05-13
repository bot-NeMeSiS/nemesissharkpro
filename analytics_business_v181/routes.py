import os, sqlite3, json, time
from datetime import datetime, timedelta
from pathlib import Path
from flask import Blueprint, jsonify, render_template, redirect, session, request

analytics_business_v181_bp = Blueprint('analytics_business_v181', __name__)

DB_PATH = os.environ.get('DATABASE_URL') or os.environ.get('DB_PATH') or '/data/database.db'
if str(DB_PATH).startswith('sqlite:///'):
    DB_PATH = str(DB_PATH).replace('sqlite:///', '', 1)


def _is_admin():
    user = session.get('user') or {}
    return bool(user and (user.get('role') == 'admin' or user.get('is_admin') is True))


def _db_exists():
    try:
        return Path(DB_PATH).exists()
    except Exception:
        return False


def _conn():
    con = sqlite3.connect(DB_PATH, timeout=5)
    con.row_factory = sqlite3.Row
    return con


def _tables():
    if not _db_exists():
        return []
    try:
        with _conn() as con:
            return [r[0] for r in con.execute("select name from sqlite_master where type='table' order by name").fetchall()]
    except Exception:
        return []


def _cols(table):
    try:
        with _conn() as con:
            return [r[1] for r in con.execute(f"pragma table_info({table})").fetchall()]
    except Exception:
        return []


def _count(table, where='1=1', params=()):
    if not table or not _db_exists():
        return 0
    try:
        with _conn() as con:
            row = con.execute(f"select count(*) c from {table} where {where}", params).fetchone()
            return int(row['c'] or 0)
    except Exception:
        return 0


def _first_existing(candidates, tables):
    for t in candidates:
        if t in tables:
            return t
    return None


def _safe_recent(table, limit=8):
    if not table:
        return []
    try:
        cols = _cols(table)
        order = 'rowid desc'
        for c in ['created_at', 'timestamp', 'sent_at', 'updated_at', 'date']:
            if c in cols:
                order = f"{c} desc"
                break
        with _conn() as con:
            rows = con.execute(f"select * from {table} order by {order} limit ?", (limit,)).fetchall()
            out=[]
            for row in rows:
                d=dict(row)
                out.append({k: (str(v)[:140] if v is not None else None) for k,v in d.items()})
            return out
    except Exception:
        return []


def _membership_counts(users_table):
    if not users_table:
        return {'FREE':0,'PRO':0,'ELITE':0,'ADMIN':0,'OTHER':0}
    cols = _cols(users_table)
    field = None
    for candidate in ['membership','plan','tier','role']:
        if candidate in cols:
            field = candidate
            break
    if not field:
        return {'FREE':_count(users_table),'PRO':0,'ELITE':0,'ADMIN':0,'OTHER':0}
    result={'FREE':0,'PRO':0,'ELITE':0,'ADMIN':0,'OTHER':0}
    try:
        with _conn() as con:
            rows=con.execute(f"select upper(coalesce({field}, 'FREE')) k, count(*) c from {users_table} group by upper(coalesce({field}, 'FREE'))").fetchall()
            for r in rows:
                k = (r['k'] or 'FREE').upper()
                if k in result:
                    result[k] += int(r['c'] or 0)
                elif 'ADMIN' in k:
                    result['ADMIN'] += int(r['c'] or 0)
                else:
                    result['OTHER'] += int(r['c'] or 0)
    except Exception:
        pass
    return result


def _daily_series(table, days=14):
    if not table:
        return []
    cols=_cols(table)
    date_col=None
    for c in ['created_at','timestamp','date','sent_at','updated_at']:
        if c in cols:
            date_col=c; break
    # Real-only: if no timestamp column exists, return an empty premium series instead of inventing dates.
    if not date_col:
        return []
    since=(datetime.utcnow()-timedelta(days=days)).strftime('%Y-%m-%d')
    try:
        with _conn() as con:
            rows=con.execute(f"select substr({date_col},1,10) d, count(*) c from {table} where {date_col} >= ? group by substr({date_col},1,10) order by d asc", (since,)).fetchall()
            return [{'date':r['d'],'count':int(r['c'] or 0)} for r in rows]
    except Exception:
        return []


def v181_business_snapshot():
    tables=_tables()
    users=_first_existing(['users','clientes','clients'], tables)
    picks=_first_existing(['picks','user_picks','bet_picks'], tables)
    fixtures=_first_existing(['fixtures_cache','fixtures','matches_cache','matches'], tables)
    favorites=_first_existing(['favorites','user_favorites','client_favorites'], tables)
    telegram_logs=_first_existing(['telegram_delivery_logs','telegram_logs','telegram_events','v174_telegram_admin_events','telegram_auto_logs'], tables)
    notification_queue=_first_existing(['notification_queue','push_notification_queue','live_alerts','alerts'], tables)
    automation_logs=_first_existing(['automation_runs','automation_logs','job_runs','v178_automation_runs'], tables)
    membership=_membership_counts(users)
    total_users=sum(membership.values()) if users else 0
    paying=membership.get('PRO',0)+membership.get('ELITE',0)
    conversion=round((paying/total_users)*100, 1) if total_users else 0
    engagement_sources=[]
    for label, table in [('Favoritos', favorites), ('Telegram', telegram_logs), ('Alertas', notification_queue), ('Automatizaciones', automation_logs)]:
        engagement_sources.append({'label':label,'table':table or 'no detectada','count':_count(table) if table else 0})
    health=[]
    health.append({'label':'Base de datos','ok':_db_exists(),'detail':DB_PATH if _db_exists() else 'No encontrada'})
    health.append({'label':'Usuarios','ok':bool(users),'detail':users or 'Tabla no detectada'})
    health.append({'label':'Fixtures reales','ok':bool(fixtures and _count(fixtures)>0),'detail':f"{_count(fixtures)} registros" if fixtures else 'Tabla no detectada'})
    health.append({'label':'Telegram activity','ok':bool(telegram_logs and _count(telegram_logs)>0),'detail':f"{_count(telegram_logs)} eventos" if telegram_logs else 'Tabla no detectada'})
    risks=[]
    if not users: risks.append('No se detectó tabla de usuarios para analytics de membresías.')
    if fixtures and _count(fixtures)==0: risks.append('Fixtures detectados pero sin registros cacheados: sincronizar partidos reales.')
    if not telegram_logs: risks.append('No se detectó tabla de logs Telegram: analytics de delivery limitado.')
    if conversion == 0 and total_users > 0: risks.append('No hay usuarios PRO/ELITE detectados todavía; revisar conversión cuando active pagos.')
    if not risks: risks.append('Sin riesgos críticos de analytics detectados ahora mismo.')
    return {
        'version':'V181_ANALYTICS_BUSINESS_PRO',
        'generated_at':datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        'tables':{'users':users,'picks':picks,'fixtures':fixtures,'favorites':favorites,'telegram_logs':telegram_logs,'notifications':notification_queue,'automation':automation_logs},
        'kpis':{
            'users_total':total_users,
            'paying_users':paying,
            'conversion_percent':conversion,
            'fixtures_total':_count(fixtures) if fixtures else 0,
            'picks_total':_count(picks) if picks else 0,
            'favorites_total':_count(favorites) if favorites else 0,
            'telegram_events':_count(telegram_logs) if telegram_logs else 0,
            'queued_alerts':_count(notification_queue) if notification_queue else 0,
            'automation_runs':_count(automation_logs) if automation_logs else 0,
        },
        'membership':membership,
        'engagement_sources':engagement_sources,
        'series':{
            'users':_daily_series(users),
            'telegram':_daily_series(telegram_logs),
            'alerts':_daily_series(notification_queue),
            'automation':_daily_series(automation_logs),
        },
        'recent':{
            'users':_safe_recent(users, 5),
            'telegram':_safe_recent(telegram_logs, 6),
            'alerts':_safe_recent(notification_queue, 6),
            'automation':_safe_recent(automation_logs, 6),
        },
        'health':health,
        'risks':risks,
        'quick_actions':[
            {'label':'Admin Intelligence','url':'/admin/intelligence'},
            {'label':'Automation Engine','url':'/admin/automation-engine'},
            {'label':'Backup Recovery','url':'/admin/backup-recovery'},
            {'label':'Telegram Control','url':'/admin/telegram-control'},
            {'label':'PWA Install','url':'/admin/pwa-install'},
            {'label':'System Health','url':'/admin/system-health'},
        ]
    }


@analytics_business_v181_bp.route('/api/v181/business-analytics')
def api_v181_business_analytics():
    if not _is_admin():
        return jsonify({'ok':False,'error':'admin_required'}), 403
    return jsonify({'ok':True,'data':v181_business_snapshot()})


@analytics_business_v181_bp.route('/admin/business-analytics')
@analytics_business_v181_bp.route('/admin/analytics-business')
@analytics_business_v181_bp.route('/admin/analytics')
def admin_v181_business_analytics():
    if not _is_admin():
        return redirect('/admin-login')
    return render_template('v181/business_analytics.html', snap=v181_business_snapshot())
