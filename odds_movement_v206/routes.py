from flask import Blueprint, jsonify, render_template, request, session
from datetime import datetime
import os
import sqlite3

bp_odds_movement_v206 = Blueprint('odds_movement_v206', __name__)


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
            create table if not exists odds_movement_snapshots_v206 (
                id integer primary key autoincrement,
                match_id text,
                provider text,
                sport text,
                league text,
                home_team text,
                away_team text,
                market text,
                selection text,
                odd_value real,
                previous_odd real,
                movement real,
                movement_pct real,
                heat_level text not null default 'sin datos',
                source text not null default 'v206',
                captured_at text not null
            )
        ''')
        conn.execute('''
            create table if not exists odds_movement_audit_v206 (
                id integer primary key autoincrement,
                action text not null,
                details text,
                created_at text not null
            )
        ''')
        conn.commit()
    finally:
        conn.close()


def _safe_float(value):
    try:
        if value is None or value == '':
            return None
        return float(value)
    except Exception:
        return None


def _classify_heat(movement_pct):
    if movement_pct is None:
        return 'sin datos'
    amp = abs(float(movement_pct))
    if amp >= 12:
        return 'movimiento fuerte'
    if amp >= 7:
        return 'mercado caliente'
    if amp >= 3:
        return 'movimiento moderado'
    if amp > 0:
        return 'movimiento leve'
    return 'estable'


def _direction(movement):
    if movement is None:
        return 'sin dirección'
    if movement > 0:
        return 'sube'
    if movement < 0:
        return 'baja'
    return 'estable'


def _session_user_name():
    return str(session.get('username') or session.get('user_name') or session.get('user') or 'Usuario')


def _tables(conn):
    rows = conn.execute("select name from sqlite_master where type='table'").fetchall()
    return {r['name'] for r in rows}


def _columns(conn, table):
    try:
        return {r['name'] for r in conn.execute(f'pragma table_info({table})').fetchall()}
    except Exception:
        return set()


def _discover_odds_rows(limit=80):
    """Lee cuotas reales desde tablas existentes si las hay. No genera cuotas inventadas."""
    _init_db()
    conn = _connect()
    found = []
    try:
        tables = _tables(conn)
        candidate_tables = [t for t in tables if any(k in t.lower() for k in ('odd', 'cuota', 'pick', 'snapshot'))]
        for table in candidate_tables[:12]:
            cols = _columns(conn, table)
            odd_cols = [c for c in cols if c.lower() in ('odd','odds','cuota','price','odd_value','quota') or 'odd' in c.lower() or 'cuota' in c.lower()]
            if not odd_cols:
                continue
            team_cols = [c for c in cols if c.lower() in ('home_team','away_team','equipo_local','equipo_visitante','home','away','match_name','partido','title')]
            date_cols = [c for c in cols if 'created' in c.lower() or 'captured' in c.lower() or 'updated' in c.lower() or 'fecha' in c.lower() or 'time' in c.lower()]
            select_cols = list(dict.fromkeys(odd_cols[:2] + team_cols[:6] + date_cols[:2]))
            if not select_cols:
                continue
            sql = f"select {', '.join(select_cols)} from {table} order by rowid desc limit ?"
            try:
                rows = conn.execute(sql, (int(limit),)).fetchall()
            except Exception:
                continue
            for r in rows:
                d = dict(r)
                odd = None
                odd_col = None
                for oc in odd_cols:
                    odd = _safe_float(d.get(oc))
                    if odd is not None:
                        odd_col = oc
                        break
                if odd is None:
                    continue
                found.append({
                    'origen_tabla': table,
                    'columna_cuota': odd_col,
                    'cuota': odd,
                    'equipo_local': d.get('home_team') or d.get('equipo_local') or d.get('home'),
                    'equipo_visitante': d.get('away_team') or d.get('equipo_visitante') or d.get('away'),
                    'partido': d.get('match_name') or d.get('partido') or d.get('title'),
                    'fecha': next((d.get(c) for c in date_cols if d.get(c)), None)
                })
                if len(found) >= limit:
                    return found
        return found
    finally:
        conn.close()


def _stored_movements(limit=50):
    _init_db()
    conn = _connect()
    try:
        rows = conn.execute('select * from odds_movement_snapshots_v206 order by id desc limit ?', (int(limit),)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _summary():
    stored = _stored_movements(200)
    strong = [x for x in stored if x.get('heat_level') in ('movimiento fuerte', 'mercado caliente')]
    real_odds = _discover_odds_rows(30)
    return {
        'cuotas_detectadas': len(real_odds),
        'snapshots_v206': len(stored),
        'mercados_calientes': len(strong),
        'estado': 'Activo' if real_odds or stored else 'Preparado esperando cuotas reales',
        'nota': 'No se muestran cuotas inventadas. El motor se activa cuando haya cuotas reales guardadas por proveedores, picks o snapshots.'
    }


def odds_payload(admin=False):
    real_odds = _discover_odds_rows(60)
    stored = _stored_movements(60)
    return {
        'version': 'V206_ADVANCED_ODDS_MOVEMENT_ENGINE_PRO',
        'modo': 'REAL ONLY',
        'generado': datetime.utcnow().isoformat() + 'Z',
        'usuario': _session_user_name(),
        'admin': admin,
        'resumen': _summary(),
        'cuotas_reales_detectadas': real_odds,
        'movimientos_guardados': stored,
        'badges': ['Mercado caliente', 'Movimiento fuerte', 'Posible valor', 'Cuota estable'],
        'mensaje_vacio': 'Todavía no hay suficiente historial real de cuotas para mostrar movimientos. Cuando entren varias capturas reales, aparecerán subidas, bajadas e intensidad del mercado.'
    }


@bp_odds_movement_v206.route('/api/v206/odds-movement')
def api_odds_movement_v206():
    return jsonify(odds_payload(admin=bool(request.args.get('admin'))))


@bp_odds_movement_v206.route('/api/v206/odds-movement/snapshot', methods=['POST'])
def api_odds_snapshot_v206():
    data = request.get_json(silent=True) or request.form or {}
    odd = _safe_float(data.get('odd_value') or data.get('cuota') or data.get('odd'))
    if odd is None:
        return jsonify({'ok': False, 'error': 'Falta una cuota real válida.'}), 400
    prev = _safe_float(data.get('previous_odd') or data.get('cuota_anterior'))
    movement = None if prev is None else round(odd - prev, 4)
    movement_pct = None if not prev else round(((odd - prev) / prev) * 100, 2)
    heat = _classify_heat(movement_pct)
    _init_db()
    conn = _connect()
    try:
        conn.execute('''insert into odds_movement_snapshots_v206
            (match_id, provider, sport, league, home_team, away_team, market, selection, odd_value,
             previous_odd, movement, movement_pct, heat_level, source, captured_at)
            values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (data.get('match_id'), data.get('provider'), data.get('sport'), data.get('league'),
             data.get('home_team') or data.get('equipo_local'), data.get('away_team') or data.get('equipo_visitante'),
             data.get('market') or data.get('mercado'), data.get('selection') or data.get('seleccion'), odd,
             prev, movement, movement_pct, heat, data.get('source') or 'api_v206', datetime.utcnow().isoformat() + 'Z'))
        conn.commit()
        return jsonify({'ok': True, 'mensaje': 'Snapshot real de cuota registrado.', 'movimiento': movement, 'porcentaje': movement_pct, 'intensidad': heat})
    finally:
        conn.close()


@bp_odds_movement_v206.route('/cliente/odds-movement')
@bp_odds_movement_v206.route('/cliente/value-moves')
@bp_odds_movement_v206.route('/odds-movement-pro')
@bp_odds_movement_v206.route('/market-heat-pro')
def cliente_odds_movement_v206():
    return render_template('odds_movement_v206.html', data=odds_payload(admin=False), admin=False)


@bp_odds_movement_v206.route('/admin/odds-engine')
@bp_odds_movement_v206.route('/admin/odds-movement')
def admin_odds_movement_v206():
    return render_template('odds_movement_v206.html', data=odds_payload(admin=True), admin=True)
