from flask import Blueprint, jsonify, render_template, session, request
from datetime import datetime
import os, sqlite3
from pathlib import Path

smart_live_v163_bp = Blueprint('smart_live_v163_bp', __name__)


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


def _recent(con, table, limit=8):
    if not con or not _table_exists(con, table):
        return []
    try:
        rows = con.execute(f"SELECT * FROM {table} ORDER BY rowid DESC LIMIT ?", (limit,)).fetchall()
    except Exception:
        return []
    items = []
    for r in rows:
        d = dict(r)
        title = d.get('title') or d.get('message') or d.get('event') or d.get('home_team') or d.get('pick') or 'Actividad real'
        subtitle = d.get('status') or d.get('result') or d.get('league') or d.get('kind') or table
        created = d.get('created_at') or d.get('updated_at') or d.get('date') or d.get('kickoff') or ''
        items.append({'title': str(title)[:120], 'subtitle': str(subtitle)[:80], 'created_at': str(created)[:40], 'source': table})
    return items


def _live_ecosystem(user_id=None):
    try:
        from live_ecosystem_v159.routes import build_live_ecosystem
        return build_live_ecosystem(user_id or _uid())
    except Exception as exc:
        return {'ok': False, 'counts': {}, 'ticker': [], 'hot_matches': [], 'recent_activity': [], 'shark_signals': [], 'error': str(exc)}


def build_smart_live_system(user_id=None):
    user_id = user_id or _uid()
    live = _live_ecosystem(user_id)
    con, path = _connect()
    try:
        users = _count(con, 'users')
        favorites = _count(con, 'favorites') + _count(con, 'user_favorites')
        picks = _count(con, 'picks')
        active_picks = _count(con, 'picks', "LOWER(COALESCE(status,'')) IN ('active','open','pending','')")
        alerts = _count(con, 'alerts_log') + _count(con, 'telegram_alerts')
        pending_alerts = _count(con, 'telegram_alerts', "LOWER(COALESCE(status,'')) IN ('pending','queued','retry')")
        activity = []
        for t in ('user_activity','client_activity','alerts_log','telegram_alerts','picks','fixtures'):
            activity.extend(_recent(con, t, 5))
        activity = activity[:12]
    finally:
        try:
            if con: con.close()
        except Exception:
            pass

    counts = live.get('counts') or {}
    live_count = int(counts.get('live') or 0)
    hot_count = int(counts.get('hot') or len(live.get('hot_matches') or []))
    feed_count = int(counts.get('feed') or len(live.get('recent_activity') or []))

    signals = []
    if live_count:
        signals.append({'level': 'live', 'title': 'Directo activo', 'text': f'{live_count} partido(s) reales en seguimiento live.', 'action': '/live-ecosystem'})
    if hot_count:
        signals.append({'level': 'hot', 'title': 'Partidos calientes', 'text': f'{hot_count} partido(s) preparados para seguimiento SHARK.', 'action': '/home-live-pro'})
    if active_picks:
        signals.append({'level': 'pick', 'title': 'Picks activos', 'text': f'{active_picks} pick(s) abiertos para tracking WIN/LOSS/VOID.', 'action': '/picks'})
    if pending_alerts:
        signals.append({'level': 'warning', 'title': 'Alertas pendientes', 'text': f'{pending_alerts} alerta(s) esperando envío/reintento.', 'action': '/telegram-live'})
    if favorites:
        signals.append({'level': 'favorite', 'title': 'Favoritos vivos', 'text': f'{favorites} favorito(s) guardados para personalizar la home.', 'action': '/favorites-pro'})
    if not signals:
        signals.append({'level': 'empty', 'title': 'Sistema inteligente preparado', 'text': 'No hay señales reales suficientes todavía. No se inventan partidos, scores ni picks.', 'action': '/fixtures/today-pro'})

    alert_engine = {
        'status': 'ACTIVE' if (live_count or active_picks or pending_alerts) else 'STANDBY',
        'targets': ['app', 'telegram', 'push_ready'],
        'rules': [
            'Priorizar favoritos activos',
            'Avisar picks abiertos en riesgo',
            'Destacar partidos live reales',
            'No enviar datos fake ni marcadores inventados',
        ],
        'pending_alerts': pending_alerts,
        'sent_or_logged_alerts': alerts,
    }

    smart_home = {
        'headline': 'SHARK Live preparado' if not live_count else 'SHARK Live en movimiento',
        'ticker': live.get('ticker') or [],
        'hot_matches': live.get('hot_matches') or [],
        'recent_activity': activity or live.get('recent_activity') or [],
        'empty_state': not bool(live_count or hot_count or feed_count or activity),
    }

    score = 50 + min(15, live_count * 5) + min(10, hot_count * 2) + (10 if favorites else 0) + (10 if active_picks else 0) + (5 if path else 0)
    score = max(0, min(100, score))

    return {
        'ok': True,
        'version': 'V163_AUTOMATIONS_AND_SMART_LIVE_SYSTEM',
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'database': {'detected': bool(path), 'path': path or 'NO_DETECTED'},
        'smart_score': score,
        'counts': {
            'users': users,
            'favorites': favorites,
            'picks_total': picks,
            'picks_active': active_picks,
            'live_matches': live_count,
            'hot_matches': hot_count,
            'alerts_logged': alerts,
            'pending_alerts': pending_alerts,
        },
        'signals': signals,
        'alert_engine': alert_engine,
        'smart_home': smart_home,
        'activity_tracking': activity or [],
        'policy': {
            'real_core_first': True,
            'no_fake_matches': True,
            'no_fake_scores': True,
            'no_fake_picks': True,
            'stripe_disabled': True,
            'push_ready_base': True,
        }
    }


@smart_live_v163_bp.route('/api/v163/smart-signals')
def api_smart_signals():
    data = build_smart_live_system(request.args.get('user_id') or _uid())
    return jsonify({'ok': True, 'version': data['version'], 'signals': data['signals'], 'counts': data['counts'], 'policy': data['policy']})


@smart_live_v163_bp.route('/api/v163/live-alerts')
def api_live_alerts():
    data = build_smart_live_system(request.args.get('user_id') or _uid())
    return jsonify({'ok': True, 'version': data['version'], 'alert_engine': data['alert_engine'], 'signals': data['signals']})


@smart_live_v163_bp.route('/api/v163/smart-home')
def api_smart_home():
    data = build_smart_live_system(request.args.get('user_id') or _uid())
    return jsonify({'ok': True, 'version': data['version'], 'smart_home': data['smart_home'], 'smart_score': data['smart_score']})


@smart_live_v163_bp.route('/api/v163/activity-tracking')
def api_activity_tracking():
    data = build_smart_live_system(request.args.get('user_id') or _uid())
    return jsonify({'ok': True, 'version': data['version'], 'activity': data['activity_tracking'], 'counts': data['counts']})


@smart_live_v163_bp.route('/smart-live')
@smart_live_v163_bp.route('/cliente/smart-live')
@smart_live_v163_bp.route('/smart-home')
@smart_live_v163_bp.route('/automations-live')
def page_smart_live():
    return render_template('smart_live_v163.html', data=build_smart_live_system(_uid()))
