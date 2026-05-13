from flask import Blueprint, jsonify, request, render_template_string, session
import os, sqlite3, json, time, csv, io, math, statistics
from pathlib import Path

bp_ml_pipeline_v200 = Blueprint('ml_pipeline_v200', __name__)
VERSION = 'V200_REAL_ML_PIPELINE_PRO'


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


def _num(v, fb=0.0):
    try:
        if v in (None, ''): return fb
        return float(str(v).replace('%','').replace(',','.'))
    except Exception:
        return fb


def _clamp(x, lo=0, hi=100):
    return max(lo, min(hi, x))


def init_ml_pipeline():
    con = _connect(); cur = con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS ml_training_rows_v200 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        entity_type TEXT,
        entity_id TEXT,
        league TEXT,
        market TEXT,
        odds REAL DEFAULT 0,
        confidence REAL DEFAULT 0,
        hot_score REAL DEFAULT 0,
        momentum REAL DEFAULT 0,
        risk_score REAL DEFAULT 0,
        value_score REAL DEFAULT 0,
        label_result TEXT,
        quality_score REAL DEFAULT 0,
        features_json TEXT,
        created_at INTEGER
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS ml_model_registry_v200 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model_name TEXT,
        model_type TEXT,
        version TEXT,
        status TEXT,
        metrics_json TEXT,
        notes TEXT,
        created_at INTEGER
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS ml_pipeline_runs_v200 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_type TEXT,
        status TEXT,
        rows_created INTEGER DEFAULT 0,
        metrics_json TEXT,
        message TEXT,
        created_at INTEGER
    )''')
    con.commit(); con.close()


def _table_exists(cur, table):
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cur.fetchone() is not None


def _cols(cur, table):
    try:
        cur.execute('PRAGMA table_info(%s)' % table)
        return [r[1] for r in cur.fetchall()]
    except Exception:
        return []


def _best_col(cols, names):
    lc = {c.lower(): c for c in cols}
    for n in names:
        if n.lower() in lc: return lc[n.lower()]
    for c in cols:
        low = c.lower()
        if any(n.lower() in low for n in names): return c
    return None


def _discover_rows(limit=250):
    rows = []
    # Preferimos V198 si está disponible porque ya agrega partidos/picks reales sin inventar.
    try:
        from search_discover_v198.routes import build_discover
        data = build_discover('', 'todo', limit)
        for it in data.get('resultados') or []:
            rows.append(dict(it, source='search_discover_v198'))
    except Exception:
        pass
    if rows:
        return rows[:limit]

    # Fallback prudente: inspección genérica de tablas existentes.
    con = _connect(); cur = con.cursor()
    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        candidates = [t for t in tables if any(k in t.lower() for k in ['pick','fixture','match','odds','snapshot'])]
        for t in candidates[:10]:
            cols = _cols(cur, t)
            title = _best_col(cols, ['titulo','title','name','match_name','fixture_name'])
            league = _best_col(cols, ['liga','league','competition'])
            odds = _best_col(cols, ['cuota','odds','price'])
            conf = _best_col(cols, ['confianza','confidence','score'])
            market = _best_col(cols, ['mercado','market','pick'])
            entity_id = _best_col(cols, ['id','fixture_id','match_id','pick_id'])
            select_cols = [c for c in [entity_id,title,league,odds,conf,market] if c]
            if not select_cols: continue
            q = 'SELECT %s FROM %s LIMIT 50' % (','.join('"%s"'%c for c in select_cols), '"%s"'%t)
            cur.execute(q)
            for r in cur.fetchall():
                d = dict(r)
                rows.append({
                    'source': t,
                    'tipo': 'pick' if 'pick' in t.lower() else 'partido',
                    'id': d.get(entity_id) if entity_id else None,
                    'titulo': d.get(title) if title else t,
                    'liga': d.get(league) if league else '',
                    'cuota': d.get(odds) if odds else 0,
                    'confianza': d.get(conf) if conf else 0,
                    'mercado': d.get(market) if market else '',
                })
                if len(rows) >= limit: break
            if len(rows) >= limit: break
    except Exception:
        pass
    finally:
        con.close()
    return rows[:limit]


def _feature_row(it):
    odds = _num(it.get('cuota') or it.get('odds') or it.get('price'), 0)
    confidence = _num(it.get('confianza') or it.get('confidence'), 0)
    hot = _num(it.get('hot_score') or it.get('interes') or it.get('score'), 0)
    momentum = _num(it.get('momentum') or it.get('momentum_score'), 0)
    if not hot and confidence:
        hot = confidence * 0.75
    if not momentum:
        momentum = hot * 0.55
    implied = (100.0 / odds) if odds and odds > 1 else 0
    risk = _clamp(100 - confidence + max(0, odds - 2.0) * 10 - momentum * 0.08)
    value = _clamp((confidence - implied) * 0.7 + hot * 0.25 + momentum * 0.15)
    quality = _clamp((confidence * 0.45) + (hot * 0.25) + (momentum * 0.15) + (20 if odds else 0))
    label = str(it.get('resultado') or it.get('result') or it.get('status') or '').upper()
    label_result = label if label in ['WIN','LOSS','VOID','PUSH'] else None
    entity_type = it.get('tipo') or ('pick' if it.get('mercado') else 'partido')
    entity_id = str(it.get('id') or it.get('match_id') or it.get('fixture_id') or it.get('titulo') or '')[:120]
    features = {
        'cuota': odds,
        'probabilidad_implicita_pct': round(implied, 2),
        'confianza': round(confidence, 2),
        'interes': round(hot, 2),
        'momentum': round(momentum, 2),
        'riesgo': round(risk, 2),
        'valor_estimado': round(value, 2),
        'calidad_dato': round(quality, 2),
        'titulo': it.get('titulo') or it.get('name') or '',
        'estado': it.get('estado') or it.get('status') or '',
    }
    return {
        'source': it.get('source') or 'sistema',
        'entity_type': entity_type,
        'entity_id': entity_id,
        'league': it.get('liga') or it.get('league') or '',
        'market': it.get('mercado') or it.get('market') or it.get('pick') or '',
        'odds': odds,
        'confidence': confidence,
        'hot_score': hot,
        'momentum': momentum,
        'risk_score': risk,
        'value_score': value,
        'label_result': label_result,
        'quality_score': quality,
        'features_json': json.dumps(features, ensure_ascii=False),
        'created_at': _now(),
    }


def build_dataset(limit=300, persist=True):
    init_ml_pipeline()
    raw = _discover_rows(limit)
    feature_rows = [_feature_row(x) for x in raw]
    if persist and feature_rows:
        con = _connect(); cur = con.cursor()
        for r in feature_rows:
            cur.execute('''INSERT INTO ml_training_rows_v200(source,entity_type,entity_id,league,market,odds,confidence,hot_score,momentum,risk_score,value_score,label_result,quality_score,features_json,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (r['source'],r['entity_type'],r['entity_id'],r['league'],r['market'],r['odds'],r['confidence'],r['hot_score'],r['momentum'],r['risk_score'],r['value_score'],r['label_result'],r['quality_score'],r['features_json'],r['created_at']))
        con.commit(); con.close()
    metrics = _metrics(feature_rows)
    _log_run('dataset_build', 'ok', len(feature_rows), metrics, 'Dataset generado desde datos reales disponibles.' if feature_rows else 'No hay datos reales suficientes para generar filas.')
    return {'ok': True, 'version': VERSION, 'real_only': True, 'rows_created': len(feature_rows), 'metrics': metrics, 'sample': feature_rows[:20]}


