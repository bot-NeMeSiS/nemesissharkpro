from flask import Blueprint, jsonify, render_template, request, redirect, session
from datetime import datetime
from pathlib import Path
import os, sqlite3, json, html

try:
    import requests
except Exception:
    requests = None

admin_telegram_control_v174_bp = Blueprint('admin_telegram_control_v174_bp', __name__)
VERSION = 'V174_TELEGRAM_ADMIN_CONTROL_TOWER'


def _is_admin():
    role = str(session.get('role') or session.get('user_role') or '').lower()
    user = str(session.get('username') or session.get('user') or session.get('admin') or '').lower()
    return bool(session.get('is_admin') or session.get('admin_logged_in') or role == 'admin' or user == 'admin')


def _db_path():
    for raw in [os.environ.get('DATABASE_PATH'), os.environ.get('DB_PATH'), '/data/app.db', '/data/database.db', 'app.db', 'database.db']:
        if raw and Path(raw).exists():
            return str(Path(raw))
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
    try:
        return bool(con and con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone())
    except Exception:
        return False


def _columns(con, table):
    try:
        return [r[1] for r in con.execute(f"PRAGMA table_info({table})").fetchall()]
    except Exception:
        return []


def _ensure_tables(con):
    if not con:
        return
    con.execute('''CREATE TABLE IF NOT EXISTS telegram_admin_handshake_v174 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id TEXT UNIQUE,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        is_admin INTEGER DEFAULT 1,
        source TEXT,
        last_text TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )''')
    con.execute('''CREATE TABLE IF NOT EXISTS telegram_admin_events_v174 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        event_type TEXT,
        status TEXT,
        target TEXT,
        detail TEXT,
        payload TEXT
    )''')
    con.execute('''CREATE TABLE IF NOT EXISTS telegram_delivery_log_v172 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        target_chat_id TEXT,
        target_plan TEXT,
        target_user_id TEXT,
        mode TEXT,
        status TEXT,
        message_preview TEXT,
        telegram_response TEXT,
        error TEXT
    )''')
    con.commit()


def _log(con, event_type, status, target='', detail='', payload=None):
    if not con:
        return
    try:
        con.execute('INSERT INTO telegram_admin_events_v174(created_at,event_type,status,target,detail,payload) VALUES(?,?,?,?,?,?)', (
            datetime.utcnow().isoformat(), event_type, status, str(target or ''), str(detail or '')[:500], json.dumps(payload or {}, ensure_ascii=False)[:4000]
        ))
        con.commit()
    except Exception:
        pass


def _token():
    return os.environ.get('TELEGRAM_BOT_TOKEN') or os.environ.get('BOT_TOKEN') or os.environ.get('TELEGRAM_TOKEN') or ''


def _admin_chat_id():
    return (os.environ.get('TELEGRAM_ADMIN_CHAT_ID') or os.environ.get('ADMIN_TELEGRAM_CHAT_ID') or '').strip()


def _channel_chat_id():
    return (os.environ.get('TELEGRAM_CHAT_ID') or os.environ.get('TELEGRAM_CHANNEL_ID') or os.environ.get('TELEGRAM_GROUP_ID') or '').strip()


def _tg_api(method, payload=None, timeout=15):
    if not requests:
        return {'ok': False, 'error': 'requests no disponible'}
    tok = _token()
    if not tok:
        return {'ok': False, 'error': 'Falta TELEGRAM_BOT_TOKEN'}
    try:
        r = requests.post(f'https://api.telegram.org/bot{tok}/{method}', json=payload or {}, timeout=timeout)
        try:
            return r.json()
        except Exception:
            return {'ok': False, 'status_code': r.status_code, 'text': r.text[:500]}
    except Exception as exc:
        return {'ok': False, 'error': str(exc)}


def _tg_get(method, params=None, timeout=15):
    if not requests:
        return {'ok': False, 'error': 'requests no disponible'}
    tok = _token()
    if not tok:
        return {'ok': False, 'error': 'Falta TELEGRAM_BOT_TOKEN'}
    try:
        r = requests.get(f'https://api.telegram.org/bot{tok}/{method}', params=params or {}, timeout=timeout)
        try:
            return r.json()
        except Exception:
            return {'ok': False, 'status_code': r.status_code, 'text': r.text[:500]}
    except Exception as exc:
        return {'ok': False, 'error': str(exc)}


def _send(chat_id, text):
    if not chat_id:
        return {'ok': False, 'error': 'Falta chat_id destino'}
    return _tg_api('sendMessage', {
        'chat_id': str(chat_id),
        'text': text,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True,
    })


