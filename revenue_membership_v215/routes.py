# -*- coding: utf-8 -*-
import os, sqlite3
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, render_template_string, session

bp_revenue_membership_v215 = Blueprint('revenue_membership_v215', __name__)
DB_PATH = os.environ.get('DB_PATH', '/data/database.db').strip() or '/data/database.db'

PLANS = {
    'FREE': {'nombre':'FREE','precio':0,'color':'azul básico','descripcion':'Entrada gratuita con acceso limitado para probar la plataforma.','incluye':['Partidos del día','Favoritos básicos','Resumen limitado']},
    'PRO': {'nombre':'PRO','precio':19.99,'color':'azul premium','descripcion':'Experiencia premium para usuarios activos.','incluye':['Picks premium','Radar de partidos','Alertas inteligentes','Estadísticas avanzadas']},
    'ELITE': {'nombre':'ELITE','precio':49.99,'color':'dorado premium','descripcion':'Máximo nivel para usuarios exigentes y seguimiento avanzado.','incluye':['SHARK AI Copilot','Señales avanzadas','Movimiento de cuotas','ML Explainability','Telegram premium']},
}
FEATURE_MATRIX = [
    ('Partidos reales', True, True, True), ('Favoritos', True, True, True), ('Picks diarios','Limitado',True,True),
    ('Live Command Center','Limitado',True,True), ('Radar premium',False,True,True), ('Movimiento de cuotas',False,True,True),
    ('SHARK AI Copilot',False,True,True), ('Alertas Telegram premium',False,'Limitado',True), ('ML Explainability',False,'Resumen',True)
]
PAGE = '''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{{ title }}</title><style>
body{margin:0;background:#06111f;color:#edf7ff;font-family:system-ui,-apple-system,Segoe UI,sans-serif}.wrap{max-width:1100px;margin:auto;padding:22px 16px 90px}.top{display:flex;justify-content:space-between;gap:12px;align-items:center;margin-bottom:18px}.back{color:#9bdcff;text-decoration:none;border:1px solid #1e4968;border-radius:999px;padding:9px 13px;background:#0a1b2c}.hero{background:linear-gradient(135deg,#062640,#0b4f76 55%,#102238);border:1px solid #1e668a;border-radius:26px;padding:22px;box-shadow:0 18px 60px #0008}.hero h1{margin:0 0 8px;font-size:clamp(26px,7vw,48px)}.hero p{color:#b9d8e8;margin:0;line-height:1.45}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin-top:16px}.card{background:#0a1828;border:1px solid #173c58;border-radius:22px;padding:16px;box-shadow:0 12px 35px #0004}.metric{font-size:34px;font-weight:800}.muted{color:#9db6c7}.badge{display:inline-flex;gap:6px;align-items:center;padding:7px 10px;border-radius:999px;background:#102b42;border:1px solid #235a7c;color:#bceaff;font-size:13px}.price{font-size:30px;font-weight:900;margin:8px 0}.btn{display:inline-block;margin-top:10px;text-decoration:none;color:#06111f;background:#4fe3ff;border-radius:14px;padding:10px 14px;font-weight:800}.table{width:100%;border-collapse:collapse;margin-top:10px}.table td,.table th{padding:10px;border-bottom:1px solid #173c58;text-align:left}.ok{color:#6dffb0}.no{color:#ff8a8a}.bigwarn{margin-top:18px;background:#2d1d03;border:1px solid #f0ad28;color:#ffe6ad;border-radius:22px;padding:16px;font-weight:800;font-size:clamp(18px,5vw,32px)}@media(max-width:680px){.top{align-items:flex-start;flex-direction:column}.wrap{padding:14px 12px 80px}.hero{padding:18px;border-radius:22px}.card{border-radius:18px}.table{font-size:13px}}
</style></head><body><main class="wrap"><div class="top"><a class="back" href="javascript:history.back()">← Atrás</a><span class="badge">V215 · Comercialización real</span></div>{{ body|safe }}</main></body></html>'''

def _connect():
    os.makedirs(os.path.dirname(DB_PATH) or '.', exist_ok=True)
    con=sqlite3.connect(DB_PATH, timeout=10); con.row_factory=sqlite3.Row; return con

