from flask import Blueprint, jsonify, render_template, request
from datetime import datetime
from pathlib import Path
import json
import os
import sqlite3

bp_live_score_incidents_v209 = Blueprint('live_score_incidents_v209', __name__)

LIVE_WORDS = ('live','inplay','in_play','1h','2h','ht','et','p','en vivo','en directo','descanso')
FINISHED_WORDS = ('ft','finished','finalizado','ended','closed','aet','pen')


def _db_path():
    return os.environ.get('DATABASE_PATH') or os.environ.get('DB_PATH') or '/data/app.db'


def _connect():
    path = _db_path()
    if not os.path.exists(path) and os.path.exists('/data/database.db'):
        path = '/data/database.db'
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    conn = sqlite3.connect(path, timeout=8)
    conn.row_factory = sqlite3.Row
    return conn


def _tables(conn):
    try:
        return {r['name'] for r in conn.execute("select name from sqlite_master where type='table'").fetchall()}
    except Exception:
        return set()


def _cols(conn, table):
    try:
        return {r['name'] for r in conn.execute(f'pragma table_info({table})').fetchall()}
    except Exception:
        return set()


def _pick(row, keys, default=''):
    for key in keys:
        for rk, rv in row.items():
            if rk.lower() == key.lower() and rv not in (None, ''):
                return rv
    return default


def _split_score(score):
    if score is None:
        return None, None
    txt = str(score).strip().replace('–','-')
    if not txt or txt.lower() in ('vs','n/a','none'):
        return None, None
    for sep in [' - ', '-', ':']:
        if sep in txt:
            try:
                a,b = txt.split(sep,1)
                return int(str(a).strip()), int(str(b).strip())
            except Exception:
                return None, None
    return None, None


def _status_label(status):
    s = str(status or '').strip().lower()
    if any(w in s for w in LIVE_WORDS):
        return 'EN DIRECTO'
    if 'ht' == s or 'descanso' in s:
        return 'DESCANSO'
    if any(w in s for w in FINISHED_WORDS):
        return 'FINALIZADO'
    if any(w in s for w in ('susp','post','cancel','aplazado','suspendido')):
        return 'SUSPENDIDO'
    if any(w in s for w in ('ns','scheduled','upcoming','programado','not_started','pre')) or not s:
        return 'PROGRAMADO'
    return str(status or 'Seguimiento').upper()


def _is_live(status):
    s = str(status or '').lower()
    return any(w in s for w in LIVE_WORDS) or _status_label(status) in ('EN DIRECTO','DESCANSO')


def _is_finished(status):
    s = str(status or '').lower()
    return any(w in s for w in FINISHED_WORDS)


def _fixture_rows(limit=120):
    rows = []
    try:
        from fixtures_connector_v146.core import list_fixtures
        for filt in ('live','today','upcoming'):
            for r in list_fixtures(filt, limit):
                rows.append(dict(r))
    except Exception:
        pass
    seen, out = set(), []
    for r in rows:
        key = (str(r.get('external_id') or r.get('id') or ''), str(r.get('home_team') or '').lower(), str(r.get('away_team') or '').lower(), str(r.get('kickoff') or '')[:16])
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out[:limit]


def _rows_from_picks(limit=120):
    rows = []
    try:
        conn = _connect()
        try:
            if 'picks' not in _tables(conn):
                return []
            c = _cols(conn, 'picks')
            wanted = [x for x in ['id','sport','league','title','kickoff_time','live_status','live_score','live_minute','external_event_id','source','created_at','score','pick'] if x in c]
            sql = f"select {','.join(wanted)} from picks where coalesce(active,1)=1 order by case when lower(coalesce(live_status,'')) like '%directo%' then 0 when lower(coalesce(live_status,'')) like '%live%' then 0 else 1 end, coalesce(kickoff_time,created_at) asc, id desc limit ?"
            rows = [dict(r) for r in conn.execute(sql, (int(limit),)).fetchall()]
        finally:
            conn.close()
    except Exception:
        return []
    out=[]
    for r in rows:
        title = str(r.get('title') or '').strip()
        home, away = title, ''
        for sep in [' vs ', ' VS ', ' v ', ' - ', '–']:
            if sep in title:
                home, away = [p.strip() for p in title.split(sep,1)]
                break
        hs,as_ = _split_score(r.get('live_score'))
        out.append({
            'external_id': r.get('external_event_id') or f"pick_{r.get('id')}",
            'source': r.get('source') or 'picks',
            'sport': r.get('sport') or 'football',
            'league': r.get('league') or '',
            'home_team': home or 'Partido real',
            'away_team': away,
            'kickoff': r.get('kickoff_time') or r.get('created_at') or '',
            'status': r.get('live_status') or 'programado',
            'minute': r.get('live_minute') or '',
            'score_home': hs,
            'score_away': as_,
            'pick': r.get('pick') or '',
            'shark_score': r.get('score') or '',
        })
    return out