def _metrics(rows):
    if not rows:
        return {'filas': 0, 'estado': 'sin_datos'}
    vals = lambda k: [float(r.get(k) or 0) for r in rows]
    labels = [r.get('label_result') for r in rows if r.get('label_result')]
    return {
        'filas': len(rows),
        'cuota_media': round(statistics.mean(vals('odds')), 2),
        'confianza_media': round(statistics.mean(vals('confidence')), 2),
        'riesgo_medio': round(statistics.mean(vals('risk_score')), 2),
        'valor_medio': round(statistics.mean(vals('value_score')), 2),
        'calidad_media': round(statistics.mean(vals('quality_score')), 2),
        'labels_cerrados': len(labels),
        'winrate_observable': round(100 * labels.count('WIN') / len(labels), 2) if labels else None,
        'estado': 'listo_para_entrenamiento' if len(rows) >= 50 and len(labels) >= 10 else 'recopilando_datos'
    }


def _log_run(run_type, status, rows, metrics, message):
    try:
        con = _connect()
        con.execute('INSERT INTO ml_pipeline_runs_v200(run_type,status,rows_created,metrics_json,message,created_at) VALUES(?,?,?,?,?,?)', (run_type,status,rows,json.dumps(metrics,ensure_ascii=False),message,_now()))
        con.commit(); con.close()
    except Exception:
        pass


