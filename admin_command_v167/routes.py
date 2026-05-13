from flask import Blueprint, jsonify, render_template, session, redirect
from datetime import datetime, timedelta
from pathlib import Path
import os, sqlite3, platform

admin_command_v167_bp = Blueprint('admin_command_v167_bp', __name__)


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


def _tables(con):
    if not con:
        return []
    try:
        return [r['name'] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
    except Exception:
        return []


def _count(con, table_names):
    if not con:
        return None
    cur = con.cursor()
    for t in table_names:
        try:
            cur.execute(f"SELECT COUNT(*) AS n FROM {t}")
            return int(cur.fetchone()['n'])
        except Exception:
            continue
    return None


def _count_where(con, table_names, where_sql, params=()):
    if not con:
        return None
    cur = con.cursor()
    for t in table_names:
        try:
            cur.execute(f"SELECT COUNT(*) AS n FROM {t} WHERE {where_sql}", params)
            return int(cur.fetchone()['n'])
        except Exception:
            continue
    return None


def _recent(con, table_names, limit=7):
    if not con:
        return []
    cur = con.cursor()
    for t in table_names:
        try:
            rows = cur.execute(f"SELECT * FROM {t} ORDER BY rowid DESC LIMIT ?", (limit,)).fetchall()
            out = []
            for row in rows:
                d = dict(row)
                title = d.get('title') or d.get('name') or d.get('username') or d.get('email') or d.get('home_team') or d.get('match_name') or d.get('event') or 'Registro real'
                meta = d.get('created_at') or d.get('updated_at') or d.get('date') or d.get('kickoff') or d.get('status') or ''
                badge = d.get('membership') or d.get('tier') or d.get('plan') or d.get('result') or d.get('status') or t
                out.append({'title': str(title), 'meta': str(meta), 'badge': str(badge), 'table': t})
            return out
        except Exception:
            continue
    return []


def _env_status(name):
    configured = bool(os.environ.get(name))
    return {'name': name, 'configured': configured, 'label': 'OK' if configured else 'FALTA'}


def _db_size(path):
    try:
        return Path(path).stat().st_size if path else 0
    except Exception:
        return 0


def _fmt_bytes(n):
    try:
        n = float(n)
        for unit in ['B','KB','MB','GB']:
            if n < 1024:
                return f"{n:.0f} {unit}" if unit == 'B' else f"{n:.1f} {unit}"
            n /= 1024
        return f"{n:.1f} TB"
    except Exception:
        return '—'


def build_admin_command_center():
    con, path = _connect()
    try:
        table_list = _tables(con)
        users = _count(con, ['users', 'clientes', 'clients', 'user'])
        fixtures = _count(con, ['fixtures', 'matches', 'events', 'real_fixtures'])
        picks = _count(con, ['picks', 'bets', 'apuestas'])
        favs = _count(con, ['favorites', 'user_favorites', 'favoritos'])
        alerts = _count(con, ['notification_queue', 'push_notifications', 'telegram_alerts', 'alerts'])
        subs = _count(con, ['push_subscriptions', 'telegram_users', 'subscriptions'])
        free = _count_where(con, ['users', 'clientes', 'clients'], "LOWER(COALESCE(membership,tier,plan,''))='free'")
        pro = _count_where(con, ['users', 'clientes', 'clients'], "LOWER(COALESCE(membership,tier,plan,''))='pro'")
        elite = _count_where(con, ['users', 'clientes', 'clients'], "LOWER(COALESCE(membership,tier,plan,''))='elite'")
        recent_users = _recent(con, ['users', 'clientes', 'clients'])
        recent_picks = _recent(con, ['picks', 'bets', 'apuestas'])
        recent_alerts = _recent(con, ['notification_queue', 'push_notifications', 'telegram_alerts', 'alerts'])
        recent_fixtures = _recent(con, ['fixtures', 'matches', 'events', 'real_fixtures'])
    finally:
        try:
            if con: con.close()
        except Exception:
            pass

    envs = [_env_status('DATABASE_PATH'), _env_status('DB_PATH'), _env_status('THE_ODDS_API_KEY'), _env_status('TELEGRAM_BOT_TOKEN'), _env_status('OPENAI_API_KEY'), _env_status('STRIPE_SECRET_KEY'), _env_status('VAPID_PUBLIC_KEY')]
    configured = sum(1 for e in envs if e['configured'])
    critical = []
    if not path:
        critical.append('No se detecta SQLite persistente. Revisa Render Disk y DATABASE_PATH/DB_PATH.')
    if not any(e['name'] == 'THE_ODDS_API_KEY' and e['configured'] for e in envs):
        critical.append('The Odds API no configurada: fixtures/picks reales dependerán de caché o estados vacíos.')
    if not any(e['name'] == 'TELEGRAM_BOT_TOKEN' and e['configured'] for e in envs):
        critical.append('Telegram no configurado: alertas premium no se enviarán.')
    if any(e['name'] == 'STRIPE_SECRET_KEY' and e['configured'] for e in envs):
        billing = 'Stripe configurado en entorno. Revisar webhook antes de activar upgrades reales.'
    else:
        billing = 'Stripe foundation segura: pagos desactivados hasta configurar claves reales.'

    score = 52
    score += 10 if path else 0
    score += min(configured * 4, 24)
    score += 4 if users not in (None, 0) else 0
    score += 4 if fixtures not in (None, 0) else 0
    score += 4 if picks not in (None, 0) else 0
    score += 4 if favs not in (None, 0) else 0
    score -= len(critical) * 6
    score = max(0, min(100, score))

    today = datetime.utcnow().date().isoformat()
    return {
        'ok': True,
        'version': 'V167_ADMIN_COMMAND_CENTER_PRO',
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'today': today,
        'health_score': score,
        'database': {'detected': bool(path), 'path': path or 'NO_DETECTED', 'size': _fmt_bytes(_db_size(path)), 'tables': len(table_list)},
        'runtime': {'python': platform.python_version(), 'platform': platform.system(), 'render': bool(os.environ.get('RENDER'))},
        'kpis': [
            {'label': 'Usuarios', 'value': users if users is not None else '—', 'tone': 'blue', 'hint': 'usuarios reales detectados'},
            {'label': 'Fixtures', 'value': fixtures if fixtures is not None else '—', 'tone': 'cyan', 'hint': 'partidos/cache real'},
            {'label': 'Picks', 'value': picks if picks is not None else '—', 'tone': 'green', 'hint': 'picks/operaciones'},
            {'label': 'Favoritos', 'value': favs if favs is not None else '—', 'tone': 'gold', 'hint': 'seguimiento cliente'},
            {'label': 'Alertas', 'value': alerts if alerts is not None else '—', 'tone': 'purple', 'hint': 'push/telegram/colas'},
            {'label': 'Suscripciones', 'value': subs if subs is not None else '—', 'tone': 'pink', 'hint': 'push/telegram/billing'},
        ],
        'memberships': [
            {'label': 'FREE', 'value': free if free is not None else '—', 'class': 'free'},
            {'label': 'PRO', 'value': pro if pro is not None else '—', 'class': 'pro'},
            {'label': 'ELITE', 'value': elite if elite is not None else '—', 'class': 'elite'},
        ],
        'env': envs,
        'critical': critical,
        'billing_note': billing,
        'recent': {'users': recent_users, 'fixtures': recent_fixtures, 'picks': recent_picks, 'alerts': recent_alerts},
        'daily_checklist': [
            {'label': 'Revisar sync de partidos', 'href': '/admin/fixtures-sync', 'status': 'real-core'},
            {'label': 'Cerrar picks pendientes', 'href': '/admin/results', 'status': 'roi'},
            {'label': 'Comprobar Telegram Live', 'href': '/admin/telegram-live', 'status': 'alerts'},
            {'label': 'Ver cola de notificaciones', 'href': '/admin/push-center', 'status': 'push'},
            {'label': 'Revisar billing foundation', 'href': '/admin/billing-center', 'status': 'billing'},
        ],
        'quick_links': [
            {'label': 'Cliente PRO', 'href': '/cliente/pro'},
            {'label': 'Live Ecosystem', 'href': '/live-ecosystem'},
            {'label': 'Match Center', 'href': '/match-center-pro'},
            {'label': 'Smart Live', 'href': '/api/v163/smart-home'},
            {'label': 'Stats Cliente', 'href': '/api/v161/client-stats'},
            {'label': 'Telegram Premium', 'href': '/admin/telegram-premium'},
            {'label': 'Push Center', 'href': '/admin/push-center'},
            {'label': 'Billing', 'href': '/admin/billing-center'},
        ],
        'policy': {'no_fake_matches': True, 'no_fake_picks': True, 'no_fake_scores': True}
    }


@admin_command_v167_bp.route('/api/v167/admin-command-center')
def api_admin_command_center():
    return jsonify(build_admin_command_center())


@admin_command_v167_bp.route('/admin/command')
@admin_command_v167_bp.route('/admin/command-center')
@admin_command_v167_bp.route('/admin/admin-command-center')
@admin_command_v167_bp.route('/admin')
def page_admin_command_center():
    if not _is_admin_session():
        return redirect('/admin-login')
    return render_template('admin_command_v167.html', data=build_admin_command_center())
