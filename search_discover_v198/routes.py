from flask import Blueprint, jsonify, request, render_template_string
import os, sqlite3, json, time, re, math
from pathlib import Path

bp_search_discover_v198 = Blueprint('search_discover_v198', __name__)
VERSION = 'V198_SEARCH_DISCOVER_PRO'


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
    cur.execute('''CREATE TABLE IF NOT EXISTS search_discover_logs_v198 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        query TEXT,
        filters_json TEXT,
        results_count INTEGER DEFAULT 0,
        created_at INTEGER
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS search_discover_cache_v198 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cache_key TEXT UNIQUE,
        payload_json TEXT,
        created_at INTEGER,
        updated_at INTEGER
    )''')
    con.commit(); con.close()


def _tables(con):
    try:
        return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    except Exception:
        return set()


def _cols(con, table):
    try:
        return [r[1] for r in con.execute(f'PRAGMA table_info({table})').fetchall()]
    except Exception:
        return []


def _rows(con, table, limit=300):
    if table not in _tables(con):
        return []
    cols = _cols(con, table)
    order = 'rowid DESC'
    for c in ['kickoff','commence_time','start_time','date','updated_at','created_at']:
        if c in cols:
            order = f"COALESCE({c}, '') DESC"; break
    try:
        return [dict(r) for r in con.execute(f'SELECT * FROM {table} ORDER BY {order} LIMIT ?', (int(limit),)).fetchall()]
    except Exception:
        try:
            return [dict(r) for r in con.execute(f'SELECT * FROM {table} LIMIT ?', (int(limit),)).fetchall()]
        except Exception:
            return []


def _pick(row, names, fallback=''):
    lower = {str(k).lower(): k for k in row.keys()}
    for n in names:
        k = lower.get(n.lower())
        if k is not None and row.get(k) not in (None, ''):
            return row.get(k)
    for k in row.keys():
        lk = str(k).lower()
        if any(n.lower() in lk for n in names) and row.get(k) not in (None, ''):
            return row.get(k)
    return fallback


def _safe(v, fb=''):
    v = '' if v is None else str(v).strip()
    return v or fb


def _num(v, fb=0.0):
    try:
        if v in (None, ''): return fb
        return float(str(v).replace('%','').replace(',','.'))
    except Exception:
        return fb


def _norm(s):
    s = str(s or '').lower()
    repl = {'á':'a','é':'e','í':'i','ó':'o','ú':'u','ü':'u','ñ':'n','ç':'c'}
    for a,b in repl.items(): s = s.replace(a,b)
    return re.sub(r'[^a-z0-9]+',' ',s).strip()


def _status_bucket(status):
    s = _norm(status)
    if any(x in s for x in ['live','en vivo','1h','2h','min','playing','inplay','started']): return 'directo'
    if any(x in s for x in ['final','finished','ft','terminado']): return 'finalizado'
    if any(x in s for x in ['postponed','aplazado','cancel']): return 'incidencia'
    return 'proximo'


def _hot_score(item):
    score = 0.0
    score += _num(item.get('confianza'), 0) * 0.45
    score += _num(item.get('shark_score'), 0) * 0.25
    score += _num(item.get('ev'), 0) * 0.8
    if item.get('estado_bucket') == 'directo': score += 18
    if item.get('favorito'): score += 8
    if item.get('tipo') == 'pick': score += 10
    return round(max(0, min(100, score)), 1)


def _identity(kind, name):
    try:
        from team_identity_v197.routes import _identity as ident
        return ident(kind, name)
    except Exception:
        initials = ''.join([p[:1] for p in str(name or 'NE').split()[:2]]).upper() or 'NE'
        return {'nombre': name, 'logo': '/static/team_identity/fallback_league.svg' if kind == 'league' else '/static/team_identity/fallback_team.svg', 'iniciales': initials, 'calidad': 'fallback_premium'}


