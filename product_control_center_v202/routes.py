from flask import Blueprint, jsonify, render_template_string, request
import os, sqlite3, json, time
from pathlib import Path

bp_product_control_center_v202 = Blueprint('product_control_center_v202', __name__)
VERSION = 'V202_SMART_PRODUCT_CONTROL_CENTER_PRO'

CORE_TABLES = {
    'fixtures': ['fixtures', 'real_fixtures', 'fixtures_cache', 'fixtures_v146', 'fixtures_real_v146'],
    'picks': ['picks', 'real_picks', 'picks_history', 'pick_lifecycle_v190'],
    'usuarios': ['users', 'usuarios', 'user_profiles'],
    'favoritos': ['favorites', 'favorites_pro', 'user_favorites_v150'],
    'snapshots': ['data_snapshots_v190', 'match_snapshots_v190', 'historical_snapshots_v190'],
    'ml_dataset': ['ml_training_rows_v200', 'ml_feature_store_v189', 'ml_datasets_v189'],
    'ml_explicaciones': ['ml_explanations_v201', 'ml_audit_runs_v201'],
    'telegram': ['telegram_logs', 'telegram_dispatch_v191', 'telegram_alerts'],
    'automatizacion': ['automation_runs_v191', 'automation_jobs_v191'],
    'identidad_equipos': ['team_identity_cache_v197', 'team_identity_v197']
}

ENV_CHECKS = [
    ('DATABASE_PATH', 'Base de datos persistente'),
    ('DB_PATH', 'Ruta alternativa de base de datos'),
    ('THE_ODDS_API_KEY', 'The Odds API'),
    ('ODDS_API_KEY', 'The Odds API alternativa'),
    ('TELEGRAM_BOT_TOKEN', 'Telegram Bot'),
    ('TELEGRAM_ADMIN_CHAT_ID', 'Telegram admin'),
    ('OPENAI_API_KEY', 'SHARK AI externo opcional'),
]


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


def _now():
    return int(time.time())


