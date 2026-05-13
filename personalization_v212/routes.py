import os
import sqlite3
from datetime import datetime
from pathlib import Path
from flask import Blueprint, jsonify, render_template, request, session, redirect

bp_personalization_v212 = Blueprint('personalization_v212', __name__)


def _db_path():
    raw = os.environ.get('DATABASE_PATH') or os.environ.get('DB_PATH') or '/data/database.db'
    if str(raw).startswith('sqlite:///'):
        raw = str(raw).replace('sqlite:///', '', 1)
    return raw


def _connect():
    path = _db_path()
    parent = Path(path).parent
    try:
        parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    con = sqlite3.connect(path, timeout=6)
    con.row_factory = sqlite3.Row
    return con


def _now():
    return datetime.utcnow().isoformat(timespec='seconds') + 'Z'


def _user():
    u = session.get('user') or {}
    return {
        'id': u.get('id') or 0,
        'username': u.get('username') or 'Usuario',
        'plan': (u.get('plan') or 'FREE').upper(),
        'role': u.get('role') or 'cliente'
    }


def _safe_table_exists(cur, name):
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None


def init_db():
    con = _connect(); cur = con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS user_preferences_v212 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        pref_type TEXT NOT NULL,
        pref_value TEXT NOT NULL,
        weight INTEGER DEFAULT 1,
        source TEXT DEFAULT 'usuario',
        created_at TEXT,
        updated_at TEXT,
        UNIQUE(user_id, pref_type, pref_value)
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS user_activity_v212 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        username TEXT,
        activity_type TEXT NOT NULL,
        entity_type TEXT,
        entity_id TEXT,
        label TEXT,
        metadata TEXT,
        created_at TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS personalization_cache_v212 (
        user_id INTEGER PRIMARY KEY,
        payload TEXT,
        created_at TEXT,
        updated_at TEXT
    )''')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_v212_preferences_user ON user_preferences_v212(user_id, pref_type)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_v212_activity_user ON user_activity_v212(user_id, created_at)')
    con.commit(); con.close()


def _preferences(user_id):
    init_db()
    con = _connect(); cur = con.cursor()
    cur.execute('SELECT pref_type, pref_value, weight, source, updated_at FROM user_preferences_v212 WHERE user_id=? ORDER BY pref_type, weight DESC, updated_at DESC', (user_id,))
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    grouped = {'equipo': [], 'liga': [], 'mercado': [], 'pick': []}
    for r in rows:
        grouped.setdefault(r['pref_type'], []).append(r)
    return grouped


def _recent_activity(user_id, limit=12):
    init_db()
    con = _connect(); cur = con.cursor()
    cur.execute('SELECT activity_type, entity_type, entity_id, label, created_at FROM user_activity_v212 WHERE user_id=? ORDER BY id DESC LIMIT ?', (user_id, limit))
    data = [dict(r) for r in cur.fetchall()]
    con.close()
    return data


def _read_candidates(limit=18):
    """Lee datos reales existentes sin inventar partidos. Si no hay tablas, devuelve vacío."""
    con = _connect(); cur = con.cursor(); items = []
    try:
        if _safe_table_exists(cur, 'picks'):
            cols = [r['name'] for r in cur.execute('PRAGMA table_info(picks)').fetchall()]
            # Selección tolerante a nombres de columnas del proyecto.
            sel = []
            for c in ['id','match_name','home_team','away_team','league','competition','market','pick','selection','odds','confidence','created_at','event_time']:
                if c in cols:
                    sel.append(c)
            if sel:
                cur.execute(f"SELECT {','.join(sel)} FROM picks ORDER BY COALESCE(created_at,event_time,'') DESC LIMIT ?", (limit,))
                for row in cur.fetchall():
                    d = dict(row)
                    label = d.get('match_name') or ' vs '.join([x for x in [d.get('home_team'), d.get('away_team')] if x]) or d.get('pick') or 'Pick real'
                    items.append({
                        'tipo': 'pick',
                        'titulo': label,
                        'subtitulo': d.get('league') or d.get('competition') or 'Competición no indicada',
                        'detalle': d.get('pick') or d.get('selection') or d.get('market') or 'Mercado real disponible',
                        'score': d.get('confidence') or '',
                        'url': '/picks'
                    })
        if _safe_table_exists(cur, 'real_fixtures_v146'):
            cols = [r['name'] for r in cur.execute('PRAGMA table_info(real_fixtures_v146)').fetchall()]
            sel = [c for c in ['id','home_team','away_team','league','competition','status','kickoff','start_time'] if c in cols]
            if sel:
                cur.execute(f"SELECT {','.join(sel)} FROM real_fixtures_v146 ORDER BY COALESCE(kickoff,start_time,'') ASC LIMIT ?", (limit,))
                for row in cur.fetchall():
                    d = dict(row)
                    title = ' vs '.join([x for x in [d.get('home_team'), d.get('away_team')] if x]) or 'Partido real'
                    items.append({
                        'tipo': 'partido',
                        'titulo': title,
                        'subtitulo': d.get('league') or d.get('competition') or 'Competición no indicada',
                        'detalle': d.get('status') or 'Estado pendiente del proveedor',
                        'score': '',
                        'url': '/home-live-real'
                    })
    except Exception:
        pass
    finally:
        con.close()
    return items[:limit]


def _personal_feed(user_id):
    prefs = _preferences(user_id)
    candidates = _read_candidates(24)
    needles = []
    for k in ['equipo','liga','mercado']:
        needles += [str(x.get('pref_value','')).lower() for x in prefs.get(k, []) if x.get('pref_value')]
    ranked = []
    for item in candidates:
        blob = ' '.join(str(item.get(k,'')) for k in ['titulo','subtitulo','detalle']).lower()
        score = 10
        for n in needles:
            if n and n in blob:
                score += 40
        if item['tipo'] == 'pick':
            score += 8
        ranked.append((score, item))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return [dict(i, relevancia=s) for s, i in ranked[:12]]


def _summary():
    user = _user(); uid = int(user['id'] or 0)
    prefs = _preferences(uid) if uid else {'equipo': [], 'liga': [], 'mercado': [], 'pick': []}
    activity = _recent_activity(uid) if uid else []
    feed = _personal_feed(uid) if uid else []
    return {
        'version': 'V212',
        'nombre': 'User Personalization Engine PRO',
        'estado': 'activo',
        'usuario': user,
        'preferencias': prefs,
        'actividad': activity,
        'feed': feed,
        'metricas': {
            'preferencias': sum(len(v) for v in prefs.values()),
            'actividad_reciente': len(activity),
            'items_feed': len(feed)
        },
        'fecha': _now()
    }


@bp_personalization_v212.route('/api/v212/personalization', methods=['GET', 'POST'])
def api_personalization_v212():
    user = _user(); uid = int(user['id'] or 0)
    if not uid:
        return jsonify({'ok': False, 'error': 'Sesión de cliente no encontrada.'}), 401
    init_db()
    if request.method == 'POST':
        data = request.get_json(silent=True) or request.form
        pref_type = (data.get('pref_type') or data.get('tipo') or '').strip().lower()
        pref_value = (data.get('pref_value') or data.get('valor') or '').strip()
        if pref_type not in ['equipo','liga','mercado','pick'] or not pref_value:
            return jsonify({'ok': False, 'error': 'Preferencia no válida.'}), 400
        con = _connect(); cur = con.cursor()
        cur.execute('''INSERT INTO user_preferences_v212(user_id,pref_type,pref_value,weight,source,created_at,updated_at)
                       VALUES(?,?,?,?,?,?,?)
                       ON CONFLICT(user_id,pref_type,pref_value) DO UPDATE SET weight=weight+1, updated_at=excluded.updated_at''',
                    (uid, pref_type, pref_value, 1, 'usuario', _now(), _now()))
        cur.execute('INSERT INTO user_activity_v212(user_id,username,activity_type,entity_type,entity_id,label,metadata,created_at) VALUES(?,?,?,?,?,?,?,?)',
                    (uid, user['username'], 'preferencia_guardada', pref_type, pref_value, pref_value, '', _now()))
        con.commit(); con.close()
        return jsonify({'ok': True, 'message': 'Preferencia guardada.', 'data': _summary()})
    return jsonify({'ok': True, 'data': _summary()})


@bp_personalization_v212.route('/api/v212/activity', methods=['POST'])
def api_activity_v212():
    user = _user(); uid = int(user['id'] or 0)
    if not uid:
        return jsonify({'ok': False, 'error': 'Sesión no encontrada.'}), 401
    data = request.get_json(silent=True) or request.form
    init_db()
    con = _connect(); cur = con.cursor()
    cur.execute('INSERT INTO user_activity_v212(user_id,username,activity_type,entity_type,entity_id,label,metadata,created_at) VALUES(?,?,?,?,?,?,?,?)',
                (uid, user['username'], (data.get('activity_type') or 'vista').strip(), (data.get('entity_type') or '').strip(), str(data.get('entity_id') or '').strip(), (data.get('label') or '').strip(), str(data.get('metadata') or ''), _now()))
    con.commit(); con.close()
    return jsonify({'ok': True, 'message': 'Actividad registrada.'})


@bp_personalization_v212.route('/cliente/personalizacion')
def cliente_personalizacion_v212():
    if not session.get('user'):
        return redirect('/cliente-login')
    return render_template('personalizacion_v212.html', data=_summary())


@bp_personalization_v212.route('/cliente/mi-feed')
def cliente_mi_feed_v212():
    if not session.get('user'):
        return redirect('/cliente-login')
    data = _summary()
    return render_template('mi_feed_v212.html', data=data)


@bp_personalization_v212.route('/cliente/actividad')
def cliente_actividad_v212():
    if not session.get('user'):
        return redirect('/cliente-login')
    data = _summary()
    return render_template('actividad_v212.html', data=data)


@bp_personalization_v212.route('/admin/personalizacion')
def admin_personalizacion_v212():
    init_db()
    con = _connect(); cur = con.cursor()
    stats = {'usuarios_con_preferencias': 0, 'preferencias': 0, 'actividad': 0}
    try:
        cur.execute('SELECT COUNT(DISTINCT user_id) AS n FROM user_preferences_v212'); stats['usuarios_con_preferencias'] = cur.fetchone()['n']
        cur.execute('SELECT COUNT(*) AS n FROM user_preferences_v212'); stats['preferencias'] = cur.fetchone()['n']
        cur.execute('SELECT COUNT(*) AS n FROM user_activity_v212'); stats['actividad'] = cur.fetchone()['n']
    except Exception:
        pass
    con.close()
    return render_template('admin_personalizacion_v212.html', stats=stats, data=_summary())