def _fixtures(limit=500):
    con = _connect(); out = []
    try:
        for table in ['fixtures_cache','fixtures','real_fixtures','matches_cache','matches','events','odds_cache']:
            if table not in _tables(con): continue
            for r in _rows(con, table, limit):
                home = _safe(_pick(r, ['home_team','home','team_home','local','equipo_local'], ''), '')
                away = _safe(_pick(r, ['away_team','away','team_away','visitor','visitante','equipo_visitante'], ''), '')
                if not home and not away: continue
                league = _safe(_pick(r, ['league','competition','competition_name','sport_title','liga'], 'Competición real'), 'Competición real')
                status = _safe(_pick(r, ['status','state','match_status','fixture_status','estado'], 'Programado'), 'Programado')
                kickoff = _safe(_pick(r, ['kickoff','commence_time','start_time','date','hora'], ''), '')
                item = {
                    'tipo':'partido','titulo': f'{home or "Local"} vs {away or "Visitante"}', 'local':home or 'Local', 'visitante':away or 'Visitante',
                    'liga':league,'hora':kickoff,'estado':status,'estado_bucket':_status_bucket(status),'fuente':table,
                    'confianza': _num(_pick(r, ['confidence','confianza','confidence_score','score'], 0), 0),
                    'shark_score': _num(_pick(r, ['shark_score','score_shark','rating'], 0), 0),
                    'ev': _num(_pick(r, ['ev','expected_value','valor'], 0), 0),
                    'url':'/match-center-real',
                    'local_id':_identity('team', home or 'Local'), 'visitante_id':_identity('team', away or 'Visitante'), 'liga_id':_identity('league', league)
                }
                item['hot_score'] = _hot_score(item)
                out.append(item)
    finally:
        con.close()
    seen=set(); clean=[]
    for m in out:
        key=(m['tipo'],m['local'],m['visitante'],m.get('hora',''))
        if key in seen: continue
        seen.add(key); clean.append(m)
    return clean[:limit]


def _picks(limit=500):
    con = _connect(); out = []
    try:
        for table in ['picks','real_picks','pick_history','telegram_picks','bet_picks']:
            if table not in _tables(con): continue
            for r in _rows(con, table, limit):
                title = _safe(_pick(r, ['title','titulo','pick','selection','seleccion','market','mercado'], ''), '')
                home = _safe(_pick(r, ['home_team','home','local','equipo_local'], ''), '')
                away = _safe(_pick(r, ['away_team','away','visitante','equipo_visitante'], ''), '')
                league = _safe(_pick(r, ['league','competition','liga'], 'Pick real'), 'Pick real')
                if not title and (home or away): title = f'Pick · {home} vs {away}'
                if not title: continue
                item = {
                    'tipo':'pick','titulo':title,'local':home,'visitante':away,'liga':league,
                    'hora':_safe(_pick(r, ['kickoff','commence_time','date','created_at','hora'], ''), ''),
                    'estado':_safe(_pick(r, ['status','estado','result'], 'Activo'), 'Activo'),'estado_bucket':_status_bucket(_pick(r, ['status','estado'], 'Activo')),
                    'cuota':_safe(_pick(r, ['odds','cuota','price'], ''), ''), 'mercado':_safe(_pick(r, ['market','mercado'], ''), ''),
                    'confianza':_num(_pick(r, ['confidence','confianza','confidence_score'], 0), 0),
                    'shark_score':_num(_pick(r, ['shark_score','score','rating'], 0), 0),
                    'ev':_num(_pick(r, ['ev','expected_value','valor'], 0), 0),
                    'fuente':table,'url':'/picks'
                }
                item['hot_score'] = _hot_score(item)
                out.append(item)
    finally:
        con.close()
    seen=set(); clean=[]
    for p in out:
        key=(p['tipo'],p['titulo'],p.get('hora',''))
        if key in seen: continue
        seen.add(key); clean.append(p)
    return clean[:limit]