def init_control_center():
    con = _connect(); cur = con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS product_control_snapshots_v202 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        version TEXT,
        health_score REAL DEFAULT 0,
        status TEXT,
        summary_json TEXT,
        created_at INTEGER
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS product_control_checks_v202 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        area TEXT,
        status TEXT,
        message TEXT,
        details_json TEXT,
        created_at INTEGER
    )''')
    con.commit(); con.close()


def _safe_count(cur, table):
    try:
        cur.execute(f'SELECT COUNT(*) c FROM "{table}"')
        return int(cur.fetchone()['c'])
    except Exception:
        return None


def _existing_tables(cur):
    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return {r['name'] for r in cur.fetchall()}
    except Exception:
        return set()


def _table_groups():
    con = _connect(); cur = con.cursor()
    existing = _existing_tables(cur)
    groups = {}
    total_rows = 0
    try:
        for area, candidates in CORE_TABLES.items():
            found = []
            for t in candidates:
                if t in existing:
                    c = _safe_count(cur, t)
                    found.append({'tabla': t, 'filas': c if c is not None else 0})
                    if c:
                        total_rows += c
            groups[area] = {'ok': bool(found), 'tablas': found, 'filas': sum(x['filas'] for x in found)}
    finally:
        con.close()
    return groups, total_rows


def _env_status():
    items = []
    for key, label in ENV_CHECKS:
        val = os.environ.get(key)
        items.append({
            'clave': key,
            'nombre': label,
            'configurado': bool(val),
            'estado': 'ok' if val else 'pendiente',
            'valor': 'Configurado' if val else 'No configurado'
        })
    return items


def _file_status():
    checks = [
        ('app.py', 'Aplicación principal'),
        ('requirements.txt', 'Dependencias'),
        ('render.yaml', 'Render'),
        ('Procfile', 'Procfile'),
        ('manifest.json', 'PWA manifest'),
        ('service-worker.js', 'Service Worker'),
    ]
    base = Path.cwd()
    items = []
    for fname, label in checks:
        p = base / fname
        if not p.exists():
            # cuando Flask arranca desde otro cwd, comprobar junto a este módulo
            p = Path(__file__).resolve().parents[1] / fname
        items.append({'archivo': fname, 'nombre': label, 'ok': p.exists(), 'peso_kb': round(p.stat().st_size/1024, 1) if p.exists() else 0})
    return items


def _route_map():
    routes = [
        ('Cliente premium', '/cliente/pro'),
        ('Partidos reales', '/fixtures/today-pro'),
        ('Match Center', '/match-center-real'),
        ('Live Depth', '/cliente/live-depth'),
        ('Estadísticas avanzadas', '/cliente/advanced-stats'),
        ('Búsqueda y descubrir', '/cliente/descubrir'),
        ('SHARK AI real', '/cliente/shark-ai-real'),
        ('ML real', '/cliente/ml-real'),
        ('ML explicado', '/cliente/ml-explicado'),
        ('Eventos live', '/cliente/live-events-real'),
        ('Identidad equipos', '/cliente/team-identity'),
        ('Admin datos', '/admin/data-engine'),
        ('Admin automatización', '/admin/automation-engine'),
        ('Admin ML', '/admin/ml-real'),
        ('Centro de control', '/admin/control-center'),
    ]
    return [{'nombre': n, 'ruta': r} for n, r in routes]


def _recommendations(groups, envs):
    recs = []
    if not groups.get('fixtures', {}).get('ok'):
        recs.append('Sin tabla de fixtures detectada: ejecutar sincronización de partidos reales antes de analizar live/ML.')
    if not groups.get('snapshots', {}).get('ok'):
        recs.append('Sin snapshots históricos detectados: activar V190/V191 para mejorar ML y tendencias.')
    if not groups.get('ml_dataset', {}).get('ok'):
        recs.append('Dataset ML no detectado: generar dataset V200 cuando haya datos suficientes.')
    if not any(e['clave'] in ('THE_ODDS_API_KEY','ODDS_API_KEY') and e['configurado'] for e in envs):
        recs.append('The Odds API no aparece configurada en variables: los datos reales dependerán de caché o de otros conectores.')
    if not any(e['clave']=='TELEGRAM_BOT_TOKEN' and e['configurado'] for e in envs):
        recs.append('Telegram Bot no aparece configurado: el centro lo marca como pendiente, no como fallo crítico.')
    if not recs:
        recs.append('Sistema listo: seguir acumulando datos reales para mejorar automatización, ML y experiencia live.')
    return recs[:6]


def build_control_snapshot(persist=False):
    init_control_center()
    groups, total_rows = _table_groups()
    envs = _env_status()
    files = _file_status()
    routes = _route_map()
    ok_groups = sum(1 for g in groups.values() if g.get('ok'))
    ok_env_core = sum(1 for e in envs if e['configurado'] and e['clave'] in ('DATABASE_PATH','DB_PATH','THE_ODDS_API_KEY','ODDS_API_KEY','TELEGRAM_BOT_TOKEN','OPENAI_API_KEY'))
    ok_files = sum(1 for f in files if f['ok'])
    # Puntuación prudente: no es calidad deportiva ni promesa comercial; solo salud técnica visible.
    score = round(min(100, (ok_groups / max(1, len(groups))) * 55 + (ok_files / max(1, len(files))) * 25 + min(20, ok_env_core * 4)), 1)
    status = 'óptimo' if score >= 82 else 'estable' if score >= 62 else 'revisar'
    payload = {
        'ok': True,
        'version': VERSION,
        'idioma': 'español',
        'estado': status,
        'salud_producto': score,
        'filas_detectadas': total_rows,
        'areas_datos': groups,
        'variables': envs,
        'archivos': files,
        'rutas_clave': routes,
        'recomendaciones': _recommendations(groups, envs),
        'nota': 'Centro de control real: solo muestra datos detectados/configurados, sin inventar partidos, picks, resultados ni predicciones.',
        'timestamp': _now()
    }
    if persist:
        con = _connect(); cur = con.cursor()
        cur.execute('INSERT INTO product_control_snapshots_v202(version,health_score,status,summary_json,created_at) VALUES(?,?,?,?,?)', (
            VERSION, score, status, json.dumps(payload, ensure_ascii=False), _now()
        ))
        con.commit(); con.close()
    return payload


def _latest_snapshots(limit=8):
    init_control_center()
    con = _connect(); cur = con.cursor(); rows=[]
    try:
        cur.execute('SELECT * FROM product_control_snapshots_v202 ORDER BY id DESC LIMIT ?', (limit,))
        for r in cur.fetchall():
            d = dict(r)
            try: d['summary'] = json.loads(d.get('summary_json') or '{}')
            except Exception: d['summary'] = {}
            rows.append(d)
    finally:
        con.close()
    return rows


@bp_product_control_center_v202.route('/api/v202/control-center/status')
def api_status():
    persist = request.args.get('persist') in ('1','true','si','sí')
    return jsonify(build_control_snapshot(persist=persist))


@bp_product_control_center_v202.route('/api/v202/control-center/snapshot', methods=['GET','POST'])
def api_snapshot():
    return jsonify(build_control_snapshot(persist=True))


PAGE = '''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Centro de Control V202 · NeMeSiS SHARK PRO</title><style>
:root{--bg:#030812;--card:rgba(8,21,39,.92);--card2:rgba(255,255,255,.055);--line:rgba(117,215,255,.18);--txt:#f4f8ff;--mut:#9fb5ce;--acc:#70ffd2;--blue:#66b8ff;--gold:#f9d56c;--red:#ff6d8e}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 12% -5%,#143e69 0,#071222 42%,#02050a 100%);font-family:Inter,system-ui,Segoe UI,Arial,sans-serif;color:var(--txt)}.wrap{max-width:1240px;margin:auto;padding:22px}.nav{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px}.btn{border:1px solid var(--line);background:rgba(255,255,255,.06);color:var(--txt);padding:10px 14px;border-radius:16px;text-decoration:none;font-weight:950}.primary{background:linear-gradient(135deg,var(--acc),var(--blue));color:#02101b}.hero,.card{border:1px solid var(--line);background:linear-gradient(135deg,rgba(18,53,91,.94),rgba(7,18,35,.88));border-radius:30px;padding:24px;box-shadow:0 24px 70px rgba(0,0,0,.35)}h1{font-size:clamp(34px,5vw,62px);line-height:.98;margin:10px 0}h2{margin:0 0 12px}.mut{color:var(--mut)}.tag{display:inline-flex;border:1px solid var(--line);border-radius:999px;padding:7px 10px;color:var(--acc);font-weight:950}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px;margin-top:16px}.kpi,.item{border:1px solid var(--line);background:var(--card2);border-radius:22px;padding:16px}.kpi b{font-size:34px;color:var(--gold)}.two{display:grid;grid-template-columns:1.05fr .95fr;gap:14px;margin-top:16px}.area{display:flex;justify-content:space-between;gap:10px;align-items:center;border:1px solid var(--line);background:rgba(255,255,255,.045);border-radius:18px;padding:12px;margin:10px 0}.pill{border:1px solid var(--line);border-radius:999px;padding:7px 10px;font-weight:950}.ok{color:var(--acc)}.warn{color:var(--gold)}.bad{color:var(--red)}.bar{height:10px;border-radius:99px;background:rgba(255,255,255,.08);overflow:hidden;margin-top:12px}.fill{height:100%;background:linear-gradient(90deg,var(--acc),var(--blue),var(--gold));border-radius:99px}.routes{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px}.route{display:block;text-decoration:none;color:var(--txt);border:1px solid var(--line);background:rgba(255,255,255,.045);border-radius:16px;padding:12px}.route small{display:block;color:var(--mut);margin-top:4px}.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}ul{margin:8px 0 0 18px;padding:0}.mini{font-size:12px;color:var(--mut)}@media(max-width:850px){.wrap{padding:14px}.two{grid-template-columns:1fr}.hero{border-radius:24px}.area{display:block}.pill{display:inline-flex;margin-top:8px}}
</style></head><body><div class="wrap"><div class="nav"><a class="btn" href="javascript:history.back()">← Atrás</a><a class="btn" href="javascript:history.forward()">Adelante →</a><a class="btn" href="/cliente/pro">Inicio cliente</a><a class="btn" href="/admin/data-engine">Datos</a><a class="btn" href="/admin/ml-real">ML</a><a class="btn" href="/admin/automation-engine">Automatización</a></div><section class="hero"><span class="tag">V202 · SMART PRODUCT CONTROL CENTER PRO</span><h1>Centro de control del producto</h1><p class="mut">Vista admin para revisar estado real del ecosistema: datos, caché, ML, Telegram, automatización, PWA, rutas clave y salud técnica. No inventa métricas deportivas ni muestra claves privadas.</p><div class="actions"><a class="btn primary" href="?snapshot=1">Guardar snapshot real</a><a class="btn" href="/api/v202/control-center/status">API estado</a><a class="btn" href="/api/v202/control-center/snapshot">API snapshot</a></div></section><div class="grid"><div class="kpi"><b>{{data.salud_producto}}</b><div class="mut">Salud técnica /100</div><div class="bar"><div class="fill" style="width:{{data.salud_producto}}%"></div></div></div><div class="kpi"><b>{{data.estado}}</b><div class="mut">Estado general</div></div><div class="kpi"><b>{{data.filas_detectadas}}</b><div class="mut">Filas reales detectadas</div></div><div class="kpi"><b>{{snapshots|length}}</b><div class="mut">Snapshots V202 guardados</div></div></div><div class="two"><section class="card"><h2>Áreas de datos</h2>{% for name,g in data.areas_datos.items() %}<div class="area"><div><b>{{name.replace('_',' ')|title}}</b><div class="mini">{% if g.tablas %}{% for t in g.tablas %}{{t.tabla}}: {{t.filas}} filas{% if not loop.last %} · {% endif %}{% endfor %}{% else %}No detectado todavía{% endif %}</div></div><span class="pill {% if g.ok %}ok{% else %}warn{% endif %}">{% if g.ok %}Activo{% else %}Pendiente{% endif %}</span></div>{% endfor %}</section><section class="card"><h2>Variables y archivos</h2>{% for e in data.variables %}<div class="area"><div><b>{{e.nombre}}</b><div class="mini">{{e.clave}}</div></div><span class="pill {% if e.configurado %}ok{% else %}warn{% endif %}">{{e.valor}}</span></div>{% endfor %}<h2 style="margin-top:18px">Archivos base</h2>{% for f in data.archivos %}<div class="area"><div><b>{{f.nombre}}</b><div class="mini">{{f.archivo}} · {{f.peso_kb}} KB</div></div><span class="pill {% if f.ok %}ok{% else %}bad{% endif %}">{% if f.ok %}OK{% else %}Falta{% endif %}</span></div>{% endfor %}</section></div><section class="card" style="margin-top:16px"><h2>Recomendaciones reales</h2><ul>{% for r in data.recomendaciones %}<li>{{r}}</li>{% endfor %}</ul><p class="mut">{{data.nota}}</p></section><section class="card" style="margin-top:16px"><h2>Rutas clave del ecosistema</h2><div class="routes">{% for r in data.rutas_clave %}<a class="route" href="{{r.ruta}}"><b>{{r.nombre}}</b><small>{{r.ruta}}</small></a>{% endfor %}</div></section>{% if snapshots %}<section class="card" style="margin-top:16px"><h2>Últimos snapshots V202</h2>{% for s in snapshots %}<div class="area"><div><b>{{s.status}}</b><div class="mini">Score {{s.health_score}} · {{s.created_at}}</div></div><span class="pill ok">Guardado</span></div>{% endfor %}</section>{% endif %}</div></body></html>'''


@bp_product_control_center_v202.route('/admin/control-center')
@bp_product_control_center_v202.route('/admin/product-control')
@bp_product_control_center_v202.route('/control-center-pro')
def page_admin():
    persist = request.args.get('snapshot') == '1'
    data = build_control_snapshot(persist=persist)
    return render_template_string(PAGE, data=data, snapshots=_latest_snapshots())