def _save_admin_from_updates(con):
    updates = _tg_get('getUpdates', {'limit': 20, 'allowed_updates': json.dumps(['message'])})
    saved = []
    if not updates.get('ok'):
        return {'ok': False, 'updates': updates, 'saved': saved}
    _ensure_tables(con)
    for up in updates.get('result', []) or []:
        msg = up.get('message') or {}
        chat = msg.get('chat') or {}
        if chat.get('type') != 'private' or not chat.get('id'):
            continue
        chat_id = str(chat.get('id'))
        username = chat.get('username') or msg.get('from', {}).get('username') or ''
        first_name = chat.get('first_name') or msg.get('from', {}).get('first_name') or ''
        last_name = chat.get('last_name') or msg.get('from', {}).get('last_name') or ''
        text = msg.get('text') or ''
        now = datetime.utcnow().isoformat()
        if con:
            con.execute('''INSERT INTO telegram_admin_handshake_v174(chat_id,username,first_name,last_name,is_admin,source,last_text,created_at,updated_at)
                           VALUES(?,?,?,?,1,'getUpdates',?,?,?)
                           ON CONFLICT(chat_id) DO UPDATE SET username=excluded.username, first_name=excluded.first_name,
                           last_name=excluded.last_name, last_text=excluded.last_text, updated_at=excluded.updated_at''',
                        (chat_id, username, first_name, last_name, text[:250], now, now))
            con.commit()
        saved.append({'chat_id': chat_id, 'username': username, 'first_name': first_name, 'last_text': text})
    return {'ok': True, 'updates_count': len(updates.get('result', []) or []), 'saved': saved}


def _read_real_items(con, limit=6):
    if not con:
        return []
    tables = ['picks','value_picks','manual_picks','fixtures','real_fixtures','matches_cache','fixtures_cache','odds_cache']
    items = []
    for table in tables:
        if not _table_exists(con, table):
            continue
        cols = _columns(con, table)
        try:
            rows = con.execute(f"SELECT * FROM {table} ORDER BY rowid DESC LIMIT ?", (limit,)).fetchall()
        except Exception:
            continue
        for row in rows:
            d = dict(row)
            home = d.get('home_team') or d.get('home') or d.get('team_home') or d.get('local') or d.get('equipo_local')
            away = d.get('away_team') or d.get('away') or d.get('team_away') or d.get('visitor') or d.get('equipo_visitante')
            title = d.get('title') or d.get('name') or d.get('event') or d.get('match_name') or (f"{home} vs {away}" if home or away else '')
            if not title:
                continue
            market = d.get('market') or d.get('selection') or d.get('pick') or d.get('bet') or d.get('recommendation') or 'Mercado no especificado'
            odds = d.get('odds') or d.get('price') or d.get('quota') or d.get('cuota') or ''
            league = d.get('league') or d.get('competition') or d.get('sport_title') or 'Competición real'
            score = d.get('score') or d.get('shark_score') or d.get('confidence') or ''
            items.append({'title': str(title), 'market': str(market), 'odds': str(odds), 'league': str(league), 'score': str(score), 'id': d.get('id') or d.get('fixture_id') or d.get('match_id') or ''})
            if len(items) >= limit:
                return items
    return items


def _admin_message(items=None):
    lines = [
        '👑 <b>NeMeSiS SHARK PRO · ADMIN ELITE</b>',
        'Telegram admin conectado correctamente.',
        '',
        '🦈 Modo: <b>máximo/admin</b>',
        '📡 Fuente: datos reales/cacheados de la app',
    ]
    if items:
        lines += ['', '🔥 <b>Señales/partidos disponibles:</b>']
        for it in items[:5]:
            title = html.escape(it.get('title',''))
            market = html.escape(it.get('market',''))
            odds = html.escape(str(it.get('odds') or ''))
            league = html.escape(it.get('league',''))
            lines.append(f'• <b>{title}</b> · {league}\n  {market}' + (f' · cuota {odds}' if odds else ''))
    else:
        lines += ['', '⚠️ No hay picks/partidos reales disponibles ahora mismo. No se inventa contenido.']
    lines += ['', '✅ Si recibes esto, el delivery admin privado funciona.']
    return '\n'.join(lines)