def build_discover(q='', filtro='todo', limit=120):
    _init()
    items = _fixtures(500) + _picks(500)
    query = _norm(q)
    if query:
        words = [w for w in query.split() if w]
        def ok(it):
            hay = _norm(' '.join(str(it.get(k,'')) for k in ['titulo','local','visitante','liga','estado','mercado']))
            return all(w in hay for w in words)
        items = [it for it in items if ok(it)]
    if filtro == 'directo': items = [it for it in items if it.get('estado_bucket') == 'directo']
    elif filtro == 'proximos': items = [it for it in items if it.get('estado_bucket') == 'proximo']
    elif filtro == 'picks': items = [it for it in items if it.get('tipo') == 'pick']
    elif filtro == 'partidos': items = [it for it in items if it.get('tipo') == 'partido']
    elif filtro == 'alta-confianza': items = [it for it in items if _num(it.get('confianza'),0) >= 70 or _num(it.get('hot_score'),0) >= 70]
    elif filtro == 'calientes': items = [it for it in items if _num(it.get('hot_score'),0) >= 55]
    items.sort(key=lambda x: (_num(x.get('hot_score'),0), _num(x.get('confianza'),0)), reverse=True)
    resumen = {
        'total': len(items),
        'partidos': sum(1 for x in items if x.get('tipo') == 'partido'),
        'picks': sum(1 for x in items if x.get('tipo') == 'pick'),
        'directo': sum(1 for x in items if x.get('estado_bucket') == 'directo'),
        'alta_confianza': sum(1 for x in items if _num(x.get('confianza'),0) >= 70 or _num(x.get('hot_score'),0) >= 70),
    }
    try:
        con = _connect()
        con.execute('INSERT INTO search_discover_logs_v198(action,query,filters_json,results_count,created_at) VALUES(?,?,?,?,?)', ('search',q,json.dumps({'filtro':filtro},ensure_ascii=False),len(items),int(time.time())))
        con.commit(); con.close()
    except Exception: pass
    return {'ok': True, 'version': VERSION, 'consulta': q, 'filtro': filtro, 'resumen': resumen, 'resultados': items[:int(limit)]}


@bp_search_discover_v198.route('/api/v198/search-discover')
def api_search():
    return jsonify(build_discover(request.args.get('q',''), request.args.get('filtro','todo'), int(request.args.get('limit',120))))


@bp_search_discover_v198.route('/api/v198/discover/quick')
def api_quick():
    return jsonify({'ok': True, 'version': VERSION, 'bloques': {
        'directo': build_discover('', 'directo', 20)['resultados'],
        'calientes': build_discover('', 'calientes', 20)['resultados'],
        'alta_confianza': build_discover('', 'alta-confianza', 20)['resultados'],
        'picks': build_discover('', 'picks', 20)['resultados'],
    }})


