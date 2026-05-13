from flask import Blueprint, jsonify, render_template, request
from datetime import datetime
import os
import sqlite3

bp_premium_match_radar_v207 = Blueprint('premium_match_radar_v207', __name__)


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


def _safe_float(v, default=None):
    try:
        if v in (None, ''):
            return default
        return float(v)
    except Exception:
        return default


def _safe_int(v, default=0):
    try:
        if v in (None, ''):
            return default
        return int(float(v))
    except Exception:
        return default


def _fixture_rows(limit=80):
    # Fuente principal: conector real V146 + recuperación V206.1 desde picks/cuotas reales.
    try:
        from fixtures_connector_v146.core import list_fixtures
        rows = list_fixtures('live', limit)
        if not rows:
            rows = list_fixtures('today', limit)
        if not rows:
            rows = list_fixtures('upcoming', limit)
        return rows[:limit]
    except Exception:
        return []


def _tables(conn):
    try:
        return {r['name'] for r in conn.execute("select name from sqlite_master where type='table'").fetchall()}
    except Exception:
        return set()


def _stored_odds_movements(limit=200):
    try:
        conn = _connect()
        try:
            if 'odds_movement_snapshots_v206' not in _tables(conn):
                return []
            rows = conn.execute('select * from odds_movement_snapshots_v206 order by id desc limit ?', (int(limit),)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
    except Exception:
        return []


def _pick(row, keys, default=None):
    for k in keys:
        for rk, rv in row.items():
            if rk.lower() == k.lower() and rv not in (None, ''):
                return rv
    return default


def _norm_name(v):
    return str(v or '').strip().lower()


def _movement_for_match(row, movements):
    home = _norm_name(_pick(row, ['home_team', 'home', 'equipo_local', 'local_team']))
    away = _norm_name(_pick(row, ['away_team', 'away', 'equipo_visitante', 'visitor_team']))
    league = _norm_name(_pick(row, ['league', 'competition', 'league_name', 'sport_key']))
    best = None
    for m in movements:
        mh = _norm_name(m.get('home_team'))
        ma = _norm_name(m.get('away_team'))
        ml = _norm_name(m.get('league'))
        same_teams = home and away and ((home == mh and away == ma) or (home == ma and away == mh))
        same_league = league and ml and league == ml
        if same_teams or (same_league and (home in mh or away in ma or mh in home or ma in away)):
            best = m
            break
    return best


def _status_points(status):
    s = str(status or '').lower()
    if any(x in s for x in ['live', 'in_play', 'inplay', '1h', '2h', 'en vivo', 'en directo']):
        return 30, 'En directo'
    if any(x in s for x in ['ht', 'descanso']):
        return 24, 'Descanso'
    if any(x in s for x in ['upcoming', 'scheduled', 'pre', 'not_started', 'programado']):
        return 12, 'Próximo'
    if any(x in s for x in ['finished', 'ft', 'finalizado']):
        return 4, 'Finalizado'
    return 10, 'Seguimiento'


def _radar_card(row, idx, movements):
    home = _pick(row, ['home_team', 'home', 'equipo_local', 'local_team', 'home_name'], 'Local')
    away = _pick(row, ['away_team', 'away', 'equipo_visitante', 'visitor_team', 'away_name'], 'Visitante')
    league = _pick(row, ['league', 'competition', 'league_name', 'sport_key'], 'Competición')
    kickoff = _pick(row, ['kickoff', 'commence_time', 'start_time', 'fecha', 'date'], '')
    status_raw = _pick(row, ['status', 'fixture_status', 'state'], '')
    base_points, estado = _status_points(status_raw)
    hs = _pick(row, ['score_home', 'home_score', 'goals_home'])
    as_ = _pick(row, ['score_away', 'away_score', 'goals_away'])
    marcador = f'{hs} - {as_}' if hs is not None and as_ is not None else 'vs'
    confidence = _safe_float(_pick(row, ['confidence', 'confianza', 'shark_score', 'score']), None)
    pick_quality = max(0, min(25, int((confidence or 0) / 4))) if confidence is not None else 0
    movement = _movement_for_match(row, movements)
    heat = str((movement or {}).get('heat_level') or '').lower()
    market_points = 0
    if 'fuerte' in heat:
        market_points = 25
    elif 'caliente' in heat:
        market_points = 20
    elif 'moderado' in heat:
        market_points = 12
    elif 'leve' in heat:
        market_points = 7
    live_bias = (idx * 3) % 10  # solo desempate visual estable, no crea datos deportivos.
    radar_score = max(0, min(100, base_points + pick_quality + market_points + live_bias + 20))
    if radar_score >= 82:
        nivel = 'Muy alto'
        badge = '🔥 Radar caliente'
    elif radar_score >= 68:
        nivel = 'Alto'
        badge = '⚡ Alta atención'
    elif radar_score >= 50:
        nivel = 'Medio'
        badge = '🎯 Interesante'
    else:
        nivel = 'Bajo'
        badge = '🛡️ Seguimiento'
    razones = []
    if estado in ('En directo', 'Descanso'):
        razones.append('partido en seguimiento live')
    if confidence is not None:
        razones.append(f'confianza detectada {int(confidence)}%')
    if movement:
        razones.append('movimiento de cuota registrado')
    if not razones:
        razones.append('partido real disponible sin señales suficientes todavía')
    return {
        'local': str(home),
        'visitante': str(away),
        'competicion': str(league),
        'inicio': str(kickoff or 'Pendiente'),
        'estado': estado,
        'marcador': marcador,
        'radar_score': radar_score,
        'nivel': nivel,
        'badge': badge,
        'confianza': None if confidence is None else int(confidence),
        'mercado': (movement or {}).get('heat_level') or 'sin historial suficiente',
        'movimiento_pct': (movement or {}).get('movement_pct'),
        'razones': razones,
    }


def radar_payload(limit=60):
    fixtures = _fixture_rows(limit)
    movements = _stored_odds_movements(250)
    cards = [_radar_card(r, i, movements) for i, r in enumerate(fixtures)]
    cards.sort(key=lambda c: c['radar_score'], reverse=True)
    hot = [c for c in cards if c['radar_score'] >= 68]
    return {
        'version': 'V207_PREMIUM_MATCH_RADAR_PRO',
        'modo': 'REAL ONLY',
        'generado': datetime.utcnow().isoformat() + 'Z',
        'total_partidos': len(cards),
        'partidos_calientes': len(hot),
        'cards': cards,
        'resumen': {
            'estado': 'Activo' if cards else 'Esperando partidos reales',
            'fuentes': ['fixtures reales V146/V206.1', 'movimientos de cuotas V206', 'picks/confianza si existen'],
            'nota': 'El radar ordena datos reales disponibles. No crea partidos, cuotas ni resultados.'
        },
        'mensaje_vacio': 'No hay partidos reales disponibles en caché ahora mismo. Sin proveedor, sync o cuotas reales, el radar no inventa contenido.'
    }


@bp_premium_match_radar_v207.route('/api/v207/match-radar')
def api_match_radar_v207():
    limit = _safe_int(request.args.get('limit'), 60)
    return jsonify(radar_payload(limit=limit))


@bp_premium_match_radar_v207.route('/cliente/match-radar')
@bp_premium_match_radar_v207.route('/cliente/premium-radar')
@bp_premium_match_radar_v207.route('/premium-match-radar')
def cliente_match_radar_v207():
    return render_template('premium_match_radar_v207.html', data=radar_payload(), admin=False)


@bp_premium_match_radar_v207.route('/admin/match-radar')
@bp_premium_match_radar_v207.route('/admin/premium-match-radar')
def admin_match_radar_v207():
    return render_template('premium_match_radar_v207.html', data=radar_payload(), admin=True)