def _incidents_from_raw(row):
    raw = row.get('raw_json') or row.get('raw') or ''
    incidents=[]
    if not raw:
        return incidents
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        return []
    for key in ('events','incidents','timeline'):
        val = data.get(key) if isinstance(data, dict) else None
        if isinstance(val, list):
            for item in val[:20]:
                if not isinstance(item, dict):
                    continue
                minute = item.get('minute') or item.get('time') or item.get('elapsed') or ''
                tipo = item.get('type') or item.get('detail') or item.get('event_type') or 'Evento'
                team = item.get('team') or item.get('team_name') or ''
                player = item.get('player') or item.get('player_name') or ''
                incidents.append({'minuto': str(minute), 'tipo': str(tipo), 'equipo': str(team), 'jugador': str(player)})
    return incidents


def _normalize(row, idx=0):
    home = _pick(row, ['home_team','home','equipo_local','local_team','home_name'], 'Local')
    away = _pick(row, ['away_team','away','equipo_visitante','visitor_team','away_name'], 'Visitante')
    league = _pick(row, ['league','competition','league_name','sport_key'], 'Competición')
    status_raw = _pick(row, ['status','live_status','fixture_status','state'], '')
    status = _status_label(status_raw)
    minute = _pick(row, ['minute','live_minute','elapsed','match_minute','time'], '')
    hs = _pick(row, ['score_home','home_score','goals_home'], None)
    aw = _pick(row, ['score_away','away_score','goals_away'], None)
    if hs in ('', None) or aw in ('', None):
        hs2, aw2 = _split_score(_pick(row, ['score','live_score','result_score'], ''))
        hs = hs if hs not in ('', None) else hs2
        aw = aw if aw not in ('', None) else aw2
    has_score = hs is not None and aw is not None and hs != '' and aw != ''
    marcador = f'{hs} - {aw}' if has_score else 'Sin marcador real'
    live = _is_live(status_raw) or status == 'EN DIRECTO'
    finished = _is_finished(status_raw) or status == 'FINALIZADO'
    badge = '🔴 En directo' if live else '🏁 Finalizado' if finished else '📅 Programado'
    if status == 'DESCANSO':
        badge = '⏱️ Descanso'
    incidents = _incidents_from_raw(row)
    return {
        'id': str(_pick(row, ['external_id','event_id','id','match_id'], f'match_{idx}')),
        'partido': f'{home} vs {away}'.strip(' vs '),
        'local': str(home),
        'visitante': str(away),
        'competicion': str(league),
        'estado': status,
        'minuto': str(minute or ('Live' if live else '')),
        'marcador': marcador,
        'goles_local': hs if has_score else None,
        'goles_visitante': aw if has_score else None,
        'tiene_marcador': bool(has_score),
        'badge': badge,
        'en_directo': bool(live),
        'finalizado': bool(finished),
        'kickoff': _pick(row, ['kickoff','kickoff_time','date','commence_time'], ''),
        'source': _pick(row, ['source','provider'], 'real_core'),
        'incidents': incidents,
        'incidentes_count': len(incidents),
        'mensaje_score': 'Marcador recibido del proveedor' if has_score else 'El proveedor aún no ha enviado marcador para este partido.',
    }


def live_score_payload(limit=80):
    rows = []
    rows.extend(_fixture_rows(limit))
    rows.extend(_rows_from_picks(limit))
    seen, matches = set(), []
    for i, r in enumerate(rows):
        m = _normalize(r, i)
        key = (m['id'], m['local'].lower(), m['visitante'].lower(), str(m.get('kickoff'))[:16])
        if key in seen:
            continue
        seen.add(key)
        matches.append(m)
    matches.sort(key=lambda x: (0 if x['en_directo'] else 1 if x['estado']=='DESCANSO' else 2, 0 if x['tiene_marcador'] else 1, str(x.get('kickoff') or '')))
    with_score = sum(1 for m in matches if m['tiene_marcador'])
    live_count = sum(1 for m in matches if m['en_directo'])
    return {
        'version': 'V209_LIVE_SCORE_INCIDENTS_RECOVERY_PRO',
        'generado': datetime.utcnow().isoformat() + 'Z',
        'modo': 'REAL ONLY',
        'total_partidos': len(matches),
        'en_directo': live_count,
        'con_marcador': with_score,
        'partidos': matches[:int(limit)],
        'mensaje': 'Marcadores e incidentes se muestran solo cuando llegan desde proveedor o caché real. No se inventan resultados.',
    }


@bp_live_score_incidents_v209.route('/api/v209/live-score')
def api_live_score_v209():
    limit = request.args.get('limit', 80)
    try:
        limit = int(limit)
    except Exception:
        limit = 80
    return jsonify(live_score_payload(limit))


@bp_live_score_incidents_v209.route('/cliente/live-score')
@bp_live_score_incidents_v209.route('/live-score-pro')
@bp_live_score_incidents_v209.route('/live-incidents-pro')
def page_live_score_v209():
    return render_template('live_score_incidents_v209.html', data=live_score_payload(), admin=False)


@bp_live_score_incidents_v209.route('/admin/live-score')
def admin_live_score_v209():
    return render_template('live_score_incidents_v209.html', data=live_score_payload(), admin=True)
