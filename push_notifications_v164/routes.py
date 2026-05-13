from flask import Blueprint, jsonify, render_template, session, request
from datetime import datetime
from pathlib import Path
import os, sqlite3, json

push_notifications_v164_bp = Blueprint('push_notifications_v164_bp', __name__)

def _uid():
    try:
        return str(session.get('user_id') or session.get('id') or session.get('username') or session.get('user') or 'default')
    except Exception:
        return 'default'

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
        return bool(con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone())
    except Exception:
        return False

def _ensure_tables(con):
    if not con:
        return False
    con.execute("""CREATE TABLE IF NOT EXISTS push_subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        endpoint TEXT,
        subscription_json TEXT,
        channel TEXT DEFAULT 'web_push',
        enabled INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS notification_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        channel TEXT,
        title TEXT,
        body TEXT,
        action_url TEXT,
        status TEXT DEFAULT 'pending',
        payload_json TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        sent_at TEXT
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS client_activity_v164 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        event_type TEXT,
        title TEXT,
        metadata_json TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    con.commit()
    return True

def _count(con, table, where='1=1'):
    if not con or not _table_exists(con, table):
        return 0
    try:
        return int(con.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}").fetchone()[0] or 0)
    except Exception:
        return 0

def _recent_queue(con, limit=12):
    if not con or not _table_exists(con, 'notification_queue'):
        return []
    try:
        rows = con.execute("SELECT * FROM notification_queue ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    except Exception:
        return []
    return [{'id': r['id'], 'channel': r['channel'] or 'app', 'title': r['title'] or 'Notificación SHARK', 'body': r['body'] or '', 'status': r['status'] or 'pending', 'action_url': r['action_url'] or '/cliente/pro', 'created_at': r['created_at'] or ''} for r in rows]

def _smart_system(user_id=None):
    try:
        from smart_live_v163.routes import build_smart_live_system
        return build_smart_live_system(user_id or _uid())
    except Exception as exc:
        return {'ok': False, 'signals': [], 'counts': {}, 'alert_engine': {'pending_alerts': 0}, 'smart_score': 0, 'error': str(exc)}

def build_push_foundation(user_id=None):
    user_id = user_id or _uid()
    con, path = _connect()
    ensured = False
    try:
        ensured = _ensure_tables(con) if con else False
        safe_user = str(user_id).replace("'", "''")
        subscriptions = _count(con, 'push_subscriptions', 'enabled=1')
        user_subscriptions = _count(con, 'push_subscriptions', "enabled=1 AND user_id='{}'".format(safe_user))
        pending = _count(con, 'notification_queue', "LOWER(COALESCE(status,'')) IN ('pending','queued','retry','')")
        sent = _count(con, 'notification_queue', "LOWER(COALESCE(status,'')) IN ('sent','delivered')")
        failed = _count(con, 'notification_queue', "LOWER(COALESCE(status,'')) IN ('failed','error')")
        queue = _recent_queue(con)
    finally:
        try:
            if con: con.close()
        except Exception:
            pass
    smart = _smart_system(user_id)
    smart_signals = smart.get('signals') or []
    suggested = []
    for s in smart_signals[:6]:
        suggested.append({'title': s.get('title') or 'Señal SHARK', 'body': s.get('text') or 'Nueva señal real disponible.', 'channel': 'app_push_ready', 'action_url': s.get('action') or '/smart-live', 'source': 'smart_live_v163', 'queued': False})
    if not suggested:
        suggested.append({'title': 'SHARK Push preparado', 'body': 'No hay señales reales suficientes todavía. El sistema queda listo sin inventar datos.', 'channel': 'app_push_ready', 'action_url': '/fixtures/today-pro', 'source': 'empty_state', 'queued': False})
    web_push_ready = bool(os.environ.get('VAPID_PUBLIC_KEY') and os.environ.get('VAPID_PRIVATE_KEY'))
    telegram_ready = bool(os.environ.get('TELEGRAM_BOT_TOKEN') or os.environ.get('BOT_TOKEN'))
    service_worker_ready = Path('service-worker.js').exists()
    return {'ok': True, 'version': 'V164_PUSH_NOTIFICATIONS_REAL_FOUNDATION', 'generated_at': datetime.utcnow().isoformat() + 'Z', 'database': {'detected': bool(path), 'path': path or 'NO_DETECTED', 'tables_ready': ensured}, 'readiness': {'web_push_vapid_configured': web_push_ready, 'telegram_configured': telegram_ready, 'service_worker_present': service_worker_ready, 'pwa_ready': True, 'stripe_disabled': True}, 'counts': {'subscriptions_active': subscriptions, 'subscriptions_for_user': user_subscriptions, 'queue_pending': pending, 'queue_sent': sent, 'queue_failed': failed, 'smart_signals_available': len(smart_signals)}, 'channels': [{'id': 'app', 'name': 'App / PWA', 'status': 'ready_base', 'description': 'Centro de notificaciones interno y service worker preparado.'}, {'id': 'telegram', 'name': 'Telegram', 'status': 'configured' if telegram_ready else 'needs_env', 'description': 'Conecta con Telegram Live Premium cuando exista token y usuarios vinculados.'}, {'id': 'web_push', 'name': 'Web Push', 'status': 'configured' if web_push_ready else 'needs_vapid', 'description': 'Base preparada. Para envío push real faltan claves VAPID en Render.'}], 'suggested_alerts': suggested, 'recent_queue': queue, 'policy': {'no_fake_notifications': True, 'no_fake_scores': True, 'no_fake_picks': True, 'real_signals_only': True, 'user_control_first': True}}

@push_notifications_v164_bp.route('/api/v164/push-status')
def api_push_status():
    return jsonify(build_push_foundation(request.args.get('user_id') or _uid()))

@push_notifications_v164_bp.route('/api/v164/notification-center')
def api_notification_center():
    data = build_push_foundation(request.args.get('user_id') or _uid())
    return jsonify({'ok': True, 'version': data['version'], 'counts': data['counts'], 'suggested_alerts': data['suggested_alerts'], 'recent_queue': data['recent_queue'], 'policy': data['policy']})

@push_notifications_v164_bp.route('/api/v164/notification-queue')
def api_notification_queue():
    data = build_push_foundation(request.args.get('user_id') or _uid())
    return jsonify({'ok': True, 'version': data['version'], 'queue': data['recent_queue'], 'counts': data['counts']})

@push_notifications_v164_bp.route('/api/v164/push-subscribe', methods=['POST'])
def api_push_subscribe():
    payload = request.get_json(silent=True) or {}
    endpoint = payload.get('endpoint') or (payload.get('subscription') or {}).get('endpoint') or ''
    con, path = _connect()
    if not con:
        return jsonify({'ok': False, 'error': 'DATABASE_NOT_DETECTED', 'message': 'No hay base SQLite detectada para guardar suscripciones push.'}), 200
    try:
        _ensure_tables(con)
        con.execute("INSERT INTO push_subscriptions(user_id, endpoint, subscription_json, channel, enabled) VALUES(?,?,?,?,1)", (_uid(), endpoint, json.dumps(payload, ensure_ascii=False), 'web_push'))
        con.commit()
        return jsonify({'ok': True, 'version': 'V164_PUSH_NOTIFICATIONS_REAL_FOUNDATION', 'message': 'Suscripción push guardada en SQLite.', 'database': path})
    except Exception as exc:
        return jsonify({'ok': False, 'error': str(exc)}), 200
    finally:
        try: con.close()
        except Exception: pass

@push_notifications_v164_bp.route('/api/v164/queue-alert', methods=['POST'])
def api_queue_alert():
    payload = request.get_json(silent=True) or {}
    title = str(payload.get('title') or 'Alerta SHARK').strip()[:120]
    body = str(payload.get('body') or 'Nueva señal real disponible.').strip()[:500]
    action_url = str(payload.get('action_url') or '/smart-live').strip()[:250]
    channel = str(payload.get('channel') or 'app').strip()[:40]
    con, path = _connect()
    if not con:
        return jsonify({'ok': False, 'error': 'DATABASE_NOT_DETECTED'}), 200
    try:
        _ensure_tables(con)
        con.execute("INSERT INTO notification_queue(user_id, channel, title, body, action_url, status, payload_json) VALUES(?,?,?,?,?,'pending',?)", (_uid(), channel, title, body, action_url, json.dumps(payload, ensure_ascii=False)))
        con.commit()
        return jsonify({'ok': True, 'version': 'V164_PUSH_NOTIFICATIONS_REAL_FOUNDATION', 'queued': {'title': title, 'channel': channel, 'action_url': action_url}})
    except Exception as exc:
        return jsonify({'ok': False, 'error': str(exc)}), 200
    finally:
        try: con.close()
        except Exception: pass

@push_notifications_v164_bp.route('/notifications-pro')
@push_notifications_v164_bp.route('/cliente/notifications')
@push_notifications_v164_bp.route('/cliente/notificaciones')
@push_notifications_v164_bp.route('/admin/push-center')
def page_notifications_pro():
    return render_template('push_notifications_v164.html', data=build_push_foundation(_uid()))
