import os
import sqlite3
from pathlib import Path
from datetime import datetime, date
from flask import Blueprint, jsonify, render_template_string, session, request

bp_engagement_v214 = Blueprint('engagement_v214', __name__)

def _db_path():
    raw = os.environ.get('DATABASE_PATH') or os.environ.get('DB_PATH') or '/data/database.db'
    if str(raw).startswith('sqlite:///'):
        raw = str(raw).replace('sqlite:///', '', 1)
    return raw

def _connect():
    path = _db_path()
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    con = sqlite3.connect(path, timeout=8)
    con.row_factory = sqlite3.Row
    return con

def _tables(cur):
    try:
        return {r['name'] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    except Exception:
        return set()

def _user():
    u = session.get('user') or {}
    return {
        'id': u.get('id') or u.get('user_id') or 0,
        'username': u.get('username') or u.get('name') or 'Usuario',
        'plan': (u.get('plan') or u.get('membership') or 'FREE').upper(),
        'role': u.get('role') or 'cliente'
    }

def _ensure():
    con = _connect(); cur = con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS engagement_v214_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        event_type TEXT NOT NULL,
        label TEXT,
        meta TEXT,
        created_at TEXT NOT NULL
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS engagement_v214_daily_state (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        day TEXT NOT NULL,
        opened INTEGER DEFAULT 0,
        checked_live INTEGER DEFAULT 0,
        checked_picks INTEGER DEFAULT 0,
        checked_radar INTEGER DEFAULT 0,
        asked_shark INTEGER DEFAULT 0,
        updated_at TEXT NOT NULL,
        UNIQUE(user_id, day)
    )''')
    con.commit(); con.close()

def _mark(action):
    _ensure(); user = _user(); today = date.today().isoformat(); now = datetime.utcnow().isoformat(timespec='seconds') + 'Z'
    field = {'open': 'opened', 'live': 'checked_live', 'picks': 'checked_picks', 'radar': 'checked_radar', 'shark': 'asked_shark'}.get(action, 'opened')
    con = _connect(); cur = con.cursor()
    cur.execute('''INSERT INTO engagement_v214_daily_state(user_id, day, opened, updated_at)
                   VALUES(?,?,1,?) ON CONFLICT(user_id, day) DO NOTHING''', (str(user['id']), today, now))
    cur.execute(f"UPDATE engagement_v214_daily_state SET {field}=1, updated_at=? WHERE user_id=? AND day=?", (now, str(user['id']), today))
    cur.execute("INSERT INTO engagement_v214_events(user_id,event_type,label,meta,created_at) VALUES(?,?,?,?,?)", (str(user['id']), action, request.path, '', now))
    con.commit(); con.close()

def _real_counts():
    data = {'partidos': 0, 'directo': 0, 'picks': 0, 'notificaciones': 0, 'radar': 0}
    try:
        con = _connect(); cur = con.cursor(); tables = _tables(cur)
        if 'real_fixtures_v146' in tables:
            try: data['partidos'] += int(cur.execute('SELECT COUNT(*) n FROM real_fixtures_v146').fetchone()['n'])
            except Exception: pass
        if 'picks' in tables:
            try: data['picks'] += int(cur.execute('SELECT COUNT(*) n FROM picks').fetchone()['n'])
            except Exception: pass
        for t in ['smart_notifications_v205','notifications_v205','user_notifications_v205']:
            if t in tables:
                try: data['notificaciones'] += int(cur.execute(f'SELECT COUNT(*) n FROM {t}').fetchone()['n'])
                except Exception: pass
        try:
            from live_score_incidents_v209.routes import _live_payload
            payload = _live_payload(limit=80)
            matches = payload.get('matches', []) or payload.get('partidos', []) or []
            data['directo'] = len([m for m in matches if m.get('minute') or m.get('minuto') or 'live' in str(m.get('status','')).lower() or 'directo' in str(m.get('estado','')).lower()])
            data['partidos'] = max(data['partidos'], len(matches))
        except Exception:
            pass
        con.close()
    except Exception:
        pass
    data['radar'] = min(99, data['partidos'] + data['picks'])
    return data

def _daily_state():
    _ensure(); user=_user(); today=date.today().isoformat()
    con=_connect(); cur=con.cursor()
    row = cur.execute('SELECT * FROM engagement_v214_daily_state WHERE user_id=? AND day=?', (str(user['id']), today)).fetchone()
    con.close()
    if not row:
        return {'opened':0,'checked_live':0,'checked_picks':0,'checked_radar':0,'asked_shark':0}
    return dict(row)

def _summary():
    _mark('open')
    user=_user(); counts=_real_counts(); state=_daily_state()
    checklist = [
        {'key':'live','titulo':'Revisar directo', 'hecho': bool(state.get('checked_live')), 'url':'/live-command-center', 'icono':'🔥'},
        {'key':'picks','titulo':'Ver picks del día', 'hecho': bool(state.get('checked_picks')), 'url':'/picks', 'icono':'🎯'},
        {'key':'radar','titulo':'Mirar radar premium', 'hecho': bool(state.get('checked_radar')), 'url':'/cliente/premium-match-radar', 'icono':'📡'},
        {'key':'shark','titulo':'Preguntar a SHARK', 'hecho': bool(state.get('asked_shark')), 'url':'/cliente/shark-copilot', 'icono':'🧠'},
    ]
    progress = int(sum(1 for x in checklist if x['hecho']) / max(1,len(checklist)) * 100)
    return {'ok': True,'version':'V214','nombre':'Client Retention + Engagement Pro','fecha': datetime.utcnow().isoformat(timespec='seconds') + 'Z','usuario': user,'metricas': counts,'checklist': checklist,'progreso': progress,'mensaje': 'Rutina diaria premium basada solo en datos reales disponibles. No se inventan partidos, marcadores ni picks.'}

@bp_engagement_v214.route('/api/v214/engagement')
def api_engagement_v214():
    return jsonify(_summary())

@bp_engagement_v214.route('/api/v214/engagement/mark/<action>', methods=['POST','GET'])
def api_mark_engagement_v214(action):
    if action not in {'open','live','picks','radar','shark'}:
        action='open'
    _mark(action)
    return jsonify({'ok': True, 'action': action})

@bp_engagement_v214.route('/cliente/engagement')
@bp_engagement_v214.route('/cliente/rutina-diaria')
def cliente_engagement_v214():
    data=_summary()
    return render_template_string(TPL, data=data, admin=False)

@bp_engagement_v214.route('/admin/engagement')
def admin_engagement_v214():
    data=_summary()
    return render_template_string(TPL, data=data, admin=True)

TPL = '''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Rutina diaria - NeMeSiS SHARK PRO</title><style>:root{--bg:#060d18;--card:#0c1a2d;--txt:#eef7ff;--muted:#96abc4;--line:rgba(255,255,255,.11);--gold:#f4c85a;--blue:#36a3ff;--ok:#35e399}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 20% 0,#17365f 0,#07111e 38%,#030712 100%);font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial;color:var(--txt);padding-bottom:90px}.wrap{max-width:1160px;margin:0 auto;padding:16px}.bar{display:flex;gap:10px;justify-content:space-between;align-items:center}.back{color:var(--txt);text-decoration:none;border:1px solid var(--line);padding:10px 12px;border-radius:14px;background:rgba(255,255,255,.045)}.hero{margin-top:14px;border:1px solid var(--line);border-radius:26px;padding:18px;background:linear-gradient(135deg,rgba(54,163,255,.18),rgba(244,200,90,.08));box-shadow:0 18px 60px rgba(0,0,0,.32)}.hero h1{margin:0;font-size:clamp(26px,7vw,44px);line-height:1}.hero p{color:var(--muted);margin:8px 0 0}.progress{margin-top:16px;background:rgba(255,255,255,.07);border:1px solid var(--line);border-radius:999px;height:16px;overflow:hidden}.progress div{height:100%;width:{{data.progreso}}%;background:linear-gradient(90deg,var(--blue),var(--gold));border-radius:999px}.metrics{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin:16px 0}.metric{background:rgba(255,255,255,.055);border:1px solid var(--line);border-radius:18px;padding:12px}.metric b{display:block;font-size:24px}.metric span{font-size:12px;color:var(--muted)}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}.card{background:linear-gradient(180deg,var(--card),rgba(12,26,45,.83));border:1px solid var(--line);border-radius:22px;padding:15px;box-shadow:0 14px 38px rgba(0,0,0,.24)}.card.done{border-color:rgba(53,227,153,.35);background:linear-gradient(180deg,rgba(53,227,153,.10),rgba(12,26,45,.86))}.icon{font-size:28px}.card h3{margin:8px 0 6px}.muted{color:var(--muted);font-size:13px}.btn{display:inline-flex;margin-top:12px;color:#06111d;text-decoration:none;background:linear-gradient(90deg,#dff3ff,#f4c85a);padding:10px 12px;border-radius:14px;font-weight:900}.btn2{display:inline-flex;margin-top:12px;color:var(--txt);text-decoration:none;background:rgba(255,255,255,.075);border:1px solid var(--line);padding:10px 12px;border-radius:14px;font-weight:800}.section h2{font-size:20px}.note{margin-top:16px;border:1px dashed var(--line);border-radius:18px;padding:14px;color:var(--muted);background:rgba(255,255,255,.035)}.nav{position:fixed;left:10px;right:10px;bottom:10px;display:grid;grid-template-columns:repeat(5,1fr);gap:8px;background:rgba(6,13,24,.90);backdrop-filter:blur(16px);border:1px solid var(--line);border-radius:22px;padding:8px}.nav a{text-align:center;color:var(--txt);text-decoration:none;font-size:12px;padding:8px 2px;border-radius:14px}.nav a.active{background:rgba(54,163,255,.18)}@media(max-width:720px){.wrap{padding:12px}.metrics{grid-template-columns:repeat(2,1fr)}.grid{grid-template-columns:1fr}.hero{border-radius:22px;padding:16px}}</style><script>function mark(action,url){fetch('/api/v214/engagement/mark/'+action).catch(()=>{}); setTimeout(()=>{location.href=url},120); return false;}</script></head><body><div class="wrap"><div class="bar"><a class="back" href="javascript:history.back()">← Atrás</a><a class="back" href="javascript:history.forward()">Adelante →</a></div><section class="hero"><h1>Rutina diaria SHARK</h1><p>Una pantalla para que el cliente sepa qué revisar cada día sin perderse: directo, picks, radar y SHARK AI.</p><div class="progress"><div></div></div><p><b>{{data.progreso}}%</b> completado hoy</p></section><div class="metrics"><div class="metric"><b>{{data.metricas.partidos}}</b><span>partidos reales</span></div><div class="metric"><b>{{data.metricas.directo}}</b><span>en directo</span></div><div class="metric"><b>{{data.metricas.picks}}</b><span>picks</span></div><div class="metric"><b>{{data.metricas.notificaciones}}</b><span>avisos</span></div><div class="metric"><b>{{data.metricas.radar}}</b><span>radar</span></div></div><section class="section"><h2>Qué mirar ahora</h2><div class="grid">{% for item in data.checklist %}<article class="card {% if item.hecho %}done{% endif %}"><div class="icon">{{item.icono}}</div><h3>{{item.titulo}}</h3><div class="muted">{% if item.hecho %}Ya revisado hoy.{% else %}Pendiente para completar tu rutina diaria.{% endif %}</div><a class="{% if item.hecho %}btn2{% else %}btn{% endif %}" onclick="return mark('{{item.key}}','{{item.url}}')" href="{{item.url}}">{% if item.hecho %}Volver a abrir{% else %}Abrir ahora{% endif %}</a></article>{% endfor %}</div></section><div class="note"><b>REAL ONLY:</b> {{data.mensaje}}</div>{% if admin %}<div class="note"><b>Admin:</b> Esta vista ayuda a medir retención y hábitos sin enseñar datos técnicos al cliente.</div>{% endif %}</div><nav class="nav"><a href="/cliente/inicio-inteligente">Inicio</a><a href="/picks">Picks</a><a href="/live-command-center">Live</a><a class="active" href="/cliente/rutina-diaria">Rutina</a><a href="/cliente/pro">Cuenta</a></nav></body></html>'''
