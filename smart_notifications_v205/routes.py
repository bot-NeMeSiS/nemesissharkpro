from flask import Blueprint, jsonify, render_template, request, session
from datetime import datetime
import os
import sqlite3

bp_smart_notifications_v205 = Blueprint('smart_notifications_v205', __name__)


def _db_path():
    return os.environ.get('DATABASE_PATH') or os.environ.get('DB_PATH') or '/data/database.db'


def _connect():
    path = _db_path()
    if not os.path.exists(path):
        alt = '/data/app.db'
        path = alt if os.path.exists(alt) else path
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    except Exception:
        pass
    conn = sqlite3.connect(path, timeout=8)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    conn = _connect()
    try:
        conn.execute('''
            create table if not exists smart_notifications_v205 (
                id integer primary key autoincrement,
                user_id text,
                level text not null default 'info',
                category text not null default 'sistema',
                title text not null,
                body text,
                source text not null default 'v205',
                related_url text,
                is_read integer not null default 0,
                created_at text not null,
                dispatched_web integer not null default 1,
                dispatched_telegram integer not null default 0
            )
        ''')
        conn.execute('''
            create table if not exists smart_notification_settings_v205 (
                user_id text primary key,
                picks integer not null default 1,
                live_events integer not null default 1,
                odds integer not null default 1,
                hot_matches integer not null default 1,
                telegram integer not null default 0,
                pwa integer not null default 1,
                updated_at text not null
            )
        ''')
        conn.commit()
    finally:
        conn.close()


def _session_user_id():
    return str(session.get('user_id') or session.get('user') or session.get('username') or 'anonimo')


def _session_user_name():
    return str(session.get('username') or session.get('user_name') or session.get('user') or 'Usuario')


def _settings(user_id):
    _init_db()
    conn = _connect()
    try:
        row = conn.execute('select * from smart_notification_settings_v205 where user_id=?', (user_id,)).fetchone()
        if not row:
            now = datetime.utcnow().isoformat() + 'Z'
            conn.execute('insert into smart_notification_settings_v205 (user_id, updated_at) values (?,?)', (user_id, now))
            conn.commit()
            row = conn.execute('select * from smart_notification_settings_v205 where user_id=?', (user_id,)).fetchone()
        return dict(row)
    finally:
        conn.close()


def _list_notifications(user_id=None, limit=30, include_all=False):
    _init_db()
    conn = _connect()
    try:
        if include_all:
            rows = conn.execute('select * from smart_notifications_v205 order by id desc limit ?', (int(limit),)).fetchall()
        else:
            rows = conn.execute('select * from smart_notifications_v205 where user_id is null or user_id=? order by id desc limit ?', (user_id, int(limit))).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _counts(user_id=None, include_all=False):
    _init_db()
    conn = _connect()
    try:
        if include_all:
            row = conn.execute('select count(*) total, sum(case when is_read=0 then 1 else 0 end) unread from smart_notifications_v205').fetchone()
        else:
            row = conn.execute('select count(*) total, sum(case when is_read=0 then 1 else 0 end) unread from smart_notifications_v205 where user_id is null or user_id=?', (user_id,)).fetchone()
        return {'total': row['total'] or 0, 'sin_leer': row['unread'] or 0}
    finally:
        conn.close()


def notification_payload(admin=False):
    user_id = _session_user_id()
    items = _list_notifications(user_id=user_id, include_all=admin)
    return {
        'version': 'V205_SMART_NOTIFICATIONS_ENGINE_PRO',
        'modo': 'REAL ONLY',
        'generado': datetime.utcnow().isoformat() + 'Z',
        'usuario': _session_user_name(),
        'resumen': _counts(user_id=user_id, include_all=admin),
        'ajustes': _settings(user_id),
        'notificaciones': items,
        'canales': ['App', 'PWA preparada', 'Telegram preparado'],
        'mensaje_vacio': 'Todavía no hay avisos reales. Cuando entren picks, eventos live, cuotas o señales, aparecerán aquí sin inventar datos.'
    }


