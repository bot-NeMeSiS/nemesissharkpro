from flask import Blueprint, jsonify, request, render_template_string
import os, sqlite3, json, time, math
from pathlib import Path

bp_ml_explainability_v201 = Blueprint('ml_explainability_v201', __name__)
VERSION = 'V201_ML_EXPLAINABILITY_AUDIT_PRO'


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
        if v in (None, ''):
            return fb
        return float(str(v).replace('%', '').replace(',', '.'))
    except Exception:
        return fb


def _clamp(x, lo=0, hi=100):
    return max(lo, min(hi, float(x)))


def init_explainability():
    con = _connect(); cur = con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS ml_explanations_v201 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_row_id INTEGER,
        entity_type TEXT,
        entity_id TEXT,
        title TEXT,
        confidence REAL DEFAULT 0,
        risk_score REAL DEFAULT 0,
        value_score REAL DEFAULT 0,
        quality_score REAL DEFAULT 0,
        verdict TEXT,
        explanation_json TEXT,
        audit_json TEXT,
        created_at INTEGER
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS ml_audit_runs_v201 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_type TEXT,
        status TEXT,
        rows_checked INTEGER DEFAULT 0,
        issues_found INTEGER DEFAULT 0,
        summary_json TEXT,
        created_at INTEGER
    )''')
    con.commit(); con.close()


def _v200_rows(limit=200):
    rows = []
    con = _connect(); cur = con.cursor()
    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ml_training_rows_v200'")
        if not cur.fetchone():
            try:
                from ml_pipeline_v200.routes import build_dataset
                build_dataset(limit=limit, persist=True)
            except Exception:
                pass
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ml_training_rows_v200'")
        if cur.fetchone():
            cur.execute('SELECT * FROM ml_training_rows_v200 ORDER BY id DESC LIMIT ?', (limit,))
            rows = [dict(r) for r in cur.fetchall()]
    except Exception:
        rows = []
    finally:
        con.close()
    return rows


def _feature_json(row):
    try:
        return json.loads(row.get('features_json') or '{}')
    except Exception:
        return {}


def _explain(row):
    features = _feature_json(row)
    confidence = _num(row.get('confidence'), _num(features.get('confianza')))
    risk = _num(row.get('risk_score'), _num(features.get('riesgo')))
    value = _num(row.get('value_score'), _num(features.get('valor_estimado')))
    quality = _num(row.get('quality_score'), _num(features.get('calidad_dato')))
    odds = _num(row.get('odds'), _num(features.get('cuota')))
    momentum = _num(row.get('momentum'), _num(features.get('momentum')))
    hot = _num(row.get('hot_score'), _num(features.get('interes')))
    reasons, warnings = [], []

    if confidence >= 75:
        reasons.append('Confianza alta según los datos reales disponibles.')
    elif confidence >= 55:
        reasons.append('Confianza media: puede ser interesante, pero requiere prudencia.')
    elif confidence > 0:
        warnings.append('Confianza baja o todavía poco consolidada.')
    else:
        warnings.append('No hay confianza suficiente calculada con datos reales.')

    if value >= 65:
        reasons.append('Valor estimado alto frente a la cuota disponible.')
    elif value >= 40:
        reasons.append('Valor estimado moderado, no es una señal definitiva.')
    else:
        warnings.append('No aparece una ventaja clara de valor en este momento.')

    if risk >= 70:
        warnings.append('Riesgo elevado: no debe tratarse como apuesta segura.')
    elif risk <= 35:
        reasons.append('Riesgo relativamente controlado dentro del modelo actual.')
    else:
        reasons.append('Riesgo medio: conviene ajustar stake y revisar contexto.')

    if momentum >= 60:
        reasons.append('Momentum favorable detectado en la lectura reciente.')
    elif momentum > 0:
        reasons.append('Momentum presente, pero no dominante.')

    if hot >= 70:
        reasons.append('Interés alto por actividad/señales del sistema.')

    if quality < 45:
        warnings.append('Calidad de dato limitada: faltan histórico, eventos o cierre suficiente.')
    elif quality >= 75:
        reasons.append('Calidad de dato buena para explicar el score actual.')

    if odds and odds > 4:
        warnings.append('Cuota alta: mayor retorno potencial, pero también más incertidumbre.')
    elif odds and odds <= 1.35:
        warnings.append('Cuota muy baja: revisar si el beneficio compensa el riesgo.')

    if value >= 65 and risk <= 45 and confidence >= 65:
        verdict = 'Interesante con prudencia'
    elif confidence >= 70 and risk <= 55:
        verdict = 'Señal sólida, no garantizada'
    elif risk >= 75 or quality < 35:
        verdict = 'Precaución alta'
    else:
        verdict = 'Seguimiento recomendado'

    title = features.get('titulo') or row.get('entity_id') or 'Registro ML real'
    explanation = {
        'titulo': title,
        'veredicto': verdict,
        'motivos': reasons[:6],
        'alertas': warnings[:6],
        'lectura_simple': _simple_reading(verdict, reasons, warnings),
        'metricas': {
            'confianza': round(_clamp(confidence), 2),
            'riesgo': round(_clamp(risk), 2),
            'valor_estimado': round(_clamp(value), 2),
            'calidad_dato': round(_clamp(quality), 2),
            'cuota': odds,
            'momentum': round(_clamp(momentum), 2),
        }
    }
    audit = _audit_row(row, explanation)
    return {
        'source_row_id': row.get('id'),
        'entity_type': row.get('entity_type') or 'dato',
        'entity_id': row.get('entity_id') or '',
        'title': title,
        'confidence': explanation['metricas']['confianza'],
        'risk_score': explanation['metricas']['riesgo'],
        'value_score': explanation['metricas']['valor_estimado'],
        'quality_score': explanation['metricas']['calidad_dato'],
        'verdict': verdict,
        'explanation': explanation,
        'audit': audit,
    }


def _simple_reading(verdict, reasons, warnings):
    text = verdict + '. '
    if reasons:
        text += reasons[0]
    if warnings:
        text += ' Aviso: ' + warnings[0]
    return text


def _audit_row(row, explanation):
    issues = []
    m = explanation.get('metricas', {})
    if not row.get('entity_id'):
        issues.append('Falta identificador claro del partido/pick.')
    if m.get('calidad_dato', 0) < 40:
        issues.append('Calidad de dato baja para tomar decisiones automáticas.')
    if m.get('confianza', 0) >= 90 and m.get('riesgo', 0) >= 70:
        issues.append('Confianza y riesgo aparecen altos a la vez: revisar señal.')
    if not row.get('label_result'):
        issues.append('Todavía no hay resultado cerrado para validación histórica.')
    return {
        'estado': 'revisar' if issues else 'ok',
        'incidencias': issues,
        'nota': 'Auditoría prudente: no bloquea datos reales, solo marca revisión.'
    }


def build_explanations(limit=200, persist=True):
    init_explainability()
    rows = _v200_rows(limit)
    explained = [_explain(r) for r in rows]
    issues = sum(1 for e in explained if e['audit']['estado'] != 'ok')
    if persist and explained:
        con = _connect(); cur = con.cursor()
        for e in explained:
            cur.execute('''INSERT INTO ml_explanations_v201(source_row_id,entity_type,entity_id,title,confidence,risk_score,value_score,quality_score,verdict,explanation_json,audit_json,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''', (
                e['source_row_id'], e['entity_type'], e['entity_id'], e['title'], e['confidence'], e['risk_score'], e['value_score'], e['quality_score'], e['verdict'],
                json.dumps(e['explanation'], ensure_ascii=False), json.dumps(e['audit'], ensure_ascii=False), _now()
            ))
        cur.execute('INSERT INTO ml_audit_runs_v201(run_type,status,rows_checked,issues_found,summary_json,created_at) VALUES(?,?,?,?,?,?)', (
            'explainability_build', 'ok', len(explained), issues, json.dumps({'version': VERSION, 'mensaje': 'Explicaciones generadas desde filas ML reales V200.'}, ensure_ascii=False), _now()
        ))
        con.commit(); con.close()
    return {'ok': True, 'version': VERSION, 'filas_revisadas': len(explained), 'incidencias': issues, 'explicaciones': explained[:50]}


def status():
    init_explainability()
    con = _connect(); cur = con.cursor()
    try:
        cur.execute('SELECT COUNT(*) c FROM ml_explanations_v201'); explanations = cur.fetchone()['c']
        cur.execute('SELECT COUNT(*) c FROM ml_audit_runs_v201'); runs = cur.fetchone()['c']
        cur.execute('SELECT * FROM ml_explanations_v201 ORDER BY id DESC LIMIT 12')
        latest = []
        for r in cur.fetchall():
            d = dict(r)
            try: d['explicacion'] = json.loads(d.get('explanation_json') or '{}')
            except Exception: d['explicacion'] = {}
            try: d['auditoria'] = json.loads(d.get('audit_json') or '{}')
            except Exception: d['auditoria'] = {}
            latest.append(d)
    finally:
        con.close()
    return {'ok': True, 'version': VERSION, 'idioma': 'español', 'explicaciones_guardadas': explanations, 'auditorias': runs, 'ultimas': latest}


@bp_ml_explainability_v201.route('/api/v201/ml-explain/status')
def api_status():
    return jsonify(status())


@bp_ml_explainability_v201.route('/api/v201/ml-explain/build', methods=['GET', 'POST'])
def api_build():
    limit = int(request.values.get('limit', 200))
    return jsonify(build_explanations(limit=limit, persist=True))


PAGE = '''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Explicabilidad ML V201 · NeMeSiS</title><style>
:root{--bg:#030914;--card:rgba(8,22,42,.92);--line:rgba(116,210,255,.18);--txt:#f3f8ff;--mut:#9eb6ce;--acc:#6df7ca;--blue:#62b6ff;--gold:#f7d774;--red:#ff6f8c}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 15% 0,#143b68,#071121 42%,#02050b);font-family:Inter,system-ui,Segoe UI,Arial,sans-serif;color:var(--txt)}.wrap{max-width:1180px;margin:auto;padding:22px}.nav{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px}.btn{border:1px solid var(--line);background:rgba(255,255,255,.06);color:var(--txt);padding:10px 14px;border-radius:15px;text-decoration:none;font-weight:950}.primary{background:linear-gradient(135deg,var(--acc),var(--blue));color:#02101b}.hero,.card{border:1px solid var(--line);background:linear-gradient(135deg,rgba(18,52,90,.94),rgba(7,19,37,.88));border-radius:30px;padding:24px;box-shadow:0 24px 70px rgba(0,0,0,.34)}h1{font-size:clamp(32px,5vw,58px);line-height:1;margin:10px 0}.mut{color:var(--mut)}.tag{display:inline-flex;border:1px solid var(--line);border-radius:999px;padding:7px 10px;color:var(--acc);font-weight:950}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px;margin-top:16px}.kpi{border:1px solid var(--line);background:rgba(255,255,255,.05);border-radius:22px;padding:16px}.kpi b{font-size:30px;color:var(--gold)}.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}.explain{border:1px solid var(--line);background:rgba(255,255,255,.045);border-radius:22px;padding:16px;margin-top:12px}.top{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap}.pill{border:1px solid var(--line);border-radius:999px;padding:7px 10px;font-weight:900}.ok{color:var(--acc)}.warn{color:var(--gold)}.bad{color:var(--red)}.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;margin:12px 0}.metric{background:rgba(255,255,255,.055);border:1px solid var(--line);border-radius:16px;padding:10px}.metric b{display:block;font-size:22px}.bar{height:8px;border-radius:99px;background:rgba(255,255,255,.08);overflow:hidden}.fill{height:100%;background:linear-gradient(90deg,var(--acc),var(--blue),var(--gold));border-radius:99px}ul{margin:8px 0 0 18px;padding:0}@media(max-width:720px){.wrap{padding:14px}.hero{border-radius:24px}.top{display:block}}
</style></head><body><div class="wrap"><div class="nav"><a class="btn" href="javascript:history.back()">← Atrás</a><a class="btn" href="javascript:history.forward()">Adelante →</a><a class="btn" href="/cliente/pro">Inicio cliente</a><a class="btn" href="/cliente/ml-real">ML real</a><a class="btn" href="/cliente/shark-ai-real">SHARK AI</a></div><section class="hero"><span class="tag">V201 · EXPLICABILIDAD + AUDITORÍA ML PRO</span><h1>Scores explicados en español</h1><p class="mut">Capa prudente encima del ML real V200: explica por qué aparece un score, qué riesgo tiene, qué datos faltan y qué debe revisar el sistema. No inventa resultados ni vende garantías.</p><div class="actions"><a class="btn primary" href="?accion=explicar">Generar explicaciones reales</a><a class="btn" href="/api/v201/ml-explain/status">Ver API estado</a></div></section><div class="grid"><div class="kpi"><b>{{status.explicaciones_guardadas}}</b><div class="mut">Explicaciones guardadas</div></div><div class="kpi"><b>{{status.auditorias}}</b><div class="mut">Auditorías ejecutadas</div></div><div class="kpi"><b>REAL</b><div class="mut">Desde V200, sin fake ML</div></div><div class="kpi"><b>ES</b><div class="mut">Motivos en español</div></div></div>{% if resultado %}<section class="card" style="margin-top:16px"><h2>Resultado de generación</h2><p class="mut">Filas revisadas: <b>{{resultado.filas_revisadas}}</b> · Incidencias: <b>{{resultado.incidencias}}</b></p></section>{% endif %}<section class="card" style="margin-top:16px"><h2>Últimas explicaciones</h2>{% for r in status.ultimas %}{% set e = r.explicacion %}{% set a = r.auditoria %}<div class="explain"><div class="top"><div><b>{{r.title}}</b><div class="mut">{{r.entity_type}} · {{r.entity_id}}</div></div><span class="pill {% if a.estado=='ok' %}ok{% else %}warn{% endif %}">{{r.verdict}}</span></div><p>{{e.lectura_simple}}</p><div class="metrics"><div class="metric"><b>{{r.confidence|round(1)}}</b><span class="mut">Confianza</span><div class="bar"><div class="fill" style="width:{{r.confidence}}%"></div></div></div><div class="metric"><b>{{r.risk_score|round(1)}}</b><span class="mut">Riesgo</span><div class="bar"><div class="fill" style="width:{{r.risk_score}}%"></div></div></div><div class="metric"><b>{{r.value_score|round(1)}}</b><span class="mut">Valor</span><div class="bar"><div class="fill" style="width:{{r.value_score}}%"></div></div></div><div class="metric"><b>{{r.quality_score|round(1)}}</b><span class="mut">Calidad dato</span><div class="bar"><div class="fill" style="width:{{r.quality_score}}%"></div></div></div></div>{% if e.motivos %}<b class="ok">Motivos</b><ul>{% for m in e.motivos %}<li>{{m}}</li>{% endfor %}</ul>{% endif %}{% if e.alertas %}<b class="warn">Alertas</b><ul>{% for m in e.alertas %}<li>{{m}}</li>{% endfor %}</ul>{% endif %}{% if a.incidencias %}<b class="bad">Auditoría</b><ul>{% for m in a.incidencias %}<li>{{m}}</li>{% endfor %}</ul>{% endif %}</div>{% else %}<p class="mut">Todavía no hay explicaciones. Pulsa “Generar explicaciones reales”.</p>{% endfor %}</section></div></body></html>'''


@bp_ml_explainability_v201.route('/cliente/ml-explicado')
@bp_ml_explainability_v201.route('/cliente/ml-explainability')
@bp_ml_explainability_v201.route('/ml-explainability-pro')
def page_client():
    resultado = None
    if request.args.get('accion') == 'explicar':
        resultado = build_explanations(limit=200, persist=True)
    return render_template_string(PAGE, status=status(), resultado=resultado)


@bp_ml_explainability_v201.route('/admin/ml-explicado')
@bp_ml_explainability_v201.route('/admin/ml-explainability')
def page_admin():
    return page_client()
