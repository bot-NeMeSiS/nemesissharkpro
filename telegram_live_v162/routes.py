from flask import Blueprint, jsonify, render_template, session, redirect, request
from datetime import datetime
import os, sqlite3
from pathlib import Path

telegram_live_v162_bp = Blueprint('telegram_live_v162_bp', __name__)


def _uid():
    try:
        return session.get('user_id') or session.get('id') or session.get('username') or session.get('user') or 'default'
    except Exception:
        return 'default'


def _is_admin_session():
    try:
        role = str(session.get('role') or session.get('user_role') or '').lower()
        user = str(session.get('user') or session.get('username') or session.get('admin') or '').lower()
        return bool(session.get('is_admin') or session.get('admin_logged_in') or role == 'admin' or user == 'admin')
    except Exception:
        return False


def _db_candidates():
    return [os.environ.get('DATABASE_PATH'), os.environ.get('DB_PATH'), '/data/app.db', '/data/database.db', 'app.db', 'database.db']


def _db_path():
    for item in _db_candidates():
        if item and Path(item).exists():
            return str(Path(item))
    return None


def _connect():
    path = _db_path()
    if not path:
        return None, None
    try:
        con = sqlite3.connect(path)
        con.row_factory = sqlite3.Row
        return con, path
    except Exception:
        return None, path


def _table_exists(con, table):
    if not con:
        return False
    try:
        row = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
        return bool(row)
    except Exception:
        return False


def _safe_scalar(con, sql, params=(), default=0):
    if not con:
        return default
    try:
        row = con.execute(sql, params).fetchone()
        if row is None:
            return default
        return list(row)[0]
    except Exception:
        return default


def _recent_from_table(con, table, limit=12):
    if not con or not _table_exists(con, table):
        return []
    try:
        rows = con.execute(f"SELECT * FROM {table} ORDER BY rowid DESC LIMIT ?", (limit,)).fetchall()
    except Exception:
        return []
    out = []
    for row in rows:
        d = dict(row)
        title = d.get('title') or d.get('message') or d.get('body') or d.get('pick') or d.get('event') or d.get('kind') or 'Alerta real'
        status = d.get('status') or d.get('state') or d.get('result') or d.get('kind') or 'registrado'
        created = d.get('created_at') or d.get('updated_at') or d.get('sent_at') or d.get('date') or ''
        out.append({'title': str(title)[:140], 'status': str(status)[:40], 'created_at': str(created)[:40], 'source': table})
    return out


def _telegram_env():
    token = bool(os.environ.get('TELEGRAM_BOT_TOKEN'))
    chat = bool(os.environ.get('TELEGRAM_CHAT_ID') or os.environ.get('TELEGRAM_TEST_CHAT_ID') or os.environ.get('TELEGRAM_FREE_CHAT_ID') or os.environ.get('TELEGRAM_PRO_CHAT_ID') or os.environ.get('TELEGRAM_ELITE_CHAT_ID'))
    username = os.environ.get('TELEGRAM_BOT_USERNAME') or ''
    return {
        'bot_token': token,
        'chat_target': chat,
        'bot_username': username,
        'ready': token and chat,
        'status': 'OK' if token and chat else 'PENDIENTE'
    }


def _plan_policy(plan):
    p = str(plan or 'FREE').upper()
    policies = {
        'FREE': {'min_score': 74, 'delay': 'alertas esenciales', 'label': 'FREE'},
        'PRO': {'min_score': 66, 'delay': 'alertas premium', 'label': 'PRO'},
        'ELITE': {'min_score': 58, 'delay': 'máxima prioridad', 'label': 'ELITE'},
        'ADMIN': {'min_score': 0, 'delay': 'control total', 'label': 'ADMIN'},
    }
    return policies.get(p, policies['FREE'])