def create_notification(title, body='', category='sistema', level='info', user_id=None, source='v205', related_url=None):
    _init_db()
    conn = _connect()
    try:
        conn.execute('''insert into smart_notifications_v205
            (user_id, level, category, title, body, source, related_url, created_at)
            values (?,?,?,?,?,?,?,?)''',
            (user_id, level, category, title, body, source, related_url, datetime.utcnow().isoformat() + 'Z'))
        conn.commit()
        return True
    finally:
        conn.close()


@bp_smart_notifications_v205.route('/api/v205/notifications')
def api_notifications_v205():
    admin = bool(request.args.get('admin'))
    return jsonify(notification_payload(admin=admin))


@bp_smart_notifications_v205.route('/api/v205/notifications/read-all', methods=['POST'])
def api_notifications_read_all_v205():
    user_id = _session_user_id()
    _init_db()
    conn = _connect()
    try:
        conn.execute('update smart_notifications_v205 set is_read=1 where user_id is null or user_id=?', (user_id,))
        conn.commit()
        return jsonify({'ok': True, 'mensaje': 'Notificaciones marcadas como leídas.'})
    finally:
        conn.close()


@bp_smart_notifications_v205.route('/api/v205/notifications/settings', methods=['POST'])
def api_notifications_settings_v205():
    user_id = _session_user_id()
    data = request.get_json(silent=True) or request.form or {}
    fields = ['picks', 'live_events', 'odds', 'hot_matches', 'telegram', 'pwa']
    current = _settings(user_id)
    values = {f: int(str(data.get(f, current.get(f, 1))).lower() in ('1','true','on','si','sí','yes')) for f in fields}
    conn = _connect()
    try:
        conn.execute('''replace into smart_notification_settings_v205
            (user_id, picks, live_events, odds, hot_matches, telegram, pwa, updated_at)
            values (?,?,?,?,?,?,?,?)''',
            (user_id, values['picks'], values['live_events'], values['odds'], values['hot_matches'], values['telegram'], values['pwa'], datetime.utcnow().isoformat() + 'Z'))
        conn.commit()
        return jsonify({'ok': True, 'ajustes': _settings(user_id)})
    finally:
        conn.close()


@bp_smart_notifications_v205.route('/api/v205/notifications/create', methods=['POST'])
def api_notifications_create_v205():
    # Endpoint admin/internal: crea avisos reales enviados por otros motores. No genera demos.
    data = request.get_json(silent=True) or request.form or {}
    title = (data.get('title') or data.get('titulo') or '').strip()
    if not title:
        return jsonify({'ok': False, 'error': 'Falta título real de la notificación.'}), 400
    create_notification(
        title=title,
        body=(data.get('body') or data.get('mensaje') or '').strip(),
        category=(data.get('category') or data.get('categoria') or 'sistema').strip(),
        level=(data.get('level') or data.get('nivel') or 'info').strip(),
        user_id=(data.get('user_id') or data.get('usuario') or None),
        source=(data.get('source') or 'api_v205').strip(),
        related_url=(data.get('related_url') or data.get('url') or None)
    )
    return jsonify({'ok': True, 'mensaje': 'Notificación real registrada.'})


@bp_smart_notifications_v205.route('/cliente/notificaciones')
@bp_smart_notifications_v205.route('/notifications-center')
@bp_smart_notifications_v205.route('/alertas')
def cliente_notifications_v205():
    return render_template('smart_notifications_v205.html', data=notification_payload(admin=False), admin=False)


@bp_smart_notifications_v205.route('/admin/notificaciones')
@bp_smart_notifications_v205.route('/admin/smart-notifications')
def admin_notifications_v205():
    return render_template('smart_notifications_v205.html', data=notification_payload(admin=True), admin=True)
