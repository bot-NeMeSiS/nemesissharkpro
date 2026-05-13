from flask import Blueprint, jsonify, request, render_template_string, session
import os, sqlite3, json, time, re
from pathlib import Path

bp_shark_ai_real_v199 = Blueprint('shark_ai_real_v199', __name__)
VERSION = 'V199_SHARK_AI_REAL_EXPERIENCE_PRO'


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
    cur.execute('''CREATE TABLE IF NOT EXISTS shark_ai_real_logs_v199 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        pregunta TEXT,
        respuesta TEXT,
        contexto_json TEXT,
        modo TEXT,
        created_at INTEGER
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS shark_ai_real_feedback_v199 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        pregunta TEXT,
        util INTEGER DEFAULT 0,
        created_at INTEGER
    )''')
    con.commit(); con.close()


def _norm(s):
    s = str(s or '').lower()
    repl = {'á':'a','é':'e','í':'i','ó':'o','ú':'u','ü':'u','ñ':'n','ç':'c'}
    for a,b in repl.items(): s = s.replace(a,b)
    return re.sub(r'[^a-z0-9]+',' ',s).strip()


def _num(v, fb=0.0):
    try:
        if v in (None, ''): return fb
        return float(str(v).replace('%','').replace(',','.'))
    except Exception:
        return fb


def _get_user_id():
    return str(session.get('user_id') or session.get('cliente_id') or session.get('admin_id') or 'anonimo')


def _discover(q='', filtro='todo', limit=30):
    try:
        from search_discover_v198.routes import build_discover
        return build_discover(q, filtro, limit)
    except Exception as exc:
        return {'ok': False, 'error': str(exc), 'resultados': [], 'resumen': {}}


def _signals(limit=20):
    try:
        from match_intelligence_v192.routes import build_match_intelligence
        data = build_match_intelligence(limit=limit)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {'ok': True, 'signals': [], 'resumen': {}}


def _latest_real_context(question=''):
    qn = _norm(question)
    if any(w in qn for w in ['directo','live','vivo','ahora']):
        filtro = 'directo'
    elif any(w in qn for w in ['pick','picks','apuesta','cuota','valor','value']):
        filtro = 'picks'
    elif any(w in qn for w in ['caliente','calor','presion','momentum']):
        filtro = 'calientes'
    elif any(w in qn for w in ['confianza','seguro','riesgo','mejor']):
        filtro = 'alta-confianza'
    else:
        filtro = 'todo'
    data = _discover('', filtro, 40)
    results = data.get('resultados') or []
    results.sort(key=lambda x: (_num(x.get('hot_score'),0), _num(x.get('confianza'),0)), reverse=True)
    return {'filtro': filtro, 'discover': data, 'top': results[:8], 'signals': _signals(20)}


def _item_line(it):
    tipo = 'pick' if it.get('tipo') == 'pick' else 'partido'
    titulo = it.get('titulo') or f"{it.get('local','Local')} vs {it.get('visitante','Visitante')}"
    liga = it.get('liga') or 'Competición real'
    estado = it.get('estado') or 'Estado pendiente'
    hora = it.get('hora') or 'hora pendiente'
    cuota = f" · cuota {it.get('cuota')}" if it.get('cuota') else ''
    conf = _num(it.get('confianza'),0)
    interes = _num(it.get('hot_score'),0)
    extra = f" · confianza {conf:.0f}/100" if conf else f" · interés {interes:.0f}/100"
    return f"- {tipo.capitalize()}: {titulo} · {liga} · {estado} · {hora}{cuota}{extra}"


