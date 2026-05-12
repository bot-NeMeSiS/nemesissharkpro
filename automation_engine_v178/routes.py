from flask import Blueprint, jsonify, render_template, request
from datetime import datetime, timedelta
from pathlib import Path
import os, sqlite3, json, time, hashlib

automation_engine_v178_bp = Blueprint('automation_engine_v178_bp', __name__)


def _db_candidates():
    return [os.environ.get('DATABASE_PATH'), os.environ.get('DB_PATH'), '/data/app.db', '/data/database.db', 'app.db', 'database.db']


def _db_path():
    for p in _db_candidates():
        if p and Path(p).exists():
            return str(Path(p))
    fallback = os.environ.get('DATABASE_PATH') or os.environ.get('DB_PATH') or '/data/app.db'
    try:
        Path(fallback).parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        fallback = 'app.db'
    return fallback


def _connect():
    con = sqlite3.connect(_db_path(), timeout=5)
    con.row_factory = sqlite3.Row
    return con


def _now():
    return datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'


def _init_db():
    con = _connect()
    try:
        con.execute('''CREATE TABLE IF NOT EXISTS automation_jobs_v178 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_key TEXT UNIQUE,
            title TEXT,
            job_type TEXT,
            enabled INTEGER DEFAULT 1,
            interval_minutes INTEGER DEFAULT 60,
            last_run_at TEXT,
            next_run_at TEXT,
            last_status TEXT,
            last_message TEXT,
            run_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        con.execute('''CREATE TABLE IF NOT EXISTS automation_runs_v178 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_key TEXT,
            status TEXT,
            message TEXT,
            payload_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        con.execute('''CREATE TABLE IF NOT EXISTS automation_locks_v178 (
            lock_key TEXT PRIMARY KEY,
            locked_until TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        defaults = [
            ('fixtures_sync', 'Sincronizar partidos reales', 'fixtures', 1, 180),
            ('telegram_daily_admin', 'Enviar resumen admin Telegram', 'telegram_admin', 1, 360),
            ('telegram_memberships', 'Delivery Telegram por membresía', 'telegram_membership', 1, 240),
            ('smart_live_refresh', 'Actualizar Smart Live Signals', 'smart_live', 1, 45),
            ('system_health_check', 'Health check sistema', 'health', 1, 60),
            ('cleanup_soft', 'Limpieza suave de logs/caché', 'cleanup', 1, 720),
        ]
        for key, title, typ, enabled, interval in defaults:
            next_run = (datetime.utcnow() + timedelta(minutes=interval)).replace(microsecond=0).isoformat() + 'Z'
            con.execute('''INSERT OR IGNORE INTO automation_jobs_v178
                (job_key,title,job_type,enabled,interval_minutes,next_run_at,last_status,last_message)
                VALUES (?,?,?,?,?,?,?,?)''', (key,title,typ,enabled,interval,next_run,'pendiente','Preparado'))
        con.commit()
    finally:
        con.close()


def _rows(table, where='', params=(), limit=100):
    con = _connect()
    try:
        sql = f'SELECT * FROM {table} {where} LIMIT ?'
        return [dict(r) for r in con.execute(sql, (*params, limit)).fetchall()]
    finally:
        con.close()


def _table_count(con, table):
    try:
        exists = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
        if not exists:
            return None
        return int(con.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0])
    except Exception:
        return None


def _log_run(job_key, status, message, payload=None):
    con = _connect()
    try:
        con.execute('''INSERT INTO automation_runs_v178(job_key,status,message,payload_json,created_at)
                       VALUES (?,?,?,?,?)''', (job_key,status,message,json.dumps(payload or {}, ensure_ascii=False),_now()))
        con.execute('''UPDATE automation_jobs_v178
                       SET last_run_at=?, last_status=?, last_message=?, run_count=COALESCE(run_count,0)+1,
                           next_run_at=datetime('now', '+' || interval_minutes || ' minutes')
                       WHERE job_key=?''', (_now(), status, message, job_key))
        con.commit()
    finally:
        con.close()


def _job_payload(job):
    con = _connect()
    try:
        users = _table_count(con, 'users')
        fixtures = _table_count(con, 'fixtures') or _table_count(con, 'matches')
        picks = _table_count(con, 'picks')
        telegram_logs = _table_count(con, 'telegram_delivery_logs')
        notification_queue = _table_count(con, 'notification_queue')
    finally:
        con.close()
    return {
        'job': job.get('job_key'),
        'type': job.get('job_type'),
        'users': users,
        'fixtures_or_matches': fixtures,
        'picks': picks,
        'telegram_logs': telegram_logs,
        'notification_queue': notification_queue,
        'generated_at': _now(),
    }


def run_job(job_key, force=False):
    _init_db()
    con = _connect()
    try:
        row = con.execute('SELECT * FROM automation_jobs_v178 WHERE job_key=?', (job_key,)).fetchone()
        if not row:
            return {'ok': False, 'error': 'job_not_found'}
        job = dict(row)
        if not job.get('enabled') and not force:
            _log_run(job_key, 'saltado', 'Job desactivado', {'enabled': False})
            return {'ok': True, 'status': 'saltado', 'message': 'Job desactivado'}
    finally:
        con.close()

    payload = _job_payload(job)
    # V178 no inventa datos ni fuerza llamadas externas: prepara/orquesta y deja trazabilidad real.
    messages = {
        'fixtures': 'Sync de fixtures preparado. Usa el conector real/cache existente si está disponible.',
        'telegram_admin': 'Resumen admin preparado para Telegram usando TELEGRAM_ADMIN_CHAT_ID si está configurado.',
        'telegram_membership': 'Delivery por membresía preparado con anti-duplicados V173/V174.',
        'smart_live': 'Smart Live refresh preparado sobre señales reales/cacheadas.',
        'health': 'Health check ejecutado con tablas/entorno actuales.',
        'cleanup': 'Limpieza suave registrada; no elimina datos críticos.',
    }
    msg = messages.get(job.get('job_type'), 'Job ejecutado')
    status = 'ok'
    if job.get('job_type') == 'telegram_admin' and not os.environ.get('TELEGRAM_ADMIN_CHAT_ID'):
        status = 'warning'
        msg = 'Falta TELEGRAM_ADMIN_CHAT_ID para enviar al admin privado.'
    if job.get('job_type') == 'telegram_membership' and not (os.environ.get('TELEGRAM_BOT_TOKEN') or os.environ.get('BOT_TOKEN')):
        status = 'warning'
        msg = 'Falta TELEGRAM_BOT_TOKEN/BOT_TOKEN para delivery Telegram.'
    _log_run(job_key, status, msg, payload)
    return {'ok': True, 'status': status, 'message': msg, 'payload': payload}


def build_center():
    _init_db()
    con = _connect()
    try:
        jobs = [dict(r) for r in con.execute('SELECT * FROM automation_jobs_v178 ORDER BY enabled DESC, job_key ASC').fetchall()]
        runs = [dict(r) for r in con.execute('SELECT * FROM automation_runs_v178 ORDER BY id DESC LIMIT 30').fetchall()]
        enabled = sum(1 for j in jobs if j.get('enabled'))
        warnings = []
        if not os.environ.get('TELEGRAM_ADMIN_CHAT_ID'):
            warnings.append('Configura TELEGRAM_ADMIN_CHAT_ID para que el admin reciba avisos privados.')
        if not (os.environ.get('TELEGRAM_BOT_TOKEN') or os.environ.get('BOT_TOKEN')):
            warnings.append('Configura TELEGRAM_BOT_TOKEN/BOT_TOKEN para automatizaciones Telegram.')
        if not os.environ.get('AUTOMATION_SECRET'):
            warnings.append('Recomendado añadir AUTOMATION_SECRET para proteger cron endpoints.')
    finally:
        con.close()
    return {
        'version': 'V178',
        'generated_at': _now(),
        'jobs': jobs,
        'runs': runs,
        'summary': {
            'jobs_total': len(jobs),
            'jobs_enabled': enabled,
            'runs_shown': len(runs),
            'status': 'operativo' if enabled else 'sin_jobs_activos',
        },
        'warnings': warnings,
        'cron_url': '/api/v178/automation/run-due',
        'manual_url': '/api/v178/automation/run/<job_key>',
    }


def _authorized():
    secret = os.environ.get('AUTOMATION_SECRET')
    if not secret:
        return True
    return request.headers.get('X-Automation-Secret') == secret or request.args.get('secret') == secret


@automation_engine_v178_bp.route('/admin/automation-engine')
@automation_engine_v178_bp.route('/admin/automation')
@automation_engine_v178_bp.route('/admin/jobs')
def automation_page():
    return render_template('v178/automation_engine.html', data=build_center())


@automation_engine_v178_bp.route('/api/v178/automation/status')
def api_status():
    return jsonify({'ok': True, 'data': build_center()})


@automation_engine_v178_bp.route('/api/v178/automation/run/<job_key>', methods=['GET','POST'])
def api_run_job(job_key):
    if not _authorized():
        return jsonify({'ok': False, 'error': 'unauthorized'}), 401
    return jsonify(run_job(job_key, force=True))


@automation_engine_v178_bp.route('/api/v178/automation/run-due', methods=['GET','POST'])
def api_run_due():
    if not _authorized():
        return jsonify({'ok': False, 'error': 'unauthorized'}), 401
    _init_db()
    con = _connect()
    try:
        jobs = [dict(r) for r in con.execute("SELECT * FROM automation_jobs_v178 WHERE enabled=1").fetchall()]
    finally:
        con.close()
    results = []
    now_ts = datetime.utcnow()
    for job in jobs:
        nxt = job.get('next_run_at')
        due = True
        if nxt:
            try:
                due = datetime.fromisoformat(nxt.replace('Z','')) <= now_ts
            except Exception:
                due = True
        if due:
            results.append(run_job(job['job_key'], force=False))
    return jsonify({'ok': True, 'ran': len(results), 'results': results, 'generated_at': _now()})


@automation_engine_v178_bp.route('/api/v178/automation/toggle/<job_key>', methods=['POST'])
def api_toggle(job_key):
    if not _authorized():
        return jsonify({'ok': False, 'error': 'unauthorized'}), 401
    _init_db()
    con = _connect()
    try:
        row = con.execute('SELECT enabled FROM automation_jobs_v178 WHERE job_key=?', (job_key,)).fetchone()
        if not row:
            return jsonify({'ok': False, 'error': 'job_not_found'}), 404
        new_value = 0 if int(row['enabled'] or 0) else 1
        con.execute('UPDATE automation_jobs_v178 SET enabled=? WHERE job_key=?', (new_value, job_key))
        con.commit()
    finally:
        con.close()
    return jsonify({'ok': True, 'job_key': job_key, 'enabled': bool(new_value)})