def _init():
    with _connect() as con:
        con.execute('CREATE TABLE IF NOT EXISTS v215_upgrade_intents (id INTEGER PRIMARY KEY AUTOINCREMENT,user_id TEXT,email TEXT,plan_objetivo TEXT,origen TEXT,estado TEXT DEFAULT "pendiente",created_at TEXT)')
        con.execute('CREATE TABLE IF NOT EXISTS v215_commercial_snapshots (id INTEGER PRIMARY KEY AUTOINCREMENT,total_usuarios INTEGER DEFAULT 0,free_count INTEGER DEFAULT 0,pro_count INTEGER DEFAULT 0,elite_count INTEGER DEFAULT 0,ingresos_estimados REAL DEFAULT 0,created_at TEXT)')

def _now(): return datetime.now(timezone.utc).isoformat()

def _current_user():
    return {'id':str(session.get('user_id') or session.get('client_id') or session.get('id') or ''),'email':str(session.get('email') or session.get('user_email') or ''),'nombre':str(session.get('username') or session.get('name') or session.get('client_name') or 'Usuario'),'membership':str(session.get('membership') or session.get('plan') or session.get('role') or 'FREE').upper()}

def _user_counts():
    counts={'total':0,'FREE':0,'PRO':0,'ELITE':0,'UNKNOWN':0}
    try:
        with _connect() as con:
            tables=[r['name'] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            table='users' if 'users' in tables else ('clientes' if 'clientes' in tables else None)
            if not table: return counts
            cols=[r['name'] for r in con.execute(f'PRAGMA table_info({table})').fetchall()]
            plan_col=next((c for c in ['membership','plan','role','tier'] if c in cols), None)
            if not plan_col: return counts
            rows=con.execute(f'SELECT {plan_col} AS plan FROM {table}').fetchall(); counts['total']=len(rows)
            for r in rows:
                p=str(r['plan'] or 'UNKNOWN').upper()
                if 'ELITE' in p: counts['ELITE']+=1
                elif 'PRO' in p or 'VIP' in p: counts['PRO']+=1
                elif 'FREE' in p: counts['FREE']+=1
                else: counts['UNKNOWN']+=1
    except Exception: pass
    return counts

def _commercial_snapshot(save=False):
    c=_user_counts(); ingresos=round(c['PRO']*PLANS['PRO']['precio'] + c['ELITE']*PLANS['ELITE']['precio'],2)
    data={'usuarios_total':c['total'],'free':c['FREE'],'pro':c['PRO'],'elite':c['ELITE'],'desconocidos':c['UNKNOWN'],'ingresos_mensuales_estimados':ingresos,'nota':'Estimación basada en planes, no confirma pagos reales.','created_at':_now()}
    if save:
        with _connect() as con: con.execute('INSERT INTO v215_commercial_snapshots(total_usuarios,free_count,pro_count,elite_count,ingresos_estimados,created_at) VALUES (?,?,?,?,?,?)',(c['total'],c['FREE'],c['PRO'],c['ELITE'],ingresos,data['created_at']))
    return data

def _yes(v):
    if v is True: return '<span class="ok">Sí</span>'
    if v is False: return '<span class="no">No</span>'
    return str(v)

def _matrix_html():
    rows=''.join([f'<tr><td>{name}</td><td>{_yes(free)}</td><td>{_yes(pro)}</td><td>{_yes(elite)}</td></tr>' for name,free,pro,elite in FEATURE_MATRIX])
    return f'<table class="table"><thead><tr><th>Función</th><th>FREE</th><th>PRO</th><th>ELITE</th></tr></thead><tbody>{rows}</tbody></table>'

@bp_revenue_membership_v215.before_app_request
def ensure_v215_tables():
    if not getattr(ensure_v215_tables, '_done', False): _init(); ensure_v215_tables._done=True

@bp_revenue_membership_v215.route('/admin/revenue-control')
def admin_revenue_control():
    _init(); snap=_commercial_snapshot(save=True)
    body=f'''<section class="hero"><h1>Centro comercial SHARK PRO</h1><p>Control de membresías, estimación comercial y preparación para monetización sin activar pagos reales todavía.</p></section><div class="bigwarn">FALTA INSTALAR/ACTIVAR: PASARELA DE PAGO REAL SI QUIERES COBRAR AUTOMÁTICAMENTE</div><section class="grid"><div class="card"><div class="muted">Usuarios totales</div><div class="metric">{snap['usuarios_total']}</div></div><div class="card"><div class="muted">FREE</div><div class="metric">{snap['free']}</div></div><div class="card"><div class="muted">PRO</div><div class="metric">{snap['pro']}</div></div><div class="card"><div class="muted">ELITE</div><div class="metric">{snap['elite']}</div></div><div class="card"><div class="muted">Estimación mensual</div><div class="metric">{snap['ingresos_mensuales_estimados']}€</div><p class="muted">No confirma pagos reales.</p></div></section><section class="card" style="margin-top:16px"><h2>Matriz de acceso</h2>{_matrix_html()}</section>'''
    return render_template_string(PAGE,title='Admin · Revenue Control V215',body=body)

@bp_revenue_membership_v215.route('/cliente/membresia-pro')
def cliente_membresia_pro():
    _init(); u=_current_user(); plan=PLANS.get(u['membership'],PLANS['FREE'])
    cards=''.join([f'''<div class="card"><span class="badge">{p['nombre']}</span><h2>{p['nombre']}</h2><p class="muted">{p['descripcion']}</p><div class="price">{p['precio']}€<span class="muted" style="font-size:14px">/mes</span></div><ul>{''.join(f'<li>{x}</li>' for x in p['incluye'])}</ul><a class="btn" href="/cliente/upgrade?plan={p['nombre']}">Quiero {p['nombre']}</a></div>''' for p in PLANS.values()])
    body=f'''<section class="hero"><h1>Tu membresía</h1><p>Hola {u['nombre']}. Tu plan actual es <b>{plan['nombre']}</b>. Aquí puedes ver qué incluye cada nivel.</p></section><section class="grid">{cards}</section><section class="card" style="margin-top:16px"><h2>Comparativa</h2>{_matrix_html()}</section>'''
    return render_template_string(PAGE,title='Cliente · Membresía V215',body=body)

@bp_revenue_membership_v215.route('/cliente/upgrade')
def cliente_upgrade():
    _init(); u=_current_user(); target=(request.args.get('plan') or 'PRO').upper()
    if target not in PLANS: target='PRO'
    with _connect() as con: con.execute('INSERT INTO v215_upgrade_intents(user_id,email,plan_objetivo,origen,estado,created_at) VALUES (?,?,?,?,?,?)',(u['id'],u['email'],target,'cliente','pendiente',_now()))
    body=f'''<section class="hero"><h1>Solicitud de mejora registrada</h1><p>Has marcado interés por el plan <b>{target}</b>. Por ahora esto no cobra automáticamente: queda preparado para que el admin lo revise o para conectar pagos reales más adelante.</p></section><div class="bigwarn">FALTA ACTIVAR COBRO AUTOMÁTICO SI QUIERES QUE EL USUARIO PAGUE DIRECTAMENTE</div><section class="card" style="margin-top:16px"><a class="btn" href="/cliente/membresia-pro">Volver a membresías</a></section>'''
    return render_template_string(PAGE,title='Upgrade V215',body=body)

@bp_revenue_membership_v215.route('/api/v215/revenue/status')
def api_revenue_status():
    _init(); return jsonify({'ok':True,'version':'V215','nombre':'Revenue & Membership Control Pro','planes':PLANS,'snapshot':_commercial_snapshot(False),'real_only':True})

@bp_revenue_membership_v215.route('/api/v215/upgrade-intent', methods=['POST'])
def api_upgrade_intent():
    _init(); u=_current_user(); data=request.get_json(silent=True) or {}; target=str(data.get('plan') or 'PRO').upper()
    if target not in PLANS: target='PRO'
    with _connect() as con: con.execute('INSERT INTO v215_upgrade_intents(user_id,email,plan_objetivo,origen,estado,created_at) VALUES (?,?,?,?,?,?)',(u['id'],u['email'],target,'api','pendiente',_now()))
    return jsonify({'ok':True,'mensaje':'Interés registrado sin cobro automático.','plan':target})