def answer_real(question=''):
    _init()
    q = (question or '').strip()
    ctx = _latest_real_context(q)
    top = ctx.get('top') or []
    qn = _norm(q)
    if not top:
        ans = "Ahora mismo no tengo datos reales suficientes para responder con partidos o picks. No voy a inventar cuotas, resultados ni señales. Prueba a sincronizar fixtures/picks desde el panel admin o vuelve a consultar cuando haya datos cargados."
    elif any(w in qn for w in ['por que','porque','motivo','explica','razon']):
        it = top[0]
        ans = "Mi lectura con datos reales ahora mismo es esta:\n\n" + _item_line(it) + "\n\nMotivo: destaca por combinación de interés visual, estado del partido, confianza disponible y posible valor en los datos guardados. No es una garantía de acierto; es una ayuda para decidir con gestión de riesgo."
    elif any(w in qn for w in ['mejor','top','recomienda','recomiendas','valor','value']):
        ans = "Mejores opciones reales detectadas ahora mismo:\n\n" + "\n".join(_item_line(x) for x in top[:5]) + "\n\nÚsalo como lectura de apoyo, no como apuesta garantizada. Si falta cuota o mercado es porque el proveedor no lo ha entregado o no está guardado todavía."
    elif any(w in qn for w in ['riesgo','seguro','bajo riesgo','menos riesgo']):
        low = sorted(top, key=lambda x: (_num(x.get('confianza'),0), _num(x.get('hot_score'),0)), reverse=True)[:5]
        ans = "Lectura de menor riesgo disponible con datos reales:\n\n" + "\n".join(_item_line(x) for x in low) + "\n\nAun así, ninguna apuesta es segura. La confianza indica calidad/consistencia de lectura, no certeza absoluta."
    elif any(w in qn for w in ['directo','live','vivo','ahora']):
        ans = "Partidos o señales en directo detectadas:\n\n" + "\n".join(_item_line(x) for x in top[:6]) + "\n\nSolo muestro información existente en la base de datos real del sistema."
    elif any(w in qn for w in ['pick','picks','apuesta','cuota']):
        picks = [x for x in top if x.get('tipo') == 'pick'] or top[:5]
        ans = "Picks reales encontrados:\n\n" + "\n".join(_item_line(x) for x in picks[:5]) + "\n\nSi ves pocos picks, conviene revisar sincronización, cierre de picks y proveedor de cuotas."
    else:
        ans = "Resumen inteligente SHARK con datos reales:\n\n" + "\n".join(_item_line(x) for x in top[:6]) + "\n\nPuedes preguntarme: ‘¿qué pick tiene más valor?’, ‘¿qué partido está más caliente?’, ‘¿qué tiene menos riesgo?’ o ‘explícame por qué’."
    try:
        con = _connect()
        con.execute('INSERT INTO shark_ai_real_logs_v199(user_id,pregunta,respuesta,contexto_json,modo,created_at) VALUES(?,?,?,?,?,?)', (_get_user_id(), q, ans, json.dumps({'filtro': ctx.get('filtro'), 'total': len(top)}, ensure_ascii=False), 'real_only', int(time.time())))
        con.commit(); con.close()
    except Exception:
        pass
    return {'ok': True, 'version': VERSION, 'pregunta': q, 'respuesta': ans, 'contexto': {'filtro': ctx.get('filtro'), 'items_usados': len(top)}, 'real_only': True}


@bp_shark_ai_real_v199.route('/api/v199/shark-ai-real', methods=['GET','POST'])
def api_shark_ai_real():
    question = request.values.get('q') or request.values.get('pregunta') or ''
    if request.is_json:
        body = request.get_json(silent=True) or {}
        question = body.get('q') or body.get('pregunta') or question
    return jsonify(answer_real(question))


@bp_shark_ai_real_v199.route('/api/v199/shark-ai-real/status')
def api_status():
    data = _discover('', 'todo', 10)
    return jsonify({'ok': True, 'version': VERSION, 'estado': 'activo', 'idioma': 'español', 'real_only': True, 'resultados_disponibles': len(data.get('resultados') or []), 'resumen': data.get('resumen') or {}})