def baseline_model():
    init_ml_pipeline()
    con = _connect(); cur = con.cursor()
    cur.execute('SELECT * FROM ml_training_rows_v200 ORDER BY id DESC LIMIT 500')
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    if not rows:
        ds = build_dataset(300, True)
        rows = ds.get('sample') or []
    metrics = _metrics(rows)
    if rows:
        # Baseline transparente: no entrena una caja negra; calcula umbrales reales para priorización.
        value_threshold = round(statistics.mean([r['value_score'] for r in rows]) + (statistics.pstdev([r['value_score'] for r in rows]) if len(rows)>1 else 0), 2)
        risk_threshold = round(statistics.mean([r['risk_score'] for r in rows]), 2)
        model = {
            'nombre': 'baseline_value_risk_v200',
            'tipo': 'baseline_transparente',
            'umbral_valor': value_threshold,
            'umbral_riesgo_max': risk_threshold,
            'nota': 'Modelo base interpretable. No promete aciertos; prioriza oportunidades por valor estimado, riesgo y calidad de dato.'
        }
    else:
        model = {'nombre': 'baseline_value_risk_v200', 'tipo': 'pendiente', 'nota': 'Sin datos reales suficientes.'}
    con = _connect()
    con.execute('INSERT INTO ml_model_registry_v200(model_name,model_type,version,status,metrics_json,notes,created_at) VALUES(?,?,?,?,?,?,?)', (model['nombre'], model['tipo'], VERSION, 'activo' if rows else 'pendiente', json.dumps({'metrics': metrics, 'model': model}, ensure_ascii=False), model['nota'], _now()))
    con.commit(); con.close()
    _log_run('baseline_model', 'ok' if rows else 'pendiente', len(rows), metrics, model['nota'])
    return {'ok': True, 'version': VERSION, 'real_only': True, 'modelo': model, 'metrics': metrics}


@bp_ml_pipeline_v200.route('/api/v200/ml/status')
def api_status():
    init_ml_pipeline()
    con = _connect(); cur = con.cursor()
    cur.execute('SELECT COUNT(*) c FROM ml_training_rows_v200'); rows = cur.fetchone()['c']
    cur.execute('SELECT COUNT(*) c FROM ml_model_registry_v200'); models = cur.fetchone()['c']
    cur.execute('SELECT * FROM ml_pipeline_runs_v200 ORDER BY id DESC LIMIT 5'); runs = [dict(r) for r in cur.fetchall()]
    con.close()
    return jsonify({'ok': True, 'version': VERSION, 'estado': 'activo', 'idioma': 'español', 'real_only': True, 'training_rows': rows, 'modelos_registrados': models, 'ultimas_ejecuciones': runs})


@bp_ml_pipeline_v200.route('/api/v200/ml/build-dataset', methods=['GET','POST'])
def api_build_dataset():
    limit = int(request.values.get('limit') or 300)
    return jsonify(build_dataset(limit=limit, persist=True))


@bp_ml_pipeline_v200.route('/api/v200/ml/baseline', methods=['GET','POST'])
def api_baseline():
    return jsonify(baseline_model())


@bp_ml_pipeline_v200.route('/api/v200/ml/export.csv')
def api_export_csv():
    init_ml_pipeline()
    con = _connect(); cur = con.cursor()
    cur.execute('SELECT * FROM ml_training_rows_v200 ORDER BY id DESC LIMIT 5000')
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    out = io.StringIO()
    fields = ['id','source','entity_type','entity_id','league','market','odds','confidence','hot_score','momentum','risk_score','value_score','label_result','quality_score','created_at']
    writer = csv.DictWriter(out, fieldnames=fields)
    writer.writeheader()
    for r in rows:
        writer.writerow({k:r.get(k,'') for k in fields})
    return out.getvalue(), 200, {'Content-Type':'text/csv; charset=utf-8', 'Content-Disposition':'attachment; filename="nemesis_ml_dataset_v200.csv"'}


