from flask import Blueprint, jsonify, request, render_template_string, session
import os, sqlite3, json, hashlib, time
from pathlib import Path
from datetime import datetime

bp_live_events_real_v196 = Blueprint("live_events_real_v196", __name__)
VERSION = "V196_LIVE_EVENTS_REAL_EXPANSION_PRO"


def _db_path():
    for p in [os.environ.get("DATABASE_PATH"), os.environ.get("DB_PATH"), "/data/database.db", "/data/app.db", "database.db", "app.db"]:
        if p:
            try:
                if str(p).startswith('/data'):
                    Path(p).parent.mkdir(parents=True, exist_ok=True)
                if Path(p).exists() or str(p).startswith('/data'):
                    return p
            except Exception:
                pass
    return "database.db"


def _connect():
    con = sqlite3.connect(_db_path())
    con.row_factory = sqlite3.Row
    return con


def _init():
    con = _connect()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS live_events_audit_v196 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT,
            status TEXT,
            matches_seen INTEGER DEFAULT 0,
            events_seen INTEGER DEFAULT 0,
            detail TEXT,
            created_at INTEGER
        )
    """)
    con.commit(); con.close()


def _tables(con):
    try:
        return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    except Exception:
        return set()


def _cols(con, table):
    try:
        return [r[1] for r in con.execute(f"PRAGMA table_info({table})").fetchall()]
    except Exception:
        return []


def _rows(con, table, limit=250):
    if table not in _tables(con):
        return []
    cols = _cols(con, table)
    order = "rowid DESC"
    for c in ["created_at", "updated_at", "minute", "elapsed", "kickoff", "commence_time", "date"]:
        if c in cols:
            order = f"COALESCE({c}, '') DESC"
            break
    try:
        return [dict(r) for r in con.execute(f"SELECT * FROM {table} ORDER BY {order} LIMIT ?", (int(limit),)).fetchall()]
    except Exception:
        try:
            return [dict(r) for r in con.execute(f"SELECT * FROM {table} LIMIT ?", (int(limit),)).fetchall()]
        except Exception:
            return []


def _pick(row, names, fallback=""):
    lower = {str(k).lower(): k for k in row.keys()}
    for n in names:
        key = lower.get(n.lower())
        if key is not None and row.get(key) not in (None, ""):
            return row.get(key)
    for k in row.keys():
        lk = str(k).lower()
        if any(n.lower() in lk for n in names) and row.get(k) not in (None, ""):
            return row.get(k)
    return fallback


def _safe(v, fb="Pendiente"):
    v = "" if v is None else str(v).strip()
    return v or fb


def _num(v, default=None):
    try:
        if v in (None, ""):
            return default
        return int(float(str(v).replace(',', '.')))
    except Exception:
        return default


def _stable_id(row):
    return hashlib.md5(json.dumps(row, default=str, sort_keys=True).encode('utf-8')).hexdigest()[:14]


def _is_live(status):
    s = str(status or '').lower()
    return any(x in s for x in ["live", "inplay", "in_play", "1h", "2h", "ht", "directo", "descanso"])


def _is_finished(status):
    s = str(status or '').lower()
    return any(x in s for x in ["finished", "final", "ended", "ft", "terminado", "finalizado"])


def _normalize_match(row, source):
    status = _safe(_pick(row, ["status", "state", "match_status", "fixture_status", "estado"]), "Programado")
    mid = str(_pick(row, ["match_id", "fixture_id", "event_id", "id"], "") or _stable_id(row))
    home = _safe(_pick(row, ["home_team", "home", "team_home", "local", "equipo_local"]), "Local")
    away = _safe(_pick(row, ["away_team", "away", "team_away", "visitor", "visitante", "equipo_visitante"]), "Visitante")
    league = _safe(_pick(row, ["league", "competition", "competition_name", "sport_title", "liga"]), "Competición real")
    kickoff = _safe(_pick(row, ["kickoff", "commence_time", "start_time", "date", "hora"], ""), "")
    return {
        "id": mid,
        "titulo": f"{home} vs {away}",
        "local": home,
        "visitante": away,
        "liga": league,
        "estado": status.upper(),
        "hora": kickoff,
        "minuto": _safe(_pick(row, ["minute", "elapsed", "minuto"], ""), ""),
        "marcador_local": _num(_pick(row, ["home_score", "score_home", "goals_home", "home_goals", "local_score"]), None),
        "marcador_visitante": _num(_pick(row, ["away_score", "score_away", "goals_away", "away_goals", "visitor_score"]), None),
        "en_directo": _is_live(status),
        "finalizado": _is_finished(status),
        "fuente": source,
    }


def _match_rows(con):
    out = []
    for t in ["fixtures_cache", "fixtures", "real_fixtures", "matches_cache", "matches", "events"]:
        for r in _rows(con, t, 200):
            out.append(_normalize_match(r, t))
    # Deduplicar por id/título/hora
    seen, clean = set(), []
    for m in out:
        key = (m["id"], m["titulo"], m["hora"])
        if key not in seen:
            seen.add(key); clean.append(m)
    clean.sort(key=lambda x: (not x["en_directo"], x.get("hora") or ""))
    return clean[:120]


def _event_type_es(raw):
    s = str(raw or '').lower()
    if any(x in s for x in ["goal", "gol"]): return "Gol"
    if any(x in s for x in ["yellow", "amarilla"]): return "Tarjeta amarilla"
    if any(x in s for x in ["red", "roja"]): return "Tarjeta roja"
    if any(x in s for x in ["sub", "sustit"]): return "Sustitución"
    if any(x in s for x in ["penalty", "penalti", "penal"]): return "Penalti"
    if "var" in s: return "VAR"
    if any(x in s for x in ["corner", "saque"]): return "Córner"
    if any(x in s for x in ["half", "descanso", "ht"]): return "Descanso"
    if any(x in s for x in ["finish", "final", "ft"]): return "Final"
    if any(x in s for x in ["start", "inicio"]): return "Inicio"
    return _safe(raw, "Incidente real")


def _normalize_event(row, source):
    mid = str(_pick(row, ["match_id", "fixture_id", "event_id", "id_partido"], ""))
    etype = _event_type_es(_pick(row, ["type", "event_type", "incident_type", "tipo", "name"], "Incidente real"))
    minute = _safe(_pick(row, ["minute", "elapsed", "time", "minuto"], "—"), "—")
    team = _safe(_pick(row, ["team", "team_name", "equipo"], ""), "")
    player = _safe(_pick(row, ["player", "player_name", "jugador"], ""), "")
    text = _safe(_pick(row, ["description", "detail", "comment", "texto", "title"], ""), "")
    return {
        "match_id": mid,
        "minuto": str(minute),
        "tipo": etype,
        "equipo": team,
        "jugador": player,
        "descripcion": text,
        "fuente": source,
        "tono": _tone_for_event(etype),
    }


def _tone_for_event(etype):
    s = str(etype).lower()
    if "gol" in s or "penalti" in s: return "danger"
    if "roja" in s or "var" in s: return "alert"
    if "amarilla" in s: return "warning"
    if "sustit" in s: return "info"
    if "final" in s or "descanso" in s: return "neutral"
    return "soft"


def _event_rows(con):
    out = []
    for t in ["match_events", "live_events", "incidents", "fixture_events", "timeline_events", "events_live"]:
        for r in _rows(con, t, 300):
            out.append(_normalize_event(r, t))
    return out[:300]


def _badges_for(match, events):
    badges = []
    if match.get("en_directo"):
        badges.append({"texto": "EN DIRECTO", "tono": "live"})
    if match.get("finalizado"):
        badges.append({"texto": "FINALIZADO", "tono": "neutral"})
    labels = [e.get("tipo", "") for e in events]
    if any("Gol" == x for x in labels): badges.append({"texto": "Gol registrado", "tono": "danger"})
    if any("Tarjeta roja" == x for x in labels): badges.append({"texto": "Roja", "tono": "alert"})
    if any("Penalti" == x for x in labels): badges.append({"texto": "Penalti", "tono": "danger"})
    if any("VAR" == x for x in labels): badges.append({"texto": "VAR", "tono": "alert"})
    if events and len(events) >= 5: badges.append({"texto": "Timeline activo", "tono": "info"})
    if not badges:
        badges.append({"texto": "Sin eventos live del proveedor", "tono": "soft"})
    return badges[:6]


def build_live_events_real(match_id=None):
    _init()
    con = _connect()
    try:
        matches = _match_rows(con)
        events = _event_rows(con)
        selected = None
        if match_id:
            selected = next((m for m in matches if str(m.get("id")) == str(match_id)), None)
        if not selected and matches:
            selected = next((m for m in matches if m.get("en_directo")), matches[0])
        if selected:
            sid = str(selected.get("id"))
            stitle = selected.get("titulo", "")
            evs = [e for e in events if e.get("match_id") and str(e.get("match_id")) == sid]
            # Si el proveedor no relaciona match_id, no se inventa: solo usamos eventos que vengan asociados.
            selected["eventos"] = evs[:40]
            selected["badges"] = _badges_for(selected, evs)
        live = [m for m in matches if m.get("en_directo")]
        payload = {
            "ok": True,
            "version": VERSION,
            "generado": datetime.utcnow().isoformat() + "Z",
            "politica": {"real_only": True, "sin_eventos_fake": True, "sin_marcadores_fake": True, "sin_partidos_fake": True},
            "usuario": str(session.get("username") or session.get("user") or "cliente"),
            "partido_seleccionado": selected,
            "partidos": matches[:60],
            "partidos_directo": live[:20],
            "contadores": {"partidos": len(matches), "directo": len(live), "eventos_reales": len(events)},
            "estado_vacio": not bool(matches),
            "mensaje_vacio": "Ahora mismo no hay partidos/eventos reales disponibles en caché o proveedor. NeMeSiS SHARK PRO no inventa datos.",
        }
        try:
            con.execute("INSERT INTO live_events_audit_v196(action,status,matches_seen,events_seen,detail,created_at) VALUES(?,?,?,?,?,?)", ("build", "ok", len(matches), len(events), "lectura real only", int(time.time())))
            con.commit()
        except Exception:
            pass
        return payload
    finally:
        con.close()


PAGE = r'''
<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Eventos live reales · NeMeSiS SHARK PRO</title>
<style>
:root{--bg:#061326;--panel:#0b1c34;--panel2:#10294b;--txt:#eef7ff;--mut:#9fb7d3;--line:rgba(120,190,255,.22);--cyan:#55e6ff;--green:#67f7b5;--gold:#ffd76a;--red:#ff6b8b}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 10% 0%,#103b70 0,#061326 42%,#030812 100%);color:var(--txt);font-family:Inter,system-ui,Segoe UI,Arial,sans-serif}.wrap{max-width:1180px;margin:0 auto;padding:22px}.top{display:flex;gap:10px;align-items:center;justify-content:space-between;margin-bottom:14px}.navbtn{border:1px solid var(--line);background:rgba(255,255,255,.05);color:var(--txt);border-radius:999px;padding:10px 14px;text-decoration:none;font-weight:800}.hero{border:1px solid var(--line);background:linear-gradient(135deg,rgba(16,41,75,.96),rgba(8,19,38,.94));border-radius:28px;padding:26px;box-shadow:0 24px 80px rgba(0,0,0,.35)}.kicker{display:inline-flex;border:1px solid rgba(103,247,181,.4);color:var(--green);border-radius:999px;padding:8px 12px;font-weight:900;font-size:13px}h1{font-size:42px;margin:14px 0 8px}.mut{color:var(--mut)}.grid{display:grid;grid-template-columns:1.2fr .8fr;gap:16px;margin-top:16px}.card{border:1px solid var(--line);background:rgba(12,30,56,.72);border-radius:24px;padding:18px}.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:16px}.stat{border:1px solid var(--line);border-radius:18px;padding:14px;background:rgba(255,255,255,.04)}.stat b{font-size:30px}.badge{display:inline-flex;margin:4px 6px 4px 0;padding:7px 10px;border-radius:999px;border:1px solid var(--line);font-size:12px;font-weight:900}.live{color:var(--green);border-color:rgba(103,247,181,.45)}.danger{color:var(--red);border-color:rgba(255,107,139,.48)}.alert{color:#ff9aae;border-color:rgba(255,107,139,.48)}.warning{color:var(--gold);border-color:rgba(255,215,106,.45)}.info{color:var(--cyan)}.timeline{display:flex;flex-direction:column;gap:10px}.event{display:grid;grid-template-columns:72px 1fr;gap:12px;border:1px solid var(--line);border-radius:18px;padding:12px;background:rgba(255,255,255,.035)}.minute{font-size:20px;font-weight:950;color:var(--cyan)}.matches{display:flex;flex-direction:column;gap:10px}.match{display:flex;justify-content:space-between;gap:10px;text-decoration:none;color:var(--txt);border:1px solid var(--line);border-radius:18px;padding:12px;background:rgba(255,255,255,.035)}.score{font-size:24px;font-weight:950;color:var(--green)}.empty{border:1px dashed rgba(255,255,255,.25);border-radius:22px;padding:22px;text-align:center;color:var(--mut)}@media(max-width:850px){.grid{grid-template-columns:1fr}h1{font-size:32px}.stats{grid-template-columns:1fr}.wrap{padding:14px}.hero{padding:20px}}
</style></head><body><div class="wrap">
<div class="top"><div><a class="navbtn" href="javascript:history.back()">← Atrás</a> <a class="navbtn" href="javascript:history.forward()">Adelante →</a></div><a class="navbtn" href="/cliente/pro">Inicio cliente</a></div>
<section class="hero"><span class="kicker">🟢 V196 · EVENTOS LIVE REALES</span><h1>Centro live premium</h1><p class="mut">Goles, tarjetas, sustituciones, VAR, penaltis y timeline solo cuando llegan desde proveedor/caché real. Sin eventos inventados.</p>
<div class="stats"><div class="stat"><span class="mut">Partidos</span><br><b>{{data.contadores.partidos}}</b></div><div class="stat"><span class="mut">En directo</span><br><b>{{data.contadores.directo}}</b></div><div class="stat"><span class="mut">Eventos reales</span><br><b>{{data.contadores.eventos_reales}}</b></div></div></section>
{% if data.estado_vacio %}<div class="empty" style="margin-top:16px">{{data.mensaje_vacio}}</div>{% else %}
<div class="grid"><main class="card">{% set m=data.partido_seleccionado %}<h2>{{m.titulo if m else 'Partido real'}}</h2><p class="mut">{{m.liga if m else ''}} · {{m.estado if m else ''}} · {{m.hora if m else ''}}</p>
{% if m and (m.marcador_local is not none or m.marcador_visitante is not none) %}<div class="score">{{m.marcador_local if m.marcador_local is not none else '-'}} - {{m.marcador_visitante if m.marcador_visitante is not none else '-'}}</div>{% endif %}
<div>{% for b in m.badges %}<span class="badge {{b.tono}}">{{b.texto}}</span>{% endfor %}</div><h3>Timeline real</h3><div class="timeline">{% if m.eventos %}{% for e in m.eventos %}<div class="event"><div class="minute">{{e.minuto}}</div><div><b>{{e.tipo}}</b><div class="mut">{{e.equipo}} {{e.jugador}}</div><div>{{e.descripcion}}</div><small class="mut">Fuente: {{e.fuente}}</small></div></div>{% endfor %}{% else %}<div class="empty">El proveedor todavía no ha entregado incidentes reales asociados a este partido.</div>{% endif %}</div></main>
<aside class="card"><h3>Partidos reales</h3><div class="matches">{% for x in data.partidos[:18] %}<a class="match" href="/cliente/live-events-real?match_id={{x.id}}"><span><b>{{x.titulo}}</b><br><small class="mut">{{x.liga}} · {{x.estado}}</small></span><span>{% if x.en_directo %}<span class="badge live">LIVE</span>{% endif %}</span></a>{% endfor %}</div></aside></div>{% endif %}
</div></body></html>
'''


@bp_live_events_real_v196.route('/api/v196/live-events-real')
def api_live_events_real():
    return jsonify(build_live_events_real(request.args.get('match_id') or request.args.get('id')))


@bp_live_events_real_v196.route('/cliente/live-events-real')
@bp_live_events_real_v196.route('/live-events-real')
def page_live_events_real():
    return render_template_string(PAGE, data=build_live_events_real(request.args.get('match_id') or request.args.get('id')))


@bp_live_events_real_v196.route('/admin/live-events-real')
def admin_live_events_real():
    data = build_live_events_real(request.args.get('match_id') or request.args.get('id'))
    return render_template_string(PAGE.replace('Centro live premium', 'Admin · Eventos live reales').replace('Inicio cliente', 'Panel admin').replace('/cliente/pro', '/admin'), data=data)