PAGE = r'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SHARK AI Real · NeMeSiS</title><style>
:root{--bg:#05101d;--card:rgba(10,25,48,.92);--line:rgba(135,210,255,.18);--txt:#f3f8ff;--mut:#9fb7cb;--acc:#6df7ca;--blue:#65b7ff;--gold:#f6d365}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 20% 0,#123d6b,#05101d 45%,#02060c);color:var(--txt);font-family:Inter,system-ui,Segoe UI,Arial,sans-serif}.wrap{max-width:1120px;margin:auto;padding:22px}.nav{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px}.btn{border:1px solid var(--line);background:rgba(255,255,255,.06);color:var(--txt);padding:10px 14px;border-radius:15px;text-decoration:none;font-weight:900;cursor:pointer}.primary{background:linear-gradient(135deg,var(--acc),var(--blue));color:#04111c}.hero,.panel,.answer{border:1px solid var(--line);background:linear-gradient(135deg,rgba(17,56,95,.94),rgba(9,23,43,.88));border-radius:30px;padding:24px;box-shadow:0 24px 70px rgba(0,0,0,.35)}h1{font-size:clamp(34px,5vw,60px);line-height:1;margin:10px 0}.mut{color:var(--mut)}.tag{display:inline-flex;border:1px solid var(--line);border-radius:999px;padding:7px 10px;color:var(--acc);font-weight:950}.ask{display:grid;grid-template-columns:1fr auto;gap:10px;margin-top:18px}.ask input{border:1px solid var(--line);background:rgba(255,255,255,.08);color:var(--txt);padding:15px 16px;border-radius:18px;font-size:16px;outline:none}.chips{display:flex;flex-wrap:wrap;gap:10px;margin:17px 0}.chip{border:1px solid var(--line);border-radius:999px;padding:10px 13px;background:rgba(255,255,255,.05);color:#d8efff;text-decoration:none;font-weight:900}.answer{margin-top:16px;white-space:pre-wrap;line-height:1.65}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin-top:16px}.mini{border:1px solid var(--line);background:rgba(255,255,255,.05);border-radius:20px;padding:15px}.mini b{font-size:24px;color:var(--gold)}@media(max-width:650px){.ask{grid-template-columns:1fr}.wrap{padding:14px}.hero{border-radius:24px}}
</style></head><body><div class="wrap"><div class="nav"><a class="btn" href="javascript:history.back()">← Atrás</a><a class="btn" href="javascript:history.forward()">Adelante →</a><a class="btn" href="/cliente/pro">Inicio cliente</a><a class="btn" href="/cliente/buscar">Buscar</a></div><section class="hero"><span class="tag">V199 · SHARK AI REAL EXPERIENCE PRO</span><h1>SHARK AI con datos reales</h1><p class="mut">Asistente deportivo en español conectado a partidos, picks, señales, cuotas y tendencias guardadas. No inventa partidos, resultados ni cuotas.</p><form class="ask" method="get"><input name="q" value="{{q}}" placeholder="Pregunta: ¿qué pick tiene más valor hoy? ¿qué partido está caliente? ¿qué tiene menos riesgo?"><button class="btn primary">Preguntar</button></form><div class="chips"><a class="chip" href="?q=Qué pick tiene más valor ahora">🧠 Mayor valor</a><a class="chip" href="?q=Qué partido está más caliente en directo">🔥 Partido caliente</a><a class="chip" href="?q=Qué opción tiene menos riesgo">🛡️ Menos riesgo</a><a class="chip" href="?q=Explícame por qué recomiendas el primero">💬 Explicar motivo</a></div></section><div class="grid"><div class="mini"><b>{{status.resultados_disponibles}}</b><div class="mut">Datos reales disponibles</div></div><div class="mini"><b>ES</b><div class="mut">Idioma principal</div></div><div class="mini"><b>REAL</b><div class="mut">Sin datos inventados</div></div></div>{% if respuesta %}<div class="answer">{{respuesta}}</div>{% else %}<div class="answer">Haz una pregunta para que SHARK AI consulte los datos reales del sistema.</div>{% endif %}</div></body></html>'''


@bp_shark_ai_real_v199.route('/cliente/shark-ai-real')
@bp_shark_ai_real_v199.route('/shark-ai-real')
def page_client():
    q = request.args.get('q','').strip()
    status = api_status().get_json()
    respuesta = answer_real(q)['respuesta'] if q else ''
    return render_template_string(PAGE, q=q, respuesta=respuesta, status=status)


@bp_shark_ai_real_v199.route('/admin/shark-ai-real')
def page_admin():
    q = request.args.get('q','').strip() or 'Resumen inteligente actual'
    data = answer_real(q)
    html = PAGE + '<pre style="max-width:1120px;margin:20px auto;color:#cff;background:#05101d;border:1px solid rgba(135,210,255,.18);border-radius:18px;padding:16px;white-space:pre-wrap">{{debug}}</pre>'
    return render_template_string(html, q=q, respuesta=data['respuesta'], status=api_status().get_json(), debug=json.dumps(data, ensure_ascii=False, indent=2))
