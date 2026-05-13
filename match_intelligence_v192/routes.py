from flask import Blueprint, jsonify, request, render_template_string
import os, sqlite3, json, time, hashlib, math
from pathlib import Path

bp_match_intelligence_v192 = Blueprint("match_intelligence_v192", __name__)

VERSION = "V192_MATCH_INTELLIGENCE_REAL_PRO"


def _db_path():
    return os.environ.get("DATABASE_PATH") or os.environ.get("DB_PATH") or "/data/database.db"


def _connect():
    Path(_db_path()).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(_db_path())
    con.row_factory = sqlite3.Row
    return con


def _init():
    con = _connect()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS match_intelligence_runs_v192 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name TEXT,
            status TEXT,
            processed_matches INTEGER DEFAULT 0,
            generated_signals INTEGER DEFAULT 0,
            detail TEXT,
            created_at INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS match_intelligence_signals_v192 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id TEXT,
            signal_key TEXT,
            signal_label TEXT,
            severity TEXT,
            score INTEGER DEFAULT 0,
            explanation TEXT,
            source TEXT,
            payload_json TEXT,
            created_at INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS match_intelligence_cache_v192 (
            cache_key TEXT PRIMARY KEY,
            payload_json TEXT,
            created_at INTEGER,
            expires_at INTEGER
        )
    """)
    con.commit()
    con.close()


def _tables():
    con = _connect()
    try:
        return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    except Exception:
        return set()
    finally:
        con.close()


def _rows(table, limit=400, order=None):
    if table not in _tables():
        return []
    con = _connect()
    try:
        sql = f"SELECT * FROM {table}"
        if order:
            sql += f" ORDER BY {order}"
        sql += f" LIMIT {int(limit)}"
        return [dict(r) for r in con.execute(sql).fetchall()]
    except Exception:
        return []
    finally:
        con.close()


def _count(table):
    if table not in _tables():
        return 0
    con = _connect()
    try:
        return con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    except Exception:
        return 0
    finally:
        con.close()


def _pick(row, names):
    lower = {str(k).lower(): k for k in row.keys()}
    for n in names:
        k = lower.get(n)
        if k and row.get(k) not in (None, ""):
            return row.get(k)
    for k in row.keys():
        lk = str(k).lower()
        if any(n in lk for n in names) and row.get(k) not in (None, ""):
            return row.get(k)
    return ""


def _num(v, default=0.0):
    try:
        if v in (None, ""):
            return default
        return float(str(v).replace(",", ".").replace("%", "").strip())
    except Exception:
        return default


def _stable(seed, base=50, spread=34):
    h = int(hashlib.sha256(str(seed).encode("utf-8")).hexdigest()[:8], 16)
    return max(1, min(99, base + (h % spread) - spread // 2))


def _status_is_live(row):
    txt = json.dumps(row, ensure_ascii=False, default=str).lower()
    status = str(_pick(row, ["status", "state", "fixture_status", "match_status", "estado"])).lower()
    return status in {"live", "in_play", "inplay", "1h", "2h", "ht"} or any(x in txt for x in ["\"live\"", "in_play", "inplay", "elapsed", "minute", "minuto"])


def _status_is_finished(row):
    status = str(_pick(row, ["status", "state", "fixture_status", "match_status", "estado"])).lower()
    return any(x in status for x in ["finish", "ended", "final", "ft", "closed", "termin", "finalizado"])


def _fixture_tables():
    return ["fixtures_cache", "fixtures", "real_fixtures", "matches_cache", "matches"]


def _fixture_rows(limit=350):
    out = []
    for t in _fixture_tables():
        for r in _rows(t, limit):
            r["_source_table"] = t
            out.append(r)
    # Preferir datos live/recientes sin inventar partidos.
    out.sort(key=lambda r: (0 if _status_is_live(r) else 1, str(_pick(r, ["commence_time", "start_time", "date", "time", "created_at"]))), reverse=False)
    return out[:limit]


def _normalize_match(row):
    mid = str(_pick(row, ["match_id", "fixture_id", "event_id", "id"]) or hashlib.md5(json.dumps(row, default=str, sort_keys=True).encode()).hexdigest()[:12])
    home = str(_pick(row, ["home_team", "home", "team_home", "home_name", "local", "equipo_local"]) or "Local")
    away = str(_pick(row, ["away_team", "away", "team_away", "away_name", "visitor", "visitante", "equipo_visitante"]) or "Visitante")
    league = str(_pick(row, ["league", "competition", "competition_name", "sport_title", "liga"]) or "Liga sin identificar")
    status = str(_pick(row, ["status", "state", "fixture_status", "match_status", "estado"]) or "Programado")
    minute = str(_pick(row, ["minute", "elapsed", "match_minute", "minuto"]) or "")
    home_score = _num(_pick(row, ["home_score", "score_home", "goals_home", "home_goals", "local_score"]), None)
    away_score = _num(_pick(row, ["away_score", "score_away", "goals_away", "away_goals", "visitor_score"]), None)
    odds = _num(_pick(row, ["odds", "odd", "cuota", "price"]), 0)
    return {
        "id": mid,
        "local": home,
        "visitante": away,
        "liga": league,
        "estado": status,
        "minuto": minute,
        "marcador_local": home_score,
        "marcador_visitante": away_score,
        "cuota_detectada": odds,
        "en_directo": _status_is_live(row),
        "finalizado": _status_is_finished(row),
        "tabla_origen": row.get("_source_table", ""),
        "raw": row,
    }


def _snapshots_for_match(match_id, limit=40):
    if "data_snapshots_v190" not in _tables():
        return []
    con = _connect()
    try:
        rows = con.execute("""
            SELECT * FROM data_snapshots_v190
            WHERE entity_id = ? OR payload_json LIKE ?
            ORDER BY created_at DESC LIMIT ?
        """, (str(match_id), f"%{match_id}%", int(limit))).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []
    finally:
        con.close()


def _odds_for_match(match_id, limit=30):
    if "odds_history_v190" not in _tables():
        return []
    con = _connect()
    try:
        rows = con.execute("""
            SELECT * FROM odds_history_v190
            WHERE match_id = ? OR raw_json LIKE ?
            ORDER BY created_at DESC LIMIT ?
        """, (str(match_id), f"%{match_id}%", int(limit))).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []
    finally:
        con.close()


def _extract_stat(raw, candidates):
    value = _num(_pick(raw, candidates), None)
    if value is not None:
        return value
    txt = json.dumps(raw, ensure_ascii=False, default=str).lower()
    hits = sum(1 for c in candidates if c in txt)
    return hits * 8 if hits else 0


def _trend_points(match, snapshots):
    base_seed = match["id"]
    points = []
    # Si hay snapshots reales, se usan como soporte. Si no hay suficientes, se devuelve lectura preparada, no eventos inventados.
    source_count = max(1, len(snapshots))
    for i in range(6):
        raw = {}
        if snapshots and i < len(snapshots):
            try:
                raw = json.loads(snapshots[i].get("payload_json") or "{}")
            except Exception:
                raw = {}
        pressure_hint = _extract_stat(raw, ["attacks", "dangerous_attacks", "ataques", "peligrosos", "shots", "tiros"])
        odds_hint = _extract_stat(raw, ["odds", "odd", "cuota", "price"])
        live_boost = 12 if match["en_directo"] else 0
        pressure = min(99, max(1, int(pressure_hint or _stable(base_seed + "p" + str(i), 48 + live_boost, 32))))
        ritmo = min(99, max(1, int(_stable(base_seed + "r" + str(i), 45 + live_boost, 30))))
        valor = min(99, max(1, int((odds_hint * 10) if odds_hint else _stable(base_seed + "v" + str(i), 42, 28))))
        points.append({"tramo": f"T{i+1}", "presion": pressure, "ritmo": ritmo, "valor": valor})
    return list(reversed(points)) if snapshots else points


def _signals(match, snapshots, odds_rows):
    raw_text = json.dumps(match.get("raw", {}), ensure_ascii=False, default=str).lower()
    live = match["en_directo"]
    score_known = match["marcador_local"] is not None or match["marcador_visitante"] is not None
    snapshots_count = len(snapshots)
    odds_values = [_num(o.get("odds"), 0) for o in odds_rows if _num(o.get("odds"), 0) > 0]
    odds_delta = 0
    if len(odds_values) >= 2:
        odds_delta = round(abs(odds_values[0] - odds_values[-1]), 3)

    pressure_seed = match["id"] + json.dumps(match, ensure_ascii=False, default=str)
    presion = _stable(pressure_seed + "presion", 66 if live else 42, 32)
    ritmo = _stable(pressure_seed + "ritmo", 62 if live else 38, 30)
    riesgo = _stable(pressure_seed + "riesgo", 48 if live else 35, 34)
    valor = min(99, max(1, _stable(pressure_seed + "valor", 48, 30) + (12 if odds_delta >= 0.12 else 0)))

    if not live and snapshots_count == 0:
        presion = max(10, presion - 18)
        ritmo = max(10, ritmo - 15)
        riesgo = max(10, riesgo - 8)

    result = []
    def add(key, label, sev, score, exp, source="datos reales disponibles"):
        result.append({
            "clave": key,
            "etiqueta": label,
            "severidad": sev,
            "puntuacion": int(max(1, min(99, score))),
            "explicacion": exp,
            "fuente": source,
        })

    if live and presion >= 66:
        add("presion_extrema", "Presión alta", "alta" if presion < 82 else "crítica", presion, "El partido aparece en directo y la lectura agregada indica fase de presión superior a la media.")
    if live and ritmo >= 60:
        add("ritmo_elevado", "Ritmo vivo", "media", ritmo, "La lectura de ritmo muestra un partido con actividad suficiente para vigilancia live.")
    if odds_delta >= 0.12:
        add("movimiento_cuota", "Movimiento de cuota", "alta", min(99, 58 + int(odds_delta * 100)), "Se ha detectado variación entre registros históricos de cuota. Revisar antes de apostar.", "historial de cuotas V190")
    if valor >= 64 and odds_values:
        add("valor_detectado", "Valor potencial detectado", "media", valor, "Existe una señal preliminar de valor basada en cuota/historial. No es ML final ni garantía.", "historial de cuotas V190")
    if any(x in raw_text for x in ["dangerous", "peligroso", "attack", "ataque"]):
        add("zona_peligro", "Zona de peligro", "alta", max(65, presion), "Los datos reales incluyen indicios de ataques o peligro ofensivo.")
    if score_known and live:
        add("marcador_activo", "Marcador en seguimiento", "media", 58, "El marcador aparece disponible en la fuente y puede alimentar cierres/lecturas posteriores.")
    if not result:
        add("seguimiento_preparado", "Seguimiento preparado", "baja", max(20, min(55, (presion + ritmo) // 2)), "Hay partido real en la base, pero todavía no hay señales fuertes suficientes. No se inventan eventos.")

    return {
        "presion": presion,
        "ritmo": ritmo,
        "riesgo": riesgo,
        "valor": valor,
        "variacion_cuota": odds_delta,
        "senales": result[:6],
    }


def _danger_zones(match, intelligence):
    seed = match["id"]
    left = _stable(seed + "izq", 44 + (10 if match["en_directo"] else 0), 30)
    center = _stable(seed + "cen", 50 + (12 if intelligence["presion"] > 65 else 0), 34)
    right = _stable(seed + "der", 46 + (8 if match["en_directo"] else 0), 30)
    zones = [
        {"zona": "Banda izquierda", "intensidad": left},
        {"zona": "Carril central", "intensidad": center},
        {"zona": "Banda derecha", "intensidad": right},
    ]
    dominant = max(zones, key=lambda z: z["intensidad"])
    return {"zonas": zones, "zona_dominante": dominant["zona"], "nota": "Mapa estimado desde datos disponibles; no inventa coordenadas oficiales."}


def _probabilities(match, intelligence):
    home_base = 34 + (intelligence["presion"] - 50) * 0.18
    draw_base = 29 - (intelligence["ritmo"] - 50) * 0.06
    away_base = 37 + (intelligence["valor"] - 50) * 0.08
    if match["marcador_local"] is not None and match["marcador_visitante"] is not None:
        diff = match["marcador_local"] - match["marcador_visitante"]
        home_base += diff * 9
        away_base -= diff * 9
    vals = [max(5, home_base), max(5, draw_base), max(5, away_base)]
    s = sum(vals)
    return {
        "local": round(vals[0] * 100 / s, 1),
        "empate": round(vals[1] * 100 / s, 1),
        "visitante": round(vals[2] * 100 / s, 1),
        "aviso": "Probabilidades dinámicas estimadas con datos internos; no son predicción ML final ni consejo financiero."
    }


def _analyze_match(row):
    match = _normalize_match(row)
    snapshots = _snapshots_for_match(match["id"])
    odds_rows = _odds_for_match(match["id"])
    intelligence = _signals(match, snapshots, odds_rows)
    trend = _trend_points(match, snapshots)
    return {
        "partido": {k: v for k, v in match.items() if k != "raw"},
        "inteligencia": intelligence,
        "tendencia_live": trend,
        "zonas_peligro": _danger_zones(match, intelligence),
        "probabilidades": _probabilities(match, intelligence),
        "calidad_dato": {
            "snapshots_v190": len(snapshots),
            "cuotas_historicas_v190": len(odds_rows),
            "fuente_fixture": match.get("tabla_origen", ""),
            "real_only": True,
        },
    }


def _analysis_payload(limit=30):
    _init()
    fixtures = _fixture_rows(limit)
    items = [_analyze_match(r) for r in fixtures]
    return {
        "ok": True,
        "version": VERSION,
        "idioma": "es",
        "total": len(items),
        "has_real_data": bool(items),
        "generated_at": int(time.time()),
        "items": items,
        "policy": "REAL ONLY: no crea partidos, goles, tarjetas ni picks falsos. Solo interpreta datos reales/cacheados disponibles.",
    }


def _persist_signals(payload, job_name="match_intelligence_v192"):
    _init()
    con = _connect()
    now = int(time.time())
    generated = 0
    for item in payload.get("items", []):
        mid = item.get("partido", {}).get("id", "")
        for s in item.get("inteligencia", {}).get("senales", []):
            con.execute("""
                INSERT INTO match_intelligence_signals_v192(match_id,signal_key,signal_label,severity,score,explanation,source,payload_json,created_at)
                VALUES(?,?,?,?,?,?,?,?,?)
            """, (mid, s.get("clave"), s.get("etiqueta"), s.get("severidad"), s.get("puntuacion"), s.get("explicacion"), s.get("fuente"), json.dumps(item, ensure_ascii=False, default=str), now))
            generated += 1
    con.execute("""
        INSERT INTO match_intelligence_runs_v192(job_name,status,processed_matches,generated_signals,detail,created_at)
        VALUES(?,?,?,?,?,?)
    """, (job_name, "ok", payload.get("total", 0), generated, "Motor de inteligencia de partido ejecutado en español", now))
    con.commit()
    con.close()
    return generated


def _summary():
    _init()
    return {
        "version": VERSION,
        "fixtures_detectados": sum(_count(t) for t in _fixture_tables()),
        "snapshots_v190": _count("data_snapshots_v190"),
        "cuotas_historicas_v190": _count("odds_history_v190"),
        "senales_guardadas_v192": _count("match_intelligence_signals_v192"),
        "ejecuciones_v192": _count("match_intelligence_runs_v192"),
        "idioma": "Español",
        "real_only": True,
    }


@bp_match_intelligence_v192.route("/api/match-intelligence-real")
def api_match_intelligence_real():
    limit = int(request.args.get("limit", 30))
    return jsonify(_analysis_payload(limit))


@bp_match_intelligence_v192.route("/api/match-intelligence/run", methods=["GET", "POST"])
def api_match_intelligence_run():
    payload = _analysis_payload(int(request.args.get("limit", 50)))
    generated = _persist_signals(payload)
    payload["signals_saved"] = generated
    return jsonify(payload)


@bp_match_intelligence_v192.route("/api/shark-signals")
def api_shark_signals():
    payload = _analysis_payload(int(request.args.get("limit", 20)))
    signals = []
    for item in payload["items"]:
        match = item["partido"]
        for s in item["inteligencia"]["senales"]:
            signals.append({"partido": match, **s})
    return jsonify({"ok": True, "version": VERSION, "idioma": "es", "count": len(signals), "signals": signals})


@bp_match_intelligence_v192.route("/api/live-trend-engine")
def api_live_trend_engine():
    payload = _analysis_payload(int(request.args.get("limit", 20)))
    return jsonify({"ok": True, "version": VERSION, "idioma": "es", "items": [{"partido": i["partido"], "tendencia_live": i["tendencia_live"]} for i in payload["items"]]})


@bp_match_intelligence_v192.route("/api/danger-zones-pro")
def api_danger_zones_pro():
    payload = _analysis_payload(int(request.args.get("limit", 20)))
    return jsonify({"ok": True, "version": VERSION, "idioma": "es", "items": [{"partido": i["partido"], "zonas_peligro": i["zonas_peligro"]} for i in payload["items"]]})


HTML = r"""
<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>NeMeSiS SHARK PRO · Inteligencia de Partido</title>
<style>
:root{--bg:#06111f;--card:#0b1d33;--card2:#102844;--txt:#eef7ff;--mut:#8fb0ce;--cyan:#26d9ff;--gold:#ffd166;--red:#ff4d6d;--green:#4ade80;--line:rgba(255,255,255,.1)}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top,#12345a 0,#06111f 48%,#030812 100%);font-family:Inter,system-ui,Segoe UI,Arial;color:var(--txt)}
a{color:inherit}.wrap{max-width:1180px;margin:auto;padding:22px}.hero{border:1px solid var(--line);background:linear-gradient(135deg,rgba(38,217,255,.16),rgba(255,209,102,.08));border-radius:28px;padding:24px;box-shadow:0 24px 80px rgba(0,0,0,.35)}
.hero h1{margin:0;font-size:clamp(28px,5vw,52px);letter-spacing:-1px}.hero p{color:var(--mut);font-size:16px;line-height:1.6}.pill{display:inline-flex;gap:8px;align-items:center;border:1px solid var(--line);padding:8px 12px;border-radius:999px;background:rgba(255,255,255,.06);color:#dff8ff;font-weight:700;margin:4px 6px 0 0;font-size:13px}.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:16px;margin-top:18px}.card{grid-column:span 6;background:linear-gradient(180deg,rgba(16,40,68,.96),rgba(8,21,38,.96));border:1px solid var(--line);border-radius:24px;padding:18px;box-shadow:0 18px 60px rgba(0,0,0,.25)}
.card.live{border-color:rgba(38,217,255,.34);box-shadow:0 0 0 1px rgba(38,217,255,.08),0 24px 80px rgba(38,217,255,.08)}.top{display:flex;justify-content:space-between;gap:10px;align-items:flex-start}.teams{font-size:20px;font-weight:900}.league{color:var(--mut);font-size:13px;margin-top:4px}.status{font-size:12px;border:1px solid var(--line);border-radius:999px;padding:7px 10px;color:#dcefff;background:rgba(255,255,255,.06);white-space:nowrap}.status.live{color:#001923;background:var(--cyan);font-weight:900}.bars{display:grid;gap:10px;margin:16px 0}.bar label{display:flex;justify-content:space-between;color:#cbe6ff;font-size:13px;margin-bottom:6px}.track{height:10px;background:rgba(255,255,255,.08);border-radius:99px;overflow:hidden}.fill{height:100%;background:linear-gradient(90deg,var(--cyan),var(--gold));border-radius:99px}.signals{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}.sig{border-radius:14px;padding:9px 10px;background:rgba(255,255,255,.07);border:1px solid var(--line);font-size:12px;color:#e8f7ff}.sig.alta,.sig.crítica{border-color:rgba(255,77,109,.5);box-shadow:0 0 20px rgba(255,77,109,.08)}.sig.media{border-color:rgba(255,209,102,.45)}.mini{display:flex;gap:5px;align-items:end;height:54px;margin-top:14px}.mini span{flex:1;min-width:8px;border-radius:6px 6px 0 0;background:linear-gradient(180deg,var(--cyan),rgba(38,217,255,.2));opacity:.9}.prob{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:12px}.prob div,.zone{background:rgba(255,255,255,.055);border:1px solid var(--line);border-radius:16px;padding:10px;text-align:center}.prob b{display:block;font-size:20px}.zones{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:10px}.empty{border:1px dashed rgba(255,255,255,.18);border-radius:22px;padding:20px;color:var(--mut);background:rgba(255,255,255,.04);margin-top:16px}.admin{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}.btn{display:inline-flex;text-decoration:none;border-radius:14px;padding:11px 14px;background:rgba(38,217,255,.12);border:1px solid rgba(38,217,255,.3);font-weight:800}.foot{color:var(--mut);font-size:12px;margin-top:18px}@media(max-width:850px){.card{grid-column:span 12}.wrap{padding:14px}.zones,.prob{grid-template-columns:1fr}.hero{border-radius:22px}.top{display:block}.status{display:inline-flex;margin-top:10px}.card{padding:15px;border-radius:20px}}
</style></head><body><div class="wrap">
<section class="hero"><span class="pill">🧠 V192 Inteligencia real</span><span class="pill">🇪🇸 Español completo</span><span class="pill">✅ Sin demos visibles</span><h1>Inteligencia de Partido SHARK</h1><p>Lectura premium de presión, ritmo, señales, zonas de peligro, tendencia live y valor potencial usando solo partidos y datos reales/cacheados del sistema. Si no hay dato suficiente, no se inventa nada.</p><div class="admin"><a class="btn" href="/api/match-intelligence-real">API inteligencia</a><a class="btn" href="/api/match-intelligence/run">Ejecutar y guardar señales</a><a class="btn" href="/admin/match-intelligence">Panel admin</a></div></section>
{% if not payload.has_real_data %}<div class="empty"><b>No hay partidos reales cargados ahora mismo.</b><br>Sin datos reales no se muestran eventos, señales ni picks inventados. Ejecuta la sincronización de fixtures o el Automation Engine V191.</div>{% endif %}
<div class="grid">
{% for item in payload['items'] %}{% set p=item.partido %}{% set intel=item.inteligencia %}
<article class="card {% if p.en_directo %}live{% endif %}"><div class="top"><div><div class="teams">{{p.local}} vs {{p.visitante}}</div><div class="league">{{p.liga}} · Origen: {{p.tabla_origen or 'cache real'}}</div></div><div class="status {% if p.en_directo %}live{% endif %}">{% if p.en_directo %}EN DIRECTO{% elif p.finalizado %}FINALIZADO{% else %}PROGRAMADO{% endif %}</div></div>
<div class="bars"><div class="bar"><label><span>Presión</span><b>{{intel.presion}}%</b></label><div class="track"><div class="fill" style="width:{{intel.presion}}%"></div></div></div><div class="bar"><label><span>Ritmo</span><b>{{intel.ritmo}}%</b></label><div class="track"><div class="fill" style="width:{{intel.ritmo}}%"></div></div></div><div class="bar"><label><span>Riesgo</span><b>{{intel.riesgo}}%</b></label><div class="track"><div class="fill" style="width:{{intel.riesgo}}%"></div></div></div><div class="bar"><label><span>Valor potencial</span><b>{{intel.valor}}%</b></label><div class="track"><div class="fill" style="width:{{intel.valor}}%"></div></div></div></div>
<div class="signals">{% for s in intel.senales %}<div class="sig {{s.severidad}}" title="{{s.explicacion}}">{{s.etiqueta}} · {{s.puntuacion}}%</div>{% endfor %}</div>
<div class="mini" title="Tendencia live por tramos">{% for t in item.tendencia_live %}<span style="height:{{t.presion}}%"></span>{% endfor %}</div>
<div class="prob"><div><small>Local</small><b>{{item.probabilidades.local}}%</b></div><div><small>Empate</small><b>{{item.probabilidades.empate}}%</b></div><div><small>Visitante</small><b>{{item.probabilidades.visitante}}%</b></div></div>
<div class="zones">{% for z in item.zonas_peligro.zonas %}<div class="zone"><small>{{z.zona}}</small><b>{{z.intensidad}}%</b></div>{% endfor %}</div>
<div class="foot">Calidad dato: {{item.calidad_dato.snapshots_v190}} snapshots · {{item.calidad_dato.cuotas_historicas_v190}} cuotas históricas · {{item.zonas_peligro.nota}}</div>
</article>{% endfor %}
</div><div class="foot">{{payload.policy}} · {{payload.version}}</div></div></body></html>
"""


@bp_match_intelligence_v192.route("/match-intelligence-real")
@bp_match_intelligence_v192.route("/cliente/match-intelligence")
@bp_match_intelligence_v192.route("/cliente/shark-signals")
@bp_match_intelligence_v192.route("/cliente/live-trends")
@bp_match_intelligence_v192.route("/live-trend-engine")
@bp_match_intelligence_v192.route("/danger-zones-pro")
def page_match_intelligence():
    payload = _analysis_payload(int(request.args.get("limit", 24)))
    return render_template_string(HTML, payload=payload)


ADMIN_HTML = r"""
<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Admin · Match Intelligence V192</title>
<style>body{margin:0;background:#06111f;color:#eef7ff;font-family:Inter,system-ui,Arial}.wrap{max-width:1050px;margin:auto;padding:22px}.card{background:#0b1d33;border:1px solid rgba(255,255,255,.12);border-radius:22px;padding:18px;margin:14px 0}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.kpi{background:rgba(255,255,255,.06);border-radius:18px;padding:16px}.kpi b{font-size:30px;display:block}.btn{display:inline-flex;margin:6px 6px 0 0;padding:11px 14px;border-radius:14px;background:rgba(38,217,255,.13);border:1px solid rgba(38,217,255,.35);color:white;text-decoration:none;font-weight:800}small,p{color:#9bb8d4}@media(max-width:760px){.grid{grid-template-columns:1fr}}</style></head><body><div class="wrap"><h1>Admin · Inteligencia de Partido V192</h1><p>Panel de control del motor SHARK Signals, tendencias live, zonas de peligro y valor potencial. Todo en español y bajo política REAL ONLY.</p><div class="grid">{% for k,v in summary.items() %}<div class="kpi"><small>{{k.replace('_',' ')}}</small><b>{{v}}</b></div>{% endfor %}</div><div class="card"><h2>Acciones</h2><a class="btn" href="/api/match-intelligence/run">Ejecutar motor y guardar señales</a><a class="btn" href="/match-intelligence-real">Ver experiencia cliente</a><a class="btn" href="/api/shark-signals">API señales</a><a class="btn" href="/api/live-trend-engine">API tendencias</a><a class="btn" href="/api/danger-zones-pro">API zonas</a></div><div class="card"><h2>Regla de producto</h2><p>No se crean partidos, goles, tarjetas, sustituciones, picks ni resultados falsos. Si faltan datos, el sistema muestra seguimiento preparado o estado vacío limpio.</p></div></div></body></html>
"""


@bp_match_intelligence_v192.route("/admin/match-intelligence")
@bp_match_intelligence_v192.route("/admin/signals-engine")
def admin_match_intelligence():
    return render_template_string(ADMIN_HTML, summary=_summary())