def _summary(con):
    _ensure_tables(con)
    admin_env = _admin_chat_id()
    channel_env = _channel_chat_id()
    token_ok = bool(_token())
    getme = _tg_get('getMe') if token_ok else {'ok': False, 'error': 'Sin token'}
    saved_probe = _save_admin_from_updates(con)
    saved_admins = []
    if con and _table_exists(con, 'telegram_admin_handshake_v174'):
        try:
            saved_admins = [dict(r) for r in con.execute('SELECT * FROM telegram_admin_handshake_v174 ORDER BY updated_at DESC LIMIT 10').fetchall()]
        except Exception:
            saved_admins = []
    last_events = []
    if con and _table_exists(con, 'telegram_admin_events_v174'):
        try:
            last_events = [dict(r) for r in con.execute('SELECT * FROM telegram_admin_events_v174 ORDER BY id DESC LIMIT 12').fetchall()]
        except Exception:
            last_events = []
    health = 0
    health += 25 if token_ok else 0
    health += 20 if getme.get('ok') else 0
    health += 20 if admin_env else 0
    health += 15 if channel_env else 0
    health += 20 if saved_admins else 0
    return {
        'version': VERSION,
        'db_path': _db_path() or 'No detectada',
        'health': health,
        'token_configured': token_ok,
        'bot': getme.get('result') if getme.get('ok') else {},
        'getme_ok': bool(getme.get('ok')),
        'getme_error': getme.get('description') or getme.get('error') or '',
        'admin_chat_id': admin_env,
        'channel_chat_id': channel_env,
        'admin_chat_hint': 'Correcto: chat privado SIN -100' if admin_env and not admin_env.startswith('-100') else 'Añade TELEGRAM_ADMIN_CHAT_ID=793831597',
        'channel_hint': 'Correcto si empieza por -100 para canal/grupo' if channel_env.startswith('-100') else 'El canal/grupo normalmente empieza por -100',
        'saved_probe': saved_probe,
        'saved_admins': saved_admins,
        'events': last_events,
        'real_items': _read_real_items(con, 6),
        'env_recommended': [
            {'name': 'TELEGRAM_BOT_TOKEN', 'value': 'configurado' if token_ok else 'FALTA'},
            {'name': 'TELEGRAM_ADMIN_CHAT_ID', 'value': admin_env or '793831597'},
            {'name': 'TELEGRAM_CHAT_ID', 'value': channel_env or '-100xxxxxxxxxx'},
        ]
    }


@admin_telegram_control_v174_bp.route('/admin/telegram-control')
@admin_telegram_control_v174_bp.route('/admin/telegram-admin-control')
@admin_telegram_control_v174_bp.route('/admin/control-tower')
def admin_telegram_control():
    if not _is_admin():
        return redirect('/admin-login')
    con, _ = _connect()
    data = _summary(con)
    if con:
        con.close()
    return render_template('admin_telegram_control_v174.html', data=data)


@admin_telegram_control_v174_bp.route('/api/v174/telegram-admin/status')
def api_status():
    con, _ = _connect()
    data = _summary(con)
    if con:
        con.close()
    return jsonify(data)


@admin_telegram_control_v174_bp.route('/api/v174/telegram-admin/handshake', methods=['GET','POST'])
def api_handshake():
    con, _ = _connect()
    if con:
        _ensure_tables(con)
    res = _save_admin_from_updates(con)
    if con:
        _log(con, 'handshake', 'ok' if res.get('ok') else 'error', detail='Lectura getUpdates', payload=res)
        con.close()
    return jsonify(res)


@admin_telegram_control_v174_bp.route('/api/v174/telegram-admin/test-admin', methods=['POST','GET'])
def api_test_admin():
    con, _ = _connect()
    if con:
        _ensure_tables(con)
    chat_id = request.values.get('chat_id') or _admin_chat_id()
    if not chat_id and con and _table_exists(con, 'telegram_admin_handshake_v174'):
        row = con.execute('SELECT chat_id FROM telegram_admin_handshake_v174 ORDER BY updated_at DESC LIMIT 1').fetchone()
        chat_id = row['chat_id'] if row else ''
    items = _read_real_items(con, 5)
    res = _send(chat_id, _admin_message(items))
    if con:
        _log(con, 'test_admin_delivery', 'ok' if res.get('ok') else 'error', target=chat_id, detail=res.get('description') or res.get('error') or 'sendMessage', payload=res)
        con.close()
    return jsonify({'target_chat_id': chat_id, 'sent': bool(res.get('ok')), 'telegram_response': res})


@admin_telegram_control_v174_bp.route('/api/v174/telegram-admin/test-channel', methods=['POST','GET'])
def api_test_channel():
    con, _ = _connect()
    chat_id = request.values.get('chat_id') or _channel_chat_id()
    res = _send(chat_id, '📣 <b>NeMeSiS SHARK PRO</b>\nPrueba real de canal/grupo correcta. Si recibes esto, TELEGRAM_CHAT_ID funciona.')
    if con:
        _ensure_tables(con)
        _log(con, 'test_channel_delivery', 'ok' if res.get('ok') else 'error', target=chat_id, detail=res.get('description') or res.get('error') or 'sendMessage', payload=res)
        con.close()
    return jsonify({'target_chat_id': chat_id, 'sent': bool(res.get('ok')), 'telegram_response': res})


@admin_telegram_control_v174_bp.route('/api/v174/admin/overview')
def api_admin_overview():
    con, path = _connect()
    data = _summary(con)
    kpis = []
    if con:
        for table, label in [('users','Usuarios'),('picks','Picks'),('fixtures','Fixtures'),('telegram_delivery_log_v172','Logs Telegram'),('telegram_admin_events_v174','Eventos admin')]:
            if _table_exists(con, table):
                try:
                    value = con.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
                except Exception:
                    value = 0
            else:
                value = 0
            kpis.append({'label': label, 'value': value})
        con.close()
    return jsonify({'version': VERSION, 'database': path, 'telegram_health': data['health'], 'kpis': kpis, 'quick_links': ['/admin/telegram-control','/admin/business','/admin/telegram-auto-delivery','/admin/push-center']})
