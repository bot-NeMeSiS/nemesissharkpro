from flask import Blueprint, jsonify, render_template, session, request
from datetime import datetime
from pathlib import Path
import os, sqlite3, json

ux_polish_v165_bp = Blueprint('ux_polish_v165_bp', __name__)


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


def _count(con, table, where='1=1'):
    if not con or not _table_exists(con, table):
        return 0
    try:
        return int(con.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}").fetchone()[0] or 0)
    except Exception:
        return 0


def _safe_call(fn, fallback):
    try:
        return fn()
    except Exception as exc:
        data = dict(fallback)
        data['error'] = str(exc)
        return data


def _live_data(user_id):
    return _safe_call(lambda: __import__('live_ecosystem_v159.routes', fromlist=['build_live_ecosystem']).build_live_ecosystem(user_id), {
        'counts': {}, 'ticker': [], 'hot_matches': [], 'shark_signals': [], 'empty_state': True
    })


def _push_data(user_id):
    return _safe_call(lambda: __import__('push_notifications_v164.routes', fromlist=['build_push_foundation']).build_push_foundation(user_id), {
        'counts': {}, 'readiness': {}, 'recent_queue': [], 'suggested_alerts': []
    })


def build_v165_app_status(user_id=None):
    user_id = user_id or _uid()
    live = _live_data(user_id)
    push = _push_data(user_id)
    con, path = _connect()
    try:
        users = _count(con, 'users') + _count(con, 'usuarios')
        favs = _count(con, 'favorites') + _count(con, 'user_favorites') + _count(con, 'client_favorites')
        picks = _count(con, 'picks') + _count(con, 'closing_picks')
        alerts = _count(con, 'notification_queue')
    finally:
        try:
            if con: con.close()
        except Exception:
            pass
    health_score = 72
    if path: health_score += 8
    if Path('service-worker.js').exists(): health_score += 6
    if Path('static/manifest.json').exists(): health_score += 6
    if live.get('counts', {}).get('live', 0) or live.get('counts', {}).get('upcoming', 0): health_score += 4
    if push.get('readiness', {}).get('pwa_ready'): health_score += 4
    health_score = min(100, health_score)
    return {
        'ok': True,
        'version': 'V165_FINAL_UX_POLISH_AND_APP_FLOW',
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'user_id': user_id,
        'health_score': health_score,
        'database': {'detected': bool(path), 'path': path or 'NO_DETECTED'},
        'counts': {
            'users_detected': users,
            'favorites_detected': favs,
            'picks_detected': picks,
            'notifications_detected': alerts,
            'live_items': live.get('counts', {}).get('live', 0),
            'hot_matches': live.get('counts', {}).get('hot', 0),
            'push_pending': push.get('counts', {}).get('queue_pending', 0),
        },
        'ux': {
            'mobile_bottom_nav': True,
            'premium_skeletons': True,
            'soft_transitions': True,
            'empty_states_real_only': True,
            'pwa_install_flow_visible': True,
            'login_logout_flow_reinforced': True,
            'stripe_disabled': True,
        },
        'live_preview': {
            'ticker': (live.get('ticker') or [])[:6],
            'signals': (live.get('shark_signals') or [])[:6],
            'empty_state': live.get('empty_state', True),
        },
        'notifications_preview': {
            'readiness': push.get('readiness') or {},
            'recent_queue': (push.get('recent_queue') or [])[:6],
        },
        'policy': {'no_fake_matches': True, 'no_fake_scores': True, 'no_fake_picks': True, 'real_core_first': True}
    }


def build_v165_navigation(user_id=None):
    data = build_v165_app_status(user_id)
    logged = bool(session.get('user_id') or session.get('username') or session.get('user'))
    return {
        'ok': True,
        'version': data['version'],
        'logged_in': logged,
        'primary': '/cliente/pro' if logged else '/cliente-login',
        'logout': '/logout',
        'items': [
            {'label': 'Inicio', 'href': '/', 'icon': '⌂', 'active': False},
            {'label': 'Live', 'href': '/home-live-pro', 'icon': '●', 'active': False},
            {'label': 'Partidos', 'href': '/fixtures/today-pro', 'icon': '⚽', 'active': False},
            {'label': 'SHARK', 'href': '/shark-ai', 'icon': '🦈', 'active': False},
            {'label': 'Cuenta', 'href': '/cuenta', 'icon': '👤', 'active': False},
        ],
        'quick_actions': [
            {'label': 'Panel cliente', 'href': '/cliente/pro'},
            {'label': 'Match Center', 'href': '/match-center-pro'},
            {'label': 'Notificaciones', 'href': '/cliente/notificaciones'},
            {'label': 'Smart Live', 'href': '/smart-live'},
        ],
        'health_score': data['health_score']
    }


@ux_polish_v165_bp.route('/api/v165/app-status')
def api_v165_app_status():
    return jsonify(build_v165_app_status(request.args.get('user_id') or _uid()))


@ux_polish_v165_bp.route('/api/v165/ui-health')
def api_v165_ui_health():
    data = build_v165_app_status(request.args.get('user_id') or _uid())
    return jsonify({'ok': True, 'version': data['version'], 'health_score': data['health_score'], 'ux': data['ux'], 'policy': data['policy']})


@ux_polish_v165_bp.route('/api/v165/navigation-state')
def api_v165_navigation_state():
    return jsonify(build_v165_navigation(request.args.get('user_id') or _uid()))


@ux_polish_v165_bp.route('/app-flow')
@ux_polish_v165_bp.route('/cliente/app-flow')
@ux_polish_v165_bp.route('/cliente/ux-pro')
@ux_polish_v165_bp.route('/admin/ux-health')
def page_v165_app_flow():
    data = build_v165_app_status(_uid())
    nav = build_v165_navigation(_uid())
    return render_template('ux_polish_v165.html', data=data, nav=nav)
