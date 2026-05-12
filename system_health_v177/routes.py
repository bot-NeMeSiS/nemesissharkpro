from flask import Blueprint, jsonify, render_template, request
from datetime import datetime
from pathlib import Path
import os, sqlite3, time, json

system_health_v177_bp = Blueprint('system_health_v177_bp', __name__)

START_TS = time.time()
_RATE_BUCKET = {}


def _db_candidates():
    return [os.environ.get('DATABASE_PATH'), os.environ.get('DB_PATH'), '/data/app.db', '/data/database.db', 'app.db', 'database.db']


def _db_path():
    for p in _db_candidates():
        if p and Path(p).exists():
            return str(Path(p))
    return None


def _connect():
    p = _db_path()
    if not p:
        return None, None
    try:
        con = sqlite3.connect(p, timeout=4)
        con.row_factory = sqlite3.Row
        return con, p
    except Exception:
        return None, p


def _table_exists(con, name):
    if not con:
        return False
    try:
        return bool(con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone())
    except Exception:
        return False


def _count(con, table):
    if not _table_exists(con, table):
        return None
    try:
        return int(con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    except Exception:
        return None


def _sample_errors(con):
    rows = []
    for table in ('system_logs','telegram_logs','telegram_delivery_logs','alerts_log','error_logs'):
        if not _table_exists(con, table):
            continue
        try:
            cols = [r[1] for r in con.execute(f"PRAGMA table_info({table})").fetchall()]
            order = 'rowid DESC'
            for c in ('created_at','timestamp','date'):
                if c in cols:
                    order = f"COALESCE({c}, '') DESC"
                    break
            for r in con.execute(f"SELECT * FROM {table} ORDER BY {order} LIMIT 5").fetchall():
                d = dict(r)
                rows.append({
                    'source': table,
                    'level': str(d.get('level') or d.get('status') or d.get('type') or 'info'),
                    'message': str(d.get('message') or d.get('error') or d.get('text') or d)[:260],
                    'created_at': str(d.get('created_at') or d.get('timestamp') or d.get('date') or ''),
                })
        except Exception:
            continue
    return rows[:12]


def _safe_env(name):
    value = os.environ.get(name)
    if not value:
        return {'name': name, 'present': False, 'preview': ''}
    return {'name': name, 'present': True, 'preview': value[:4] + '…' + value[-4:] if len(value) > 10 else '***'}


def build_system_health():
    con, db = _connect()
    tables = {}
    errors = []
    db_size = 0
    try:
        if db and Path(db).exists():
            db_size = Path(db).stat().st_size
        if con:
            for table in ('users','picks','fixtures','matches','telegram_users','telegram_delivery_logs','push_subscriptions','notification_queue'):
                tables[table] = _count(con, table)
            errors = _sample_errors(con)
    finally:
        try:
            if con: con.close()
        except Exception:
            pass

    checks = [
        {'key': 'database', 'label': 'SQLite / persistencia', 'ok': bool(db), 'detail': db or 'No encontrada'},
        {'key': 'telegram_token', 'label': 'Telegram token', 'ok': bool(os.environ.get('TELEGRAM_BOT_TOKEN') or os.environ.get('BOT_TOKEN')), 'detail': 'Configurado' if (os.environ.get('TELEGRAM_BOT_TOKEN') or os.environ.get('BOT_TOKEN')) else 'Pendiente'},
        {'key': 'telegram_admin', 'label': 'Admin chat privado', 'ok': bool(os.environ.get('TELEGRAM_ADMIN_CHAT_ID')), 'detail': os.environ.get('TELEGRAM_ADMIN_CHAT_ID') or 'Pendiente'},
        {'key': 'telegram_channel', 'label': 'Canal/grupo Telegram', 'ok': bool(os.environ.get('TELEGRAM_CHAT_ID')), 'detail': os.environ.get('TELEGRAM_CHAT_ID') or 'Pendiente'},
        {'key': 'the_odds_api', 'label': 'The Odds API', 'ok': bool(os.environ.get('THE_ODDS_API_KEY') or os.environ.get('ODDS_API_KEY')), 'detail': 'Configurada' if (os.environ.get('THE_ODDS_API_KEY') or os.environ.get('ODDS_API_KEY')) else 'Pendiente'},
        {'key': 'secret_key', 'label': 'SECRET_KEY', 'ok': bool(os.environ.get('SECRET_KEY')), 'detail': 'Configurada' if os.environ.get('SECRET_KEY') else 'Usando fallback'},
    ]
    ok_count = sum(1 for c in checks if c['ok'])
    score = int((ok_count / max(1, len(checks))) * 100)
    if errors:
        score = max(35, score - min(20, len(errors) * 2))
    return {
        'version': 'V177',
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'uptime_seconds': int(time.time() - START_TS),
        'score': score,
        'status': 'operativo' if score >= 70 else 'revisar',
        'database': {'path': db, 'size_bytes': db_size, 'size_mb': round(db_size / 1024 / 1024, 2)},
        'tables': tables,
        'checks': checks,
        'env': [_safe_env(x) for x in ('TELEGRAM_BOT_TOKEN','TELEGRAM_ADMIN_CHAT_ID','TELEGRAM_CHAT_ID','THE_ODDS_API_KEY','SECRET_KEY')],
        'recent_errors': errors,
        'performance': {
            'cache_mode': 'SQLite + memoria ligera',
            'live_polling': 'optimizado/base',
            'rate_limit_base': 'activo en endpoints V177',
            'recommendation': 'mantener fixtures cacheados y evitar refrescos live agresivos',
        },
        'security': {
            'admin_routes': 'revisión recomendada con sesión/rol admin',
            'csrf': 'pendiente de endurecimiento completo si hay formularios críticos',
            'cookies': 'revisar Secure/HttpOnly/SameSite en producción',
            'rate_limits': 'base preparada',
        }
    }


def _rate_limited(key, limit=60, window=60):
    now = time.time()
    bucket = _RATE_BUCKET.setdefault(key, [])
    bucket[:] = [t for t in bucket if now - t < window]
    if len(bucket) >= limit:
        return True
    bucket.append(now)
    return False


@system_health_v177_bp.before_app_request
def v177_light_rate_limit():
    path = request.path or ''
    if not path.startswith('/api/v177/'):
        return None
    ip = request.headers.get('X-Forwarded-For', request.remote_addr or 'local').split(',')[0].strip()
    if _rate_limited(f'{ip}:{path}', limit=90, window=60):
        return jsonify({'ok': False, 'error': 'rate_limited', 'message': 'Demasiadas peticiones. Espera unos segundos.'}), 429
    return None


@system_health_v177_bp.route('/admin/system-health')
@system_health_v177_bp.route('/admin/performance')
@system_health_v177_bp.route('/admin/security')
def system_health_page():
    data = build_system_health()
    return render_template('v177/system_health.html', data=data)


@system_health_v177_bp.route('/api/v177/system-health')
def api_system_health():
    return jsonify({'ok': True, 'data': build_system_health()})


@system_health_v177_bp.route('/api/v177/performance')
def api_performance():
    data = build_system_health()
    return jsonify({'ok': True, 'performance': data['performance'], 'database': data['database'], 'tables': data['tables']})


@system_health_v177_bp.route('/api/v177/security')
def api_security():
    data = build_system_health()
    return jsonify({'ok': True, 'security': data['security'], 'checks': data['checks']})
