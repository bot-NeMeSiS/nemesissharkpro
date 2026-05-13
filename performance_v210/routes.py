
from flask import Blueprint, jsonify, render_template, request
from datetime import datetime
from pathlib import Path
import os
import sqlite3
import time

bp_performance_v210 = Blueprint('performance_v210', __name__)


def _db_path():
    return os.environ.get('DATABASE_PATH') or os.environ.get('DB_PATH') or ('/data/database.db' if os.path.exists('/data/database.db') else '/data/app.db')


def _connect():
    path = _db_path()
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    conn = sqlite3.connect(path, timeout=6)
    conn.row_factory = sqlite3.Row
    return conn


def _tables(conn):
    try:
        return {r['name'] for r in conn.execute("select name from sqlite_master where type='table'").fetchall()}
    except Exception:
        return set()


def _count(conn, table):
    try:
        return int(conn.execute(f"select count(*) as n from {table}").fetchone()['n'])
    except Exception:
        return 0


def _ensure_db():
    conn = _connect()
    try:
        conn.execute("""
            create table if not exists performance_snapshots_v210 (
                id integer primary key autoincrement,
                db_path text,
                db_exists integer,
                db_size_mb real,
                tables_count integer,
                fixtures_count integer,
                picks_count integer,
                odds_snapshots_count integer,
                notifications_count integer,
                score_ms real,
                status text,
                created_at text not null
            )
        """)
        conn.execute("""
            create table if not exists performance_cache_v210 (
                cache_key text primary key,
                payload text,
                ttl_seconds integer not null default 60,
                created_at text not null
            )
        """)
        tables = _tables(conn)
        index_jobs = []
        if 'picks' in tables:
            index_jobs += [
                "create index if not exists idx_v210_picks_created on picks(created_at)",
                "create index if not exists idx_v210_picks_kickoff on picks(kickoff_time)",
            ]
        if 'real_fixtures_v146' in tables:
            index_jobs += [
                "create index if not exists idx_v210_fixtures_kickoff on real_fixtures_v146(kickoff)",
                "create index if not exists idx_v210_fixtures_status on real_fixtures_v146(status)",
            ]
        if 'odds_movement_snapshots_v206' in tables:
            index_jobs += ["create index if not exists idx_v210_odds_captured on odds_movement_snapshots_v206(captured_at)"]
        if 'smart_notifications_v205' in tables:
            index_jobs += ["create index if not exists idx_v210_notifications_created on smart_notifications_v205(created_at)"]
        for sql in index_jobs:
            try:
                conn.execute(sql)
            except Exception:
                pass
        conn.commit()
    finally:
        conn.close()


def _status_payload(save=True):
    started = time.perf_counter()
    db_path = _db_path()
    exists = os.path.exists(db_path)
    size = round(os.path.getsize(db_path) / (1024*1024), 2) if exists else 0
    conn = _connect()
    try:
        tables = _tables(conn)
        fixtures = _count(conn, 'real_fixtures_v146') if 'real_fixtures_v146' in tables else 0
        picks = _count(conn, 'picks') if 'picks' in tables else 0
        odds = _count(conn, 'odds_movement_snapshots_v206') if 'odds_movement_snapshots_v206' in tables else 0
        notifs = _count(conn, 'smart_notifications_v205') if 'smart_notifications_v205' in tables else 0
        ms = round((time.perf_counter() - started) * 1000, 2)
        if not exists:
            estado = 'pendiente'
        elif ms <= 80:
            estado = 'rápido'
        elif ms <= 180:
            estado = 'correcto'
        else:
            estado = 'revisar'
        payload = {
            'version': 'V210',
            'nombre': 'Real Performance Optimization Pro',
            'estado': estado,
            'db_path': db_path,
            'db_existe': bool(exists),
            'db_size_mb': size,
            'tablas': len(tables),
            'fixtures': fixtures,
            'picks': picks,
            'odds_snapshots': odds,
            'notificaciones': notifs,
            'score_ms': ms,
            'recomendaciones': _recommendations(exists, size, fixtures, picks, ms),
            'fecha': datetime.utcnow().isoformat(timespec='seconds') + 'Z'
        }
        if save:
            try:
                conn.execute("""insert into performance_snapshots_v210
                    (db_path, db_exists, db_size_mb, tables_count, fixtures_count, picks_count, odds_snapshots_count, notifications_count, score_ms, status, created_at)
                    values (?,?,?,?,?,?,?,?,?,?,?)""",
                    (db_path, 1 if exists else 0, size, len(tables), fixtures, picks, odds, notifs, ms, estado, payload['fecha']))
                conn.commit()
            except Exception:
                pass
        return payload
    finally:
        conn.close()


def _recommendations(exists, size, fixtures, picks, ms):
    rec=[]
    if not exists:
        rec.append('Configurar disco persistente y DATABASE_PATH en Render.')
    if fixtures == 0 and picks == 0:
        rec.append('No hay datos cacheados: ejecutar sincronización de fixtures/picks reales.')
    if size > 250:
        rec.append('Base de datos grande: revisar limpieza de snapshots antiguos y exportaciones.')
    if ms > 180:
        rec.append('Lectura lenta: revisar índices, tamaño de tablas y endpoints pesados.')
    if not rec:
        rec.append('Rendimiento correcto. Mantener caché y sincronizaciones programadas.')
    return rec


@bp_performance_v210.route('/api/v210/performance/status')
def api_performance_status():
    _ensure_db()
    return jsonify(_status_payload(save=True))


@bp_performance_v210.route('/admin/performance')
@bp_performance_v210.route('/admin/performance-v210')
def admin_performance_v210():
    _ensure_db()
    return render_template('performance_v210_admin.html', status=_status_payload(save=True))


@bp_performance_v210.route('/cliente/performance-lite')
def cliente_performance_lite_v210():
    _ensure_db()
    return render_template('performance_v210_client.html', status=_status_payload(save=False))


@bp_performance_v210.route('/api/v210/mobile-lite/fixtures')
def mobile_lite_fixtures_v210():
    """Endpoint ligero: solo lee caché/local DB, sin llamar APIs externas."""
    limit = min(int(request.args.get('limit', 30) or 30), 80)
    data=[]
    try:
        from live_score_incidents_v209.routes import _all_matches
        for m in _all_matches(limit=limit):
            data.append({
                'id': m.get('id'),
                'partido': m.get('partido'),
                'competicion': m.get('competicion'),
                'estado': m.get('estado'),
                'minuto': m.get('minuto'),
                'marcador': m.get('marcador'),
                'en_directo': m.get('en_directo'),
                'tiene_marcador': m.get('tiene_marcador'),
            })
    except Exception:
        pass
    return jsonify({'version':'V210','modo':'ligero_movil','count':len(data),'partidos':data[:limit]})


@bp_performance_v210.route('/api/v210/performance/optimize', methods=['POST','GET'])
def optimize_v210():
    _ensure_db()
    conn = _connect()
    notes=[]
    try:
        try:
            conn.execute('pragma optimize')
            notes.append('PRAGMA optimize ejecutado.')
        except Exception:
            notes.append('PRAGMA optimize no disponible en este entorno.')
        try:
            conn.execute('analyze')
            notes.append('ANALYZE ejecutado para mejorar estadísticas SQLite.')
        except Exception:
            pass
        conn.commit()
    finally:
        conn.close()
    payload=_status_payload(save=True)
    payload['acciones']=notes
    return jsonify(payload)