PAGE = r'''
<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Buscar y descubrir · NeMeSiS SHARK PRO</title>
<style>
:root{--bg:#06111f;--card:rgba(11,26,49,.9);--line:rgba(135,210,255,.18);--txt:#f2f8ff;--mut:#9fb7cb;--acc:#6df7ca;--blue:#65b7ff;--gold:#f6d365;--red:#ff6b8a}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 20% 0,#173f6b,#06111f 45%,#02060c);color:var(--txt);font-family:Inter,system-ui,Segoe UI,Arial,sans-serif}.wrap{max-width:1220px;margin:auto;padding:22px}.nav{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:15px}.btn{border:1px solid var(--line);background:rgba(255,255,255,.06);color:var(--txt);padding:10px 14px;border-radius:15px;text-decoration:none;font-weight:900}.btn:hover{background:rgba(109,247,202,.12)}.primary{background:linear-gradient(135deg,var(--acc),var(--blue));color:#04111c}.hero{border:1px solid var(--line);background:linear-gradient(135deg,rgba(17,56,95,.95),rgba(9,23,43,.88));border-radius:32px;padding:26px;box-shadow:0 25px 75px rgba(0,0,0,.35)}h1{font-size:clamp(34px,5vw,62px);line-height:1;margin:10px 0}.mut{color:var(--mut)}.search{display:grid;grid-template-columns:1fr auto;gap:10px;margin-top:18px}.search input{width:100%;border:1px solid var(--line);background:rgba(255,255,255,.08);color:var(--txt);padding:15px 16px;border-radius:18px;font-size:16px;outline:none}.chips{display:flex;gap:10px;flex-wrap:wrap;margin:16px 0}.chip{border:1px solid var(--line);background:rgba(255,255,255,.05);padding:9px 13px;border-radius:999px;color:#cfe8ff;text-decoration:none;font-weight:900}.chip.active{background:rgba(109,247,202,.16);color:var(--acc)}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin:17px 0}.stat{border:1px solid var(--line);background:rgba(255,255,255,.05);border-radius:22px;padding:16px}.stat b{font-size:27px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:16px}.card{border:1px solid var(--line);background:var(--card);border-radius:26px;padding:18px;position:relative;overflow:hidden}.card:before{content:"";position:absolute;inset:-60% -20% auto auto;width:180px;height:180px;background:radial-gradient(circle,rgba(109,247,202,.15),transparent 65%)}.top{display:flex;justify-content:space-between;gap:12px;align-items:center}.tag{border:1px solid var(--line);border-radius:999px;padding:6px 9px;font-size:12px;font-weight:950;color:var(--acc)}.tag.pick{color:var(--gold)}.score{font-weight:950;color:var(--gold)}.teams{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:10px;margin:14px 0}.team{text-align:center}.logo{width:58px;height:58px;object-fit:contain;border-radius:18px;border:1px solid var(--line);background:rgba(255,255,255,.08);padding:7px}.vs{font-weight:950;color:#d9edff}.title{font-size:18px;font-weight:950;margin:10px 0}.meta{color:var(--mut);font-size:13px;line-height:1.55}.bar{height:8px;background:rgba(255,255,255,.08);border-radius:999px;margin:12px 0;overflow:hidden}.fill{height:100%;background:linear-gradient(90deg,var(--blue),var(--acc),var(--gold));border-radius:999px}.empty{padding:24px;border:1px dashed var(--line);border-radius:24px;background:rgba(255,255,255,.04);margin-top:16px}.quick{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-top:18px}.quick a{border:1px solid var(--line);background:rgba(255,255,255,.06);border-radius:20px;padding:15px;text-decoration:none;color:var(--txt);font-weight:950}.quick small{display:block;color:var(--mut);font-weight:700;margin-top:4px}@media(max-width:650px){.search{grid-template-columns:1fr}.wrap{padding:14px}.hero{padding:20px;border-radius:24px}}
</style></head><body><div class="wrap">
<div class="nav"><a class="btn" href="javascript:history.back()">← Atrás</a><a class="btn" href="javascript:history.forward()">Adelante →</a><a class="btn" href="/cliente/pro">Inicio cliente</a><a class="btn" href="/cliente/favoritos">Favoritos</a></div>
<section class="hero"><span class="tag">V198 · SEARCH + DISCOVER PRO</span><h1>Buscar y descubrir partidos reales</h1><p class="mut">Buscador global en español para encontrar equipos, ligas, partidos, picks, directos y oportunidades destacadas sin mostrar datos inventados.</p>
<form class="search" method="get"><input name="q" value="{{q}}" placeholder="Buscar equipo, liga, partido o mercado…"><input type="hidden" name="filtro" value="{{filtro}}"><button class="btn primary" type="submit">Buscar</button></form>
<div class="quick"><a href="?filtro=directo">🔴 En directo<small>Partidos live reales</small></a><a href="?filtro=calientes">🔥 Más calientes<small>Mayor actividad o interés</small></a><a href="?filtro=alta-confianza">🧠 Alta confianza<small>Mejor lectura visual</small></a><a href="?filtro=picks">🎯 Picks<small>Selecciones reales</small></a></div></section>
<div class="chips">{% for key,label in filtros %}<a class="chip {% if filtro==key %}active{% endif %}" href="?q={{q}}&filtro={{key}}">{{label}}</a>{% endfor %}</div>
<div class="stats"><div class="stat"><b>{{resumen.total}}</b><div class="mut">Resultados</div></div><div class="stat"><b>{{resumen.partidos}}</b><div class="mut">Partidos</div></div><div class="stat"><b>{{resumen.picks}}</b><div class="mut">Picks</div></div><div class="stat"><b>{{resumen.directo}}</b><div class="mut">En directo</div></div></div>
{% if resultados %}<div class="grid">{% for r in resultados %}<article class="card"><div class="top"><span class="tag {% if r.tipo=='pick' %}pick{% endif %}">{{'Pick real' if r.tipo=='pick' else 'Partido real'}}</span><span class="score">Interés {{r.hot_score|round(0)}}/100</span></div>{% if r.tipo=='partido' %}<div class="teams"><div class="team"><img class="logo" src="{{r.local_id.logo}}" onerror="this.src='/static/team_identity/fallback_team.svg'"><strong>{{r.local}}</strong></div><div class="vs">VS</div><div class="team"><img class="logo" src="{{r.visitante_id.logo}}" onerror="this.src='/static/team_identity/fallback_team.svg'"><strong>{{r.visitante}}</strong></div></div>{% else %}<div class="title">{{r.titulo}}</div>{% endif %}<div class="meta"><b>{{r.liga}}</b><br>{{r.estado}} · {{r.hora or 'Hora pendiente'}}{% if r.cuota %}<br>Cuota: {{r.cuota}}{% endif %}{% if r.mercado %}<br>Mercado: {{r.mercado}}{% endif %}</div><div class="bar"><div class="fill" style="width:{{[r.hot_score,100]|min}}%"></div></div><a class="btn" href="{{r.url}}">Abrir</a></article>{% endfor %}</div>{% else %}<div class="empty">No hay resultados reales para esta búsqueda. No se muestran partidos, picks ni cuotas inventadas.</div>{% endif %}
</div></body></html>
'''


