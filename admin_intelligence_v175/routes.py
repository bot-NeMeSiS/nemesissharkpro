
import os, sqlite3, json, time
from datetime import datetime, timezone
from pathlib import Path
from flask import Blueprint, jsonify, render_template, redirect, session, request

admin_intelligence_v175_bp = Blueprint('admin_intelligence_v175', __name__)

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
    return sqlite3.connect(DB_PATH, timeout=4)

def _count(table, where='1=1'):
    if not _db_exists():
        return 0
    try:
        with _conn() as con:
            cur=con.cursor()
            cur.execute(f"select count(*) from {table} where {where}")
            return int(cur.fetchone()[0] or 0)
    except Exception:
        return 0

def _tables():
    if not _db_exists(): return []
    try:
        with _conn() as con:
            cur=con.cursor()
            cur.execute("select name from sqlite_master where type='table' order by name")
            return [r[0] for r in cur.fetchall()]
    except Exception:
        return []

def _sample_recent(table, limit=5):
    if not _db_exists(): return []
    try:
        with _conn() as con:
            con.row_factory = sqlite3.Row
            cur=con.cursor()
            cur.execute(f"select * from {table} order by rowid desc limit ?", (limit,))
            rows=[]
            for row in cur.fetchall():
                d=dict(row)
                rows.append({k: (str(v)[:120] if v is not None else None) for k,v in d.items()})
            return rows
    except Exception:
        return []

def v175_snapshot():
    tables=_tables()
    env={
        'telegram_token': bool(os.environ.get('TELEGRAM_BOT_TOKEN') or os.environ.get('TELEGRAM_TOKEN')),
        'telegram_chat_id': bool(os.environ.get('TELEGRAM_CHAT_ID')),
        'telegram_admin_chat_id': bool(os.environ.get('TELEGRAM_ADMIN_CHAT_ID')),
        'odds_api_key': bool(os.environ.get('THE_ODDS_API_KEY') or os.environ.get('ODDS_API_KEY')),
        'openai_key': bool(os.environ.get('OPENAI_API_KEY')),
        'render': bool(os.environ.get('RENDER') or os.environ.get('RENDER_SERVICE_ID')),
    }
    users_table = 'users' if 'users' in tables else ('clientes' if 'clientes' in tables else None)
    fixtures_table = 'fixtures_cache' if 'fixtures_cache' in tables else ('fixtures' if 'fixtures' in tables else None)
    picks_table = 'picks' if 'picks' in tables else None
    telegram_logs_table = None
    for name in ['telegram_delivery_logs','telegram_logs','telegram_events','v174_telegram_admin_events']:
        if name in tables:
            telegram_logs_table=name; break
    alerts_table = None
    for name in ['notification_queue','push_notification_queue','alerts','live_alerts']:
        if name in tables:
            alerts_table=name; break
    counts={
        'users': _count(users_table) if users_table else 0,
        'free': _count(users_table, "upper(coalesce(membership, plan, role, 'FREE'))='FREE'") if users_table else 0,
        'pro': _count(users_table, "upper(coalesce(membership, plan, role, ''))='PRO'") if users_table else 0,
        'elite': _count(users_table, "upper(coalesce(membership, plan, role, ''))='ELITE'") if users_table else 0,
        'fixtures': _count(fixtures_table) if fixtures_table else 0,
        'picks': _count(picks_table) if picks_table else 0,
        'telegram_logs': _count(telegram_logs_table) if telegram_logs_table else 0,
        'alerts': _count(alerts_table) if alerts_table else 0,
    }
    health=[]
    health.append({'name':'Base de datos persistente','ok':_db_exists(),'detail':DB_PATH if _db_exists() else 'No encontrada aún'})
    health.append({'name':'Telegram bot token','ok':env['telegram_token'],'detail':'Configurado' if env['telegram_token'] else 'Falta TELEGRAM_BOT_TOKEN'})
    health.append({'name':'Telegram admin privado','ok':env['telegram_admin_chat_id'],'detail':'TELEGRAM_ADMIN_CHAT_ID activo' if env['telegram_admin_chat_id'] else 'Añade tu chat_id privado admin'})
    health.append({'name':'Telegram canal/grupo','ok':env['telegram_chat_id'],'detail':'TELEGRAM_CHAT_ID activo' if env['telegram_chat_id'] else 'Opcional: canal/grupo'})
    health.append({'name':'Odds API','ok':env['odds_api_key'],'detail':'API real configurada' if env['odds_api_key'] else 'Falta key de cuotas/fixtures'})
    risks=[]
    if not env['telegram_admin_chat_id']: risks.append('Falta TELEGRAM_ADMIN_CHAT_ID para avisos privados admin.')
    if counts['fixtures']==0: risks.append('No hay fixtures cacheados: los paneles live pueden verse vacíos correctamente.')
    if not env['odds_api_key']: risks.append('Sin Odds API key no entrarán partidos/cuotas reales nuevos.')
    if not risks: risks.append('Sin avisos críticos detectados ahora mismo.')
    return {
        'version':'V175_ADMIN_INTELLIGENCE_BUSINESS_CONTROL_PRO',
        'generated_at':datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        'tables':tables[:40],
        'counts':counts,
        'env':env,
        'health':health,
        'risks':risks,
        'recent_telegram': _sample_recent(telegram_logs_table, 6) if telegram_logs_table else [],
        'recent_alerts': _sample_recent(alerts_table, 6) if alerts_table else [],
        'quick_actions':[
            {'label':'Telegram Control','url':'/admin/telegram-control'},
            {'label':'Telegram Auto Delivery','url':'/admin/telegram-auto-delivery'},
            {'label':'Business Center','url':'/admin/business'},
            {'label':'Fixtures Sync','url':'/admin/fixtures-sync'},
            {'label':'Push Center','url':'/admin/push-center'},
            {'label':'App Audit','url':'/admin/app-audit'},
        ]
    }

@admin_intelligence_v175_bp.route('/api/v175/admin-intelligence')
def api_v175_admin_intelligence():
    if not _is_admin():
        return jsonify({'ok':False,'error':'admin_required'}), 403
    return jsonify({'ok':True,'data':v175_snapshot()})

@admin_intelligence_v175_bp.route('/admin/intelligence')
@admin_intelligence_v175_bp.route('/admin/control-tower-pro')
@admin_intelligence_v175_bp.route('/admin/business-pro')
def admin_v175_intelligence():
    if not _is_admin():
        return redirect('/admin-login')
    return render_template('admin_intelligence_v175.html', snap=v175_snapshot())

@admin_intelligence_v175_bp.route('/admin/v175/telegram-private-test', methods=['POST'])
def admin_v175_telegram_private_test():
    if not _is_admin():
        return redirect('/admin-login')
    # Reuse existing telegram endpoints when available by redirecting to V174 control panel.
    return redirect('/admin/telegram-control')
