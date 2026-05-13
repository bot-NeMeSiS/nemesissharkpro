from flask import Blueprint, jsonify, request, render_template_string, url_for
import os, sqlite3, json, hashlib, time, re
from pathlib import Path

bp_team_identity_v197 = Blueprint('team_identity_v197', __name__)
VERSION = 'V197_TEAM_IDENTITY_ENGINE_PRO'


def _db_path():
    for p in [os.environ.get('DATABASE_PATH'), os.environ.get('DB_PATH'), '/data/database.db', '/data/app.db', 'database.db', 'app.db']:
        if p:
            try:
                if str(p).startswith('/data'):
                    Path(p).parent.mkdir(parents=True, exist_ok=True)
                if Path(p).exists() or str(p).startswith('/data'):
                    return p
            except Exception:
                pass
    return 'database.db'


def _connect():
    con = sqlite3.connect(_db_path())
    con.row_factory = sqlite3.Row
    return con


def _init():
    con = _connect(); cur = con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS team_identity_cache_v197 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kind TEXT NOT NULL,
        name TEXT NOT NULL,
        slug TEXT NOT NULL,
        logo_url TEXT,
        flag_url TEXT,
        country TEXT,
        source TEXT,
        quality TEXT DEFAULT 'fallback',
        payload_json TEXT,
        created_at INTEGER,
        updated_at INTEGER,
        UNIQUE(kind, slug)
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS team_identity_audit_v197 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        status TEXT,
        total INTEGER DEFAULT 0,
        resolved INTEGER DEFAULT 0,
        fallback INTEGER DEFAULT 0,
        detail TEXT,
        created_at INTEGER
    )''')
    con.commit(); con.close()


def _tables(con):
    try: return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    except Exception: return set()


def _cols(con, table):
    try: return [r[1] for r in con.execute(f'PRAGMA table_info({table})').fetchall()]
    except Exception: return []


def _rows(con, table, limit=300):
    if table not in _tables(con): return []
    cols = _cols(con, table)
    order = 'rowid DESC'
    for c in ['updated_at','created_at','kickoff','commence_time','date']:
        if c in cols:
            order = f"COALESCE({c}, '') DESC"; break
    try: return [dict(r) for r in con.execute(f'SELECT * FROM {table} ORDER BY {order} LIMIT ?', (int(limit),)).fetchall()]
    except Exception:
        try: return [dict(r) for r in con.execute(f'SELECT * FROM {table} LIMIT ?', (int(limit),)).fetchall()]
        except Exception: return []


def _pick(row, names, fallback=''):
    lower = {str(k).lower(): k for k in row.keys()}
    for n in names:
        k = lower.get(n.lower())
        if k is not None and row.get(k) not in (None, ''): return row.get(k)
    for k in row.keys():
        lk = str(k).lower()
        if any(n.lower() in lk for n in names) and row.get(k) not in (None, ''): return row.get(k)
    return fallback


def _safe(v, fb=''):
    v = '' if v is None else str(v).strip()
    return v or fb


def _slug(name):
    s = str(name or '').strip().lower()
    repl = {'á':'a','é':'e','í':'i','ó':'o','ú':'u','ü':'u','ñ':'n','ç':'c'}
    for a,b in repl.items(): s = s.replace(a,b)
    s = re.sub(r'[^a-z0-9]+','-',s).strip('-')
    return s or hashlib.md5(str(name).encode()).hexdigest()[:10]


def _initials(name):
    parts = [p for p in re.split(r'\s+', str(name or '').strip()) if p]
    if not parts: return 'NE'
    if len(parts) == 1: return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def _static_fallback(kind):
    return '/static/team_identity/fallback_league.svg' if kind == 'league' else '/static/team_identity/fallback_team.svg'


def _extract_logo(row, kind):
    names = ['logo','logo_url','badge','badge_url','crest','crest_url','team_logo','home_logo','away_logo','league_logo','competition_logo','emblem','image','image_url']
    value = _safe(_pick(row, names, ''), '')
    if value and (value.startswith('http') or value.startswith('/static') or value.startswith('data:')): return value
    return ''


def _extract_flag(row):
    value = _safe(_pick(row, ['flag','flag_url','country_flag','bandera'], ''), '')
    if value and (value.startswith('http') or value.startswith('/static') or value.startswith('data:')): return value
    return ''


def _upsert_identity(con, kind, name, source, row=None):
    name = _safe(name, 'Equipo real' if kind == 'team' else 'Competición real')
    slug = _slug(name)
    row = row or {}
    logo = _extract_logo(row, kind)
    flag = _extract_flag(row)
    country = _safe(_pick(row, ['country','pais','nation','area'], ''), '')
    quality = 'real_logo' if logo else 'fallback_premium'
    payload = json.dumps({'iniciales': _initials(name), 'fuente_original': source}, ensure_ascii=False)
    now = int(time.time())
    con.execute('''INSERT INTO team_identity_cache_v197(kind,name,slug,logo_url,flag_url,country,source,quality,payload_json,created_at,updated_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(kind, slug) DO UPDATE SET
                   name=excluded.name,
                   logo_url=COALESCE(NULLIF(excluded.logo_url,''), team_identity_cache_v197.logo_url),
                   flag_url=COALESCE(NULLIF(excluded.flag_url,''), team_identity_cache_v197.flag_url),
                   country=COALESCE(NULLIF(excluded.country,''), team_identity_cache_v197.country),
                   source=excluded.source,
                   quality=CASE WHEN excluded.logo_url IS NOT NULL AND excluded.logo_url != '' THEN 'real_logo' ELSE team_identity_cache_v197.quality END,
                   payload_json=excluded.payload_json,
                   updated_at=excluded.updated_at''',
                (kind,name,slug,logo,flag,country,source,quality,payload,now,now))


def sync_team_identity():
    _init(); con = _connect(); total = 0
    candidates = ['fixtures_cache','fixtures','real_fixtures','matches_cache','matches','events','picks','real_picks','odds_cache']
    try:
        for table in candidates:
            if table not in _tables(con): continue
            for r in _rows(con, table, 600):
                home = _pick(r, ['home_team','home','team_home','local','equipo_local'], '')
                away = _pick(r, ['away_team','away','team_away','visitor','visitante','equipo_visitante'], '')
                team = _pick(r, ['team','team_name','equipo'], '')
                league = _pick(r, ['league','competition','competition_name','sport_title','liga'], '')
                for n in [home, away, team]:
                    if _safe(n): _upsert_identity(con, 'team', n, table, r); total += 1
                if _safe(league): _upsert_identity(con, 'league', league, table, r); total += 1
        con.commit()
        rows = con.execute('SELECT quality, COUNT(*) c FROM team_identity_cache_v197 GROUP BY quality').fetchall()
        stats = {r['quality']: r['c'] for r in rows}
        resolved = int(stats.get('real_logo', 0)); fallback = int(stats.get('fallback_premium', 0))
        con.execute('INSERT INTO team_identity_audit_v197(action,status,total,resolved,fallback,detail,created_at) VALUES(?,?,?,?,?,?,?)',
                    ('sync','ok', total, resolved, fallback, 'sin logos inventados; fallback visual seguro', int(time.time())))
        con.commit()
        return {'ok': True, 'version': VERSION, 'procesados': total, 'logos_reales': resolved, 'fallback_premium': fallback}
    except Exception as e:
        try:
            con.execute('INSERT INTO team_identity_audit_v197(action,status,detail,created_at) VALUES(?,?,?,?)', ('sync','error',str(e),int(time.time()))); con.commit()
        except Exception: pass
        return {'ok': False, 'version': VERSION, 'error': str(e)}
    finally:
        con.close()


def _identity(kind, name):
    _init(); con = _connect()
    try:
        slug = _slug(name)
        row = con.execute('SELECT * FROM team_identity_cache_v197 WHERE kind=? AND slug=?', (kind, slug)).fetchone()
        if not row:
            _upsert_identity(con, kind, name, 'fallback_runtime', {})
            con.commit()
            row = con.execute('SELECT * FROM team_identity_cache_v197 WHERE kind=? AND slug=?', (kind, slug)).fetchone()
        d = dict(row)
        payload = {}
        try: payload = json.loads(d.get('payload_json') or '{}')
        except Exception: payload = {}
        logo = d.get('logo_url') or _static_fallback(kind)
        return {'kind': kind, 'nombre': d.get('name') or name, 'slug': d.get('slug') or slug, 'logo': logo, 'bandera': d.get('flag_url') or '', 'pais': d.get('country') or '', 'calidad': d.get('quality') or 'fallback_premium', 'iniciales': payload.get('iniciales') or _initials(name), 'fuente': d.get('source') or 'fallback'}
    finally:
        con.close()


def _fixtures_with_identity(limit=80):
    sync_team_identity()
    con = _connect(); matches = []
    try:
        for table in ['fixtures_cache','fixtures','real_fixtures','matches_cache','matches','events']:
            if table not in _tables(con): continue
            for r in _rows(con, table, limit):
                home = _safe(_pick(r, ['home_team','home','team_home','local','equipo_local'], 'Local'), 'Local')
                away = _safe(_pick(r, ['away_team','away','team_away','visitor','visitante','equipo_visitante'], 'Visitante'), 'Visitante')
                league = _safe(_pick(r, ['league','competition','competition_name','sport_title','liga'], 'Competición real'), 'Competición real')
                kickoff = _safe(_pick(r, ['kickoff','commence_time','start_time','date','hora'], ''), '')
                status = _safe(_pick(r, ['status','state','match_status','fixture_status','estado'], 'Programado'), 'Programado')
                matches.append({'local':home,'visitante':away,'liga':league,'hora':kickoff,'estado':status,'fuente':table,
                                'local_id':_identity('team', home),'visitante_id':_identity('team', away),'liga_id':_identity('league', league)})
        seen=[]; clean=[]
        for m in matches:
            key=(m['local'],m['visitante'],m['hora'])
            if key not in seen: seen.append(key); clean.append(m)
        return clean[:limit]
    finally:
        con.close()


@bp_team_identity_v197.route('/api/v197/team-identity/sync')
def api_sync():
    return jsonify(sync_team_identity())


@bp_team_identity_v197.route('/api/v197/team-identity/resolve')
def api_resolve():
    kind = request.args.get('kind','team')
    if kind not in ['team','league']: kind = 'team'
    name = request.args.get('name','')
    return jsonify({'ok': True, 'version': VERSION, 'identidad': _identity(kind, name)})


@bp_team_identity_v197.route('/api/v197/team-identity/matches')
def api_matches():
    return jsonify({'ok': True, 'version': VERSION, 'partidos': _fixtures_with_identity(120)})


PAGE = r'''
<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Identidad visual de equipos · NeMeSiS SHARK PRO</title>
<style>
:root{--bg:#07111f;--card:rgba(12,28,52,.88);--line:rgba(135,210,255,.18);--txt:#eff8ff;--mut:#9fb5c9;--acc:#6df7ca;--gold:#f6d365}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top left,#123c67,#07111f 48%,#03070d);color:var(--txt);font-family:Inter,system-ui,Segoe UI,Arial,sans-serif}.wrap{max-width:1180px;margin:auto;padding:24px}.nav{display:flex;gap:10px;margin-bottom:16px}.btn{border:1px solid var(--line);background:rgba(255,255,255,.06);color:var(--txt);padding:10px 14px;border-radius:15px;text-decoration:none;font-weight:800}.btn.primary{background:linear-gradient(135deg,#6df7ca,#5ab5ff);color:#04111c}h1{font-size:clamp(34px,5vw,64px);margin:8px 0}.hero{border:1px solid var(--line);background:linear-gradient(135deg,rgba(18,56,92,.95),rgba(15,26,51,.86));border-radius:32px;padding:28px;box-shadow:0 25px 80px rgba(0,0,0,.35)}.mut{color:var(--mut)}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;margin-top:18px}.match{border:1px solid var(--line);background:var(--card);border-radius:24px;padding:18px}.teams{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:12px}.team{text-align:center}.logo{width:70px;height:70px;border-radius:22px;object-fit:contain;background:rgba(255,255,255,.08);border:1px solid var(--line);padding:8px}.vs{font-weight:950;color:var(--gold)}.league{display:flex;align-items:center;gap:8px;margin-bottom:12px;color:#cfe7ff;font-weight:800}.league img{width:24px;height:24px;border-radius:8px}.badge{display:inline-flex;margin-top:10px;border:1px solid var(--line);border-radius:999px;padding:6px 9px;color:var(--acc);font-size:12px;font-weight:900}.quality{color:var(--mut);font-size:12px;margin-top:4px}.empty{padding:22px;border:1px dashed var(--line);border-radius:22px;background:rgba(255,255,255,.04);margin-top:18px}.top{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;align-items:center}.pill{border:1px solid var(--line);padding:8px 12px;border-radius:999px;color:#bfe9ff;font-weight:800}
</style></head><body><div class="wrap">
<div class="nav"><a class="btn" href="javascript:history.back()">← Atrás</a><a class="btn" href="javascript:history.forward()">Adelante →</a><a class="btn" href="/cliente/pro">Inicio cliente</a></div>
<section class="hero"><div class="top"><span class="pill">V197 · TEAM IDENTITY ENGINE PRO</span><a class="btn primary" href="/api/v197/team-identity/sync">Sincronizar identidad</a></div><h1>Escudos, ligas y branding real</h1><p class="mut">Motor visual para mostrar logos reales cuando vienen del proveedor. Si no existe escudo real, se usa fallback premium seguro sin inventar datos.</p></section>
{% if partidos %}<div class="grid">{% for m in partidos %}<article class="match"><div class="league"><img src="{{m.liga_id.logo}}" onerror="this.src='/static/team_identity/fallback_league.svg'"><span>{{m.liga}}</span></div><div class="teams"><div class="team"><img class="logo" src="{{m.local_id.logo}}" onerror="this.src='/static/team_identity/fallback_team.svg'"><strong>{{m.local}}</strong><div class="quality">{{m.local_id.calidad.replace('_',' ')}}</div></div><div class="vs">VS</div><div class="team"><img class="logo" src="{{m.visitante_id.logo}}" onerror="this.src='/static/team_identity/fallback_team.svg'"><strong>{{m.visitante}}</strong><div class="quality">{{m.visitante_id.calidad.replace('_',' ')}}</div></div></div><span class="badge">{{m.estado}}</span><span class="badge">{{m.hora or 'Hora pendiente'}}</span></article>{% endfor %}</div>{% else %}<div class="empty">No hay partidos reales en caché ahora mismo. El motor queda preparado y no muestra escudos ni partidos inventados.</div>{% endif %}
</div></body></html>
'''


@bp_team_identity_v197.route('/cliente/team-identity')
@bp_team_identity_v197.route('/team-identity-pro')
def page_client():
    return render_template_string(PAGE, partidos=_fixtures_with_identity(80))


@bp_team_identity_v197.route('/admin/team-identity')
def page_admin():
    data = sync_team_identity()
    return render_template_string(PAGE + '<pre style="max-width:1180px;margin:20px auto;color:#cff;background:#07111f;border:1px solid rgba(135,210,255,.18);border-radius:18px;padding:16px">{{data}}</pre>', partidos=_fixtures_with_identity(80), data=json.dumps(data, ensure_ascii=False, indent=2))