@bp_search_discover_v198.route('/cliente/buscar')
@bp_search_discover_v198.route('/cliente/discover')
@bp_search_discover_v198.route('/search-discover-pro')
def page_client():
    q = request.args.get('q','').strip(); filtro = request.args.get('filtro','todo')
    data = build_discover(q, filtro, 120)
    filtros = [('todo','Todo'),('directo','En directo'),('proximos','Próximos'),('partidos','Partidos'),('picks','Picks'),('calientes','Calientes'),('alta-confianza','Alta confianza')]
    return render_template_string(PAGE, q=q, filtro=filtro, resumen=data['resumen'], resultados=data['resultados'], filtros=filtros)


@bp_search_discover_v198.route('/admin/search-discover')
def page_admin():
    data = build_discover(request.args.get('q',''), request.args.get('filtro','todo'), 200)
    html = PAGE + '<pre style="max-width:1220px;margin:20px auto;color:#cff;background:#06111f;border:1px solid rgba(135,210,255,.18);border-radius:18px;padding:16px;white-space:pre-wrap">{{debug}}</pre>'
    return render_template_string(html, q=request.args.get('q',''), filtro=request.args.get('filtro','todo'), resumen=data['resumen'], resultados=data['resultados'], filtros=[('todo','Todo'),('directo','En directo'),('proximos','Próximos'),('partidos','Partidos'),('picks','Picks'),('calientes','Calientes'),('alta-confianza','Alta confianza')], debug=json.dumps(data['resumen'], ensure_ascii=False, indent=2))
