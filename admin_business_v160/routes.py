from flask import Blueprint, jsonify, render_template, session, redirect
from datetime import datetime
import os, sqlite3
from pathlib import Path

admin_business_v160_bp = Blueprint('admin_business_v160_bp', __name__)


def _is_admin_session():
    try:
        role = str(session.get('role') or session.get('user_role') or '').lower()
        user = session.get('user') or session.get('username') or session.get('admin')
        return bool(session.get('is_admin') or session.get('admin_logged_in') or role == 'admin' or str(user).lower() == 'admin')
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
    p = _db_path()
    if not p:
        return None, None
    try:
        con = sqlite3.connect(p)
        con.row_factory = sqlite3.Row
        return con, p
    except Exception:
        return None, p


def _safe_count(con, names):
    if not con:
        return None
    cur = con.cursor()
    for table in names:
        try:
            cur.execute(f'SELECT COUNT(*) AS n FROM {table}')
            return int(cur.fetchone()['n'])
        except Exception:
            continue
    return None


def _safe_recent(con, names, limit=8):
    if not con:
        return []
    cur = con.cursor()
    for table in names:
        try:
            cur.execute(f'SELECT * FROM {table} ORDER BY rowid DESC LIMIT ?', (limit,))
            rows = cur.fetchall()
            out = []
            for r in rows:
                d = dict(r)
                title = d.get('title') or d.get('name') or d.get('event') or d.get('match_name') or d.get('home_team') or d.get('username') or 'Registro real'
                meta = d.get('created_at') or d.get('updated_at') or d.get('date') or d.get('kickoff') or ''
                out.append({'title': str(title), 'meta': str(meta), 'table': table})
            return out
        except Exception:
            continue
    return []


def _env(name):
    value = os.environ.get(name)
    return {'name': name, 'configured': bool(value), 'status': 'OK' if value else 'MISSING'}


def build_admin_business_center():
    con, path = _connect()
    try:
        users = _safe_count(con, ['users', 'clientes', 'clients', 'user'])
        picks = _safe_count(con, ['picks', 'bets', 'apuestas'])
        fixtures = _safe_count(con, ['fixtures', 'matches', 'events', 'real_fixtures'])
        favorites = _safe_count(con, ['favorites', 'user_favorites', 'favoritos'])
        recent_users = _safe_recent(con, ['users', 'clientes', 'clients'], 6)
        recent_fixtures = _safe_recent(con, ['fixtures', 'matches', 'events', 'real_fixtures'], 6)
        recent_picks = _safe_recent(con, ['picks', 'bets', 'apuestas'], 6)
    finally:
        try:
            if con: con.close()
        except Exception:
            pass

    envs = [_env('THE_ODDS_API_KEY'), _env('TELEGRAM_BOT_TOKEN'), _env('OPENAI_API_KEY'), _env('DATABASE_PATH'), _env('DB_PATH')]
    configured = sum(1 for e in envs if e['configured'])
    warnings = []
    if not path:
        warnings.append('No se detecta base de datos persistente. Revisa Render Disk y DATABASE_PATH/DB_PATH.')
    if not any(e['name']=='THE_ODDS_API_KEY' and e['configured'] for e in envs):
        warnings.append('The Odds API no está configurada: los fixtures/picks reales dependerán de caché o quedarán vacíos.')
    if not any(e['name']=='TELEGRAM_BOT_TOKEN' and e['configured'] for e in envs):
        warnings.append('Telegram no está configurado: alertas premium desactivadas.')

    health = 60 + (10 if path else 0) + configured * 4
    if users not in (None, 0): health += 4
    if fixtures not in (None, 0): health += 4
    if picks not in (None, 0): health += 4
    if not warnings: health += 8
    health = max(0, min(100, health))

    return {
        'ok': True,
        'version': 'V160_ADMIN_BUSINESS_CENTER_PRO',
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'health_score': health,
        'database': {'detected': bool(path), 'path': path or 'NO_DETECTED'},
        'kpis': [
            {'label': 'Usuarios', 'value': users if users is not None else '—', 'hint': 'lectura real si tabla disponible'},
            {'label': 'Fixtures', 'value': fixtures if fixtures is not None else '—', 'hint': 'partidos reales/cache'},
            {'label': 'Picks', 'value': picks if picks is not None else '—', 'hint': 'picks/operaciones'},
            {'label': 'Favoritos', 'value': favorites if favorites is not None else '—', 'hint': 'seguimiento cliente'},
        ],
        'env': envs,
        'warnings': warnings,
        'recent': {'users': recent_users, 'fixtures': recent_fixtures, 'picks': recent_picks},
        'quick_links': [
            {'label': 'Fixtures Sync', 'href': '/admin/fixtures-sync'},
            {'label': 'Home Feed', 'href': '/admin/home-feed'},
            {'label': 'App Audit', 'href': '/admin/app-audit'},
            {'label': 'Telegram', 'href': '/admin/telegram'},
            {'label': 'Closing Picks', 'href': '/admin/results'},
            {'label': 'Live Ecosystem', 'href': '/live-ecosystem'},
            {'label': 'Cliente PRO', 'href': '/cliente/pro'},
            {'label': 'API V160', 'href': '/api/v160/admin/business-center'},
        ],
        'policy': {'no_fake_matches': True, 'no_fake_picks': True, 'no_fake_scores': True, 'stripe_disabled': True}
    }


@admin_business_v160_bp.route('/api/v160/admin/business-center')
def api_admin_business_center():
    return jsonify(build_admin_business_center())


@admin_business_v160_bp.route('/admin/business')
@admin_business_v160_bp.route('/admin/business-center')
@admin_business_v160_bp.route('/admin/pro-center')
def page_admin_business_center():
    if not _is_admin_session():
        return redirect('/admin-login')
    return render_template('admin_business_v160.html', data=build_admin_business_center())