def build_telegram_live_center(user_id=None):
    con, path = _connect()
    try:
        telegram_users = _safe_scalar(con, "SELECT COUNT(*) FROM users WHERE COALESCE(telegram_chat_id,'')!=''", default=0)
        total_users = _safe_scalar(con, "SELECT COUNT(*) FROM users", default=0)
        pending_alerts = _safe_scalar(con, "SELECT COUNT(*) FROM telegram_alerts WHERE LOWER(COALESCE(status,'')) IN ('pending','queued','retry')", default=0)
        sent_alerts = _safe_scalar(con, "SELECT COUNT(*) FROM telegram_alerts WHERE LOWER(COALESCE(status,'')) IN ('sent','ok','success')", default=0)
        failed_alerts = _safe_scalar(con, "SELECT COUNT(*) FROM telegram_alerts WHERE LOWER(COALESCE(status,'')) IN ('failed','error','blocked')", default=0)
        recent_alerts = _recent_from_table(con, 'telegram_alerts', 14)
        if not recent_alerts:
            recent_alerts = _recent_from_table(con, 'alerts_log', 14) or _recent_from_table(con, 'logs', 14)
    finally:
        try:
            if con: con.close()
        except Exception:
            pass

    env = _telegram_env()
    warnings = []
    if not env['bot_token']:
        warnings.append('Falta TELEGRAM_BOT_TOKEN: no se enviarán alertas reales.')
    if not env['chat_target']:
        warnings.append('Falta chat/canal destino: configura TELEGRAM_CHAT_ID o canales por plan.')
    if not path:
        warnings.append('No se detecta SQLite persistente; Telegram no podrá leer usuarios vinculados.')
    if not recent_alerts:
        warnings.append('No hay logs recientes de Telegram. Estado vacío premium, sin inventar envíos.')

    live_score = 55 + (20 if env['ready'] else 0) + (10 if path else 0) + (8 if telegram_users else 0) + (7 if recent_alerts else 0)
    live_score = max(0, min(100, live_score))
    user_plan = str(session.get('plan') or session.get('membership') or 'FREE').upper()

    signals = []
    if pending_alerts:
        signals.append({'level': 'warning', 'title': 'Alertas pendientes', 'text': f'{pending_alerts} alerta(s) esperando envío/reintento.'})
    if failed_alerts:
        signals.append({'level': 'danger', 'title': 'Errores detectados', 'text': f'{failed_alerts} alerta(s) fallidas registradas.'})
    if env['ready']:
        signals.append({'level': 'ok', 'title': 'Telegram preparado', 'text': 'Bot y destino configurados para alertas reales.'})
    else:
        signals.append({'level': 'empty', 'title': 'Telegram pendiente', 'text': 'Falta configuración real; no se muestran envíos fake.'})

    return {
        'ok': True,
        'version': 'V162_TELEGRAM_LIVE_PREMIUM',
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'database': {'detected': bool(path), 'path': path or 'NO_DETECTED'},
        'env': env,
        'live_score': live_score,
        'counts': {
            'users_total': int(total_users or 0),
            'users_linked': int(telegram_users or 0),
            'pending_alerts': int(pending_alerts or 0),
            'sent_alerts': int(sent_alerts or 0),
            'failed_alerts': int(failed_alerts or 0),
        },
        'policy': {
            'real_only': True,
            'no_fake_messages': True,
            'no_fake_scores': True,
            'stripe_disabled': True,
            'plan_policy': _plan_policy(user_plan),
        },
        'quick_actions': [
            {'label': 'Conectar Telegram', 'href': '/alertas'},
            {'label': 'Admin Telegram', 'href': '/admin/telegram'},
            {'label': 'API estado', 'href': '/api/v162/telegram-live'},
            {'label': 'Live Ecosystem', 'href': '/live-ecosystem'},
            {'label': 'Cliente PRO', 'href': '/cliente/pro'},
        ],
        'signals': signals,
        'recent_alerts': recent_alerts,
        'warnings': warnings,
    }


@telegram_live_v162_bp.route('/api/v162/telegram-live')
def api_telegram_live():
    return jsonify(build_telegram_live_center(request.args.get('user_id') or _uid()))


@telegram_live_v162_bp.route('/api/v162/telegram-signals')
def api_telegram_signals():
    data = build_telegram_live_center(request.args.get('user_id') or _uid())
    return jsonify({'ok': True, 'version': data['version'], 'signals': data['signals'], 'counts': data['counts'], 'policy': data['policy']})


@telegram_live_v162_bp.route('/telegram-live')
@telegram_live_v162_bp.route('/cliente/telegram-live')
def page_client_telegram_live():
    return render_template('telegram_live_v162.html', data=build_telegram_live_center(_uid()), admin=False)


@telegram_live_v162_bp.route('/admin/telegram-live')
@telegram_live_v162_bp.route('/admin/telegram-premium')
def page_admin_telegram_live():
    if not _is_admin_session():
        return redirect('/admin-login')
    return render_template('telegram_live_v162.html', data=build_telegram_live_center(_uid()), admin=True)
