import os
import sqlite3
from pathlib import Path
from datetime import datetime
from flask import Blueprint, jsonify, render_template_string, session

bp_daily_hub_v213 = Blueprint('daily_hub_v213', __name__)


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


def _cols(cur, table):
    try:
        return {r['name'] for r in cur.execute(f"PRAGMA table_info({table})").fetchall()}
    except Exception:
        return set()


def _now():
    return datetime.utcnow().isoformat(timespec='seconds') + 'Z'


def _user():
    u = session.get('user') or {}
    return {
        'id': u.get('id') or 0,
        'username': u.get('username') or 'Usuario',
        'plan': (u.get('plan') or 'FREE').upper(),
        'role': u.get('role') or 'cliente'
    }


def _safe_int(v, default=0):
    try:
        if v in (None, ''):
            return default
        return int(float(v))
    except Exception:
        return default


def _fixture_candidates(limit=40):
    """Lee partidos reales desde V209/V146/picks. No inventa partidos."""
    items = []
    try:
        from live_score_incidents_v209.routes import _live_payload
        payload = _live_payload(limit=limit)
        for r in payload.get('matches', []) or payload.get('partidos', []) or []:
            items.append({
                'tipo': 'partido',
                'titulo': r.get('title') or r.get('titulo') or ' vs '.join([x for x in [r.get('home_team'), r.get('away_team')] if x]) or 'Partido real',
                'competicion': r.get('league') or r.get('competition') or r.get('competicion') or 'Competición no indicada',
                'estado': r.get('status_label') or r.get('status') or r.get('estado') or 'Estado pendiente del proveedor',
                'minuto': r.get('minute') or r.get('minuto') or '',
                'marcador': r.get('score') or r.get('marcador') or '',
                'url': r.get('url') or '/live-command-center',
                'prioridad': _safe_int(r.get('priority') or r.get('radar_score') or r.get('danger_level'), 20)
            })
    except Exception:
        pass
    try:
        con = _connect(); cur = con.cursor(); tables = _tables(cur)
        if 'real_fixtures_v146' in tables:
            c = _cols(cur, 'real_fixtures_v146')
            sel = [x for x in ['id','home_team','away_team','league','competition','status','kickoff','start_time','minute','score_home','score_away','live_score'] if x in c]
            if sel:
                cur.execute(f"SELECT {','.join(sel)} FROM real_fixtures_v146 ORDER BY COALESCE(kickoff,start_time,'') ASC LIMIT ?", (limit,))
                for row in cur.fetchall():
                    d=dict(row)
                    title=' vs '.join([x for x in [d.get('home_team'), d.get('away_team')] if x]) or 'Partido real'
                    score = d.get('live_score') or ''
                    if not score and d.get('score_home') is not None and d.get('score_away') is not None:
                        score = f"{d.get('score_home')} - {d.get('score_away')}"
                    items.append({'tipo':'partido','titulo':title,'competicion':d.get('league') or d.get('competition') or 'Competición no indicada','estado':d.get('status') or 'Programado','minuto':d.get('minute') or '', 'marcador': score, 'url':'/home-live-real','prioridad':25})
        if 'picks' in tables:
            c = _cols(cur, 'picks')
            sel = [x for x in ['id','title','match_name','home_team','away_team','league','competition','pick','selection','confidence','score','odds','live_status','live_score','live_minute','created_at','kickoff_time'] if x in c]
            if sel:
                cur.execute(f"SELECT {','.join(sel)} FROM picks ORDER BY COALESCE(kickoff_time,created_at,'') DESC LIMIT ?", (limit,))
                for row in cur.fetchall():
                    d=dict(row)
                    title=d.get('match_name') or d.get('title') or ' vs '.join([x for x in [d.get('home_team'), d.get('away_team')] if x]) or 'Pick real'
                    items.append({'tipo':'pick','titulo':title,'competicion':d.get('league') or d.get('competition') or 'Competición no indicada','estado':d.get('live_status') or 'Pick disponible','minuto':d.get('live_minute') or '', 'marcador': d.get('live_score') or '', 'pick': d.get('pick') or d.get('selection') or '', 'cuota': d.get('odds') or '', 'confianza': d.get('confidence') or d.get('score') or '', 'url':'/picks','prioridad':35 + _safe_int(d.get('confidence') or d.get('score'), 0)//5})
        con.close()
    except Exception:
        pass
    seen=set(); out=[]
    for i in items:
        key=(str(i.get('tipo')), str(i.get('titulo')).lower(), str(i.get('competicion')).lower())
        if key in seen:
            continue
        seen.add(key); out.append(i)
    out.sort(key=lambda x: x.get('prioridad',0), reverse=True)
    return out[:limit]


def _notifications_count():
    try:
        con = _connect(); cur = con.cursor(); tables=_tables(cur)
        count=0
        for table in ['smart_notifications_v205','notifications_v205','user_notifications_v205']:
            if table in tables:
                try:
                    count += cur.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()['n']
                except Exception:
                    pass
        con.close(); return count
    except Exception:
        return 0


def _summary():
    user = _user(); items = _fixture_candidates(50)
    live = [x for x in items if 'directo' in str(x.get('estado','')).lower() or 'live' in str(x.get('estado','')).lower() or x.get('minuto')]
    picks = [x for x in items if x.get('tipo') == 'pick']
    hot = [x for x in items if x.get('prioridad',0) >= 40]
    return {'ok': True,'version': 'V213','nombre': 'Daily Smart Hub PRO','fecha': _now(),'usuario': user,'metricas': {'items_reales': len(items),'en_directo': len(live),'picks': len(picks),'destacados': len(hot),'notificaciones': _notifications_count()},'destacados': hot[:8],'directo': live[:8],'picks': picks[:8],'feed': items[:16],'estado_real_only': 'Sin datos inventados. Si el proveedor no manda marcador/incidencias, se muestra aviso limpio.'}


@bp_daily_hub_v213.route('/api/v213/daily-hub')
def api_daily_hub_v213():
    return jsonify(_summary())


@bp_daily_hub_v213.route('/cliente/daily-hub')
@bp_daily_hub_v213.route('/cliente/inicio-inteligente')
def cliente_daily_hub_v213():
    data = _summary()
    return render_template_string(TPL, data=data, admin=False)


@bp_daily_hub_v213.route('/admin/daily-hub')
def admin_daily_hub_v213():
    data = _summary()
    return render_template_string(TPL, data=data, admin=True)


TPL = '''
<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Inicio inteligente · NeMeSiS SHARK PRO</title>
<style>:root{--bg:#07111f;--card:#0d1b2f;--txt:#eef6ff;--muted:#9eb4cc;--line:rgba(255,255,255,.10);--blue:#3aa8ff}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top,#12325a 0,#07111f 42%,#050913 100%);font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial;color:var(--txt);padding-bottom:84px}.wrap{max-width:1180px;margin:0 auto;padding:16px}.top{display:flex;gap:12px;justify-content:space-between}.back{color:var(--txt);text-decoration:none;border:1px solid var(--line);padding:10px 12px;border-radius:14px;background:rgba(255,255,255,.04)}.hero{margin-top:14px;padding:18px;border:1px solid var(--line);border-radius:24px;background:linear-gradient(135deg,rgba(58,168,255,.16),rgba(245,196,81,.08));box-shadow:0 18px 60px rgba(0,0,0,.28)}.hero h1{margin:0 0 8px;font-size:clamp(24px,6vw,42px);line-height:1}.hero p{margin:0;color:var(--muted);font-size:15px}.metrics{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin:14px 0}.metric{background:rgba(255,255,255,.055);border:1px solid var(--line);border-radius:18px;padding:12px}.metric b{display:block;font-size:22px}.metric span{color:var(--muted);font-size:12px}.quick{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin:14px 0}.q{display:block;text-align:center;text-decoration:none;color:var(--txt);background:var(--card);border:1px solid var(--line);border-radius:18px;padding:13px 8px;font-weight:800}.section{margin-top:20px}.section h2{font-size:20px;margin:0 0 10px}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}.card{background:linear-gradient(180deg,var(--card),rgba(13,27,47,.82));border:1px solid var(--line);border-radius:22px;padding:14px;box-shadow:0 14px 38px rgba(0,0,0,.22)}.pill{display:inline-flex;font-size:12px;border:1px solid var(--line);border-radius:999px;padding:5px 9px;color:#cde5ff;background:rgba(58,168,255,.10)}.card h3{margin:10px 0 6px;font-size:17px}.muted{color:var(--muted);font-size:13px}.score{font-size:26px;font-weight:950;letter-spacing:.5px}.actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}.btn{color:var(--txt);text-decoration:none;background:rgba(255,255,255,.07);border:1px solid var(--line);padding:8px 10px;border-radius:12px;font-size:13px;font-weight:800}.empty{border:1px dashed var(--line);border-radius:20px;padding:18px;color:var(--muted);background:rgba(255,255,255,.035)}.nav{position:fixed;left:10px;right:10px;bottom:10px;display:grid;grid-template-columns:repeat(5,1fr);gap:8px;background:rgba(7,17,31,.88);backdrop-filter:blur(16px);border:1px solid var(--line);border-radius:22px;padding:8px;z-index:5}.nav a{text-align:center;color:var(--txt);text-decoration:none;font-size:12px;padding:8px 2px;border-radius:14px}.nav a.active{background:rgba(58,168,255,.18);color:#d9efff}@media(max-width:720px){.wrap{padding:12px}.metrics{grid-template-columns:repeat(2,1fr)}.quick{grid-template-columns:repeat(3,1fr)}.grid{grid-template-columns:1fr}.hero{padding:15px;border-radius:20px}}</style></head><body><div class="wrap"><div class="top"><a class="back" href="javascript:history.back()">← Atrás</a><a class="back" href="javascript:history.forward()">Adelante →</a></div><section class="hero"><h1>Inicio inteligente SHARK</h1><p>Resumen diario con partidos, directo, picks, alertas y oportunidades reales. Todo se muestra solo si existe dato real en el sistema.</p></section><div class="metrics"><div class="metric"><b>{{data.metricas.items_reales}}</b><span>items reales</span></div><div class="metric"><b>{{data.metricas.en_directo}}</b><span>en directo</span></div><div class="metric"><b>{{data.metricas.picks}}</b><span>picks</span></div><div class="metric"><b>{{data.metricas.destacados}}</b><span>destacados</span></div><div class="metric"><b>{{data.metricas.notificaciones}}</b><span>avisos</span></div></div><div class="quick"><a class="q" href="/live-command-center">🔥 Directo</a><a class="q" href="/cliente/premium-match-radar">📡 Radar</a><a class="q" href="/picks">⭐ Picks</a><a class="q" href="/cliente/shark-copilot">🧠 SHARK</a><a class="q" href="/cliente/favoritos">❤️ Favoritos</a></div>{% for title, arr in [('🔥 Destacados ahora', data.destacados), ('⚡ En directo', data.directo), ('🎯 Picks reales', data.picks)] %}<section class="section"><h2>{{title}}</h2>{% if arr %}<div class="grid">{% for item in arr %}<article class="card"><span class="pill">{{item.tipo|upper}} · {{item.estado}}</span><h3>{{item.titulo}}</h3><div class="muted">{{item.competicion}}</div>{% if item.marcador %}<div class="score">{{item.marcador}}</div>{% endif %}{% if item.minuto %}<div class="muted">Minuto: {{item.minuto}}</div>{% endif %}{% if item.pick %}<div class="muted">Pick: {{item.pick}}</div>{% endif %}<div class="actions"><a class="btn" href="{{item.url}}">Abrir</a><a class="btn" href="/cliente/shark-copilot">Preguntar a SHARK</a></div></article>{% endfor %}</div>{% else %}<div class="empty">No hay datos reales disponibles ahora para esta sección. Cuando el proveedor mande información, aparecerá aquí automáticamente.</div>{% endif %}</section>{% endfor %}<section class="section"><div class="empty"><b>REAL ONLY:</b> {{data.estado_real_only}}</div></section></div><nav class="nav"><a class="active" href="/cliente/inicio-inteligente">Inicio</a><a href="/picks">Picks</a><a href="/live-command-center">Live</a><a href="/cliente/favoritos">Favoritos</a><a href="/cliente/pro">Cuenta</a></nav></body></html>
'''