PAGE = r'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ML Real V200 · NeMeSiS</title><style>
:root{--bg:#040b14;--card:rgba(9,23,43,.9);--line:rgba(116,210,255,.18);--txt:#f2f8ff;--mut:#9fb7cc;--acc:#6df7ca;--blue:#65b7ff;--gold:#f6d365;--red:#ff6d86}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 20% 0,#123d6b,#06111f 42%,#02060c);font-family:Inter,system-ui,Segoe UI,Arial,sans-serif;color:var(--txt)}.wrap{max-width:1180px;margin:auto;padding:22px}.nav{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px}.btn{border:1px solid var(--line);background:rgba(255,255,255,.06);color:var(--txt);padding:10px 14px;border-radius:15px;text-decoration:none;font-weight:950;cursor:pointer}.primary{background:linear-gradient(135deg,var(--acc),var(--blue));color:#03101b}.hero,.card{border:1px solid var(--line);background:linear-gradient(135deg,rgba(17,56,95,.94),rgba(9,23,43,.88));border-radius:30px;padding:24px;box-shadow:0 24px 70px rgba(0,0,0,.34)}h1{font-size:clamp(34px,5vw,60px);line-height:1;margin:10px 0}.mut{color:var(--mut)}.tag{display:inline-flex;border:1px solid var(--line);border-radius:999px;padding:7px 10px;color:var(--acc);font-weight:950}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px;margin-top:16px}.kpi{border:1px solid var(--line);background:rgba(255,255,255,.05);border-radius:22px;padding:16px}.kpi b{font-size:28px;color:var(--gold)}.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}.table{overflow:auto;margin-top:16px}.row{display:grid;grid-template-columns:1.2fr .6fr .6fr .6fr .6fr;gap:10px;border-bottom:1px solid var(--line);padding:11px 0}.head{color:var(--acc);font-weight:950}.pill{border:1px solid var(--line);border-radius:999px;padding:6px 9px;display:inline-block}.warn{color:var(--gold)}@media(max-width:720px){.wrap{padding:14px}.row{grid-template-columns:1fr}.hero{border-radius:24px}}
</style></head><body><div class="wrap"><div class="nav"><a class="btn" href="javascript:history.back()">← Atrás</a><a class="btn" href="javascript:history.forward()">Adelante →</a><a class="btn" href="/cliente/pro">Inicio cliente</a><a class="btn" href="/cliente/shark-ai-real">SHARK AI</a></div><section class="hero"><span class="tag">V200 · REAL ML PIPELINE PRO</span><h1>Pipeline ML real</h1><p class="mut">Base de Machine Learning en español, conectada a datos reales guardados. No inventa predicciones ni promete aciertos: prepara datasets, calidad de datos, scoring transparente y registro de modelos.</p><div class="actions"><a class="btn primary" href="?accion=dataset">Generar dataset real</a><a class="btn" href="?accion=baseline">Crear baseline transparente</a><a class="btn" href="/api/v200/ml/export.csv">Exportar CSV</a></div></section><div class="grid"><div class="kpi"><b>{{status.training_rows}}</b><div class="mut">Filas ML guardadas</div></div><div class="kpi"><b>{{status.modelos_registrados}}</b><div class="mut">Modelos registrados</div></div><div class="kpi"><b>REAL</b><div class="mut">Sin datos fake</div></div><div class="kpi"><b>ES</b><div class="mut">Todo en español</div></div></div>{% if resultado %}<section class="card" style="margin-top:16px"><h2>Resultado</h2><pre class="mut" style="white-space:pre-wrap">{{resultado}}</pre></section>{% endif %}<section class="card" style="margin-top:16px"><h2>Últimas ejecuciones</h2><div class="table"><div class="row head"><div>Tipo</div><div>Estado</div><div>Filas</div><div>Fecha</div><div>Mensaje</div></div>{% for r in status.ultimas_ejecuciones %}<div class="row"><div>{{r.run_type}}</div><div><span class="pill">{{r.status}}</span></div><div>{{r.rows_created}}</div><div>{{r.created_at}}</div><div class="mut">{{r.message}}</div></div>{% else %}<p class="mut">Todavía no hay ejecuciones registradas.</p>{% endfor %}</div><p class="mut warn">Aviso: V200 es infraestructura ML real. Las probabilidades finales vendrán cuando haya suficiente histórico cerrado y validación.</p></section></div></body></html>'''


@bp_ml_pipeline_v200.route('/cliente/ml-real')
@bp_ml_pipeline_v200.route('/ml-real-pipeline')
def page_client():
    accion = request.args.get('accion','')
    resultado = ''
    if accion == 'dataset': resultado = json.dumps(build_dataset(300, True), ensure_ascii=False, indent=2)
    elif accion == 'baseline': resultado = json.dumps(baseline_model(), ensure_ascii=False, indent=2)
    status = api_status().get_json()
    return render_template_string(PAGE, status=status, resultado=resultado)


@bp_ml_pipeline_v200.route('/admin/ml-real')
@bp_ml_pipeline_v200.route('/admin/real-ml-pipeline')
def page_admin():
    return page_client()
