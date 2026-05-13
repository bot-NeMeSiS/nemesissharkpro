from flask import Blueprint, jsonify, request, render_template_string
from datetime import datetime, timedelta
from pathlib import Path
import os, sqlite3, json, time, urllib.request, urllib.parse

bp_automation_engine_v191 = Blueprint("automation_engine_v191", __name__)

VERSION = "V191_AUTOMATION_ENGINE_PRO"


def _db_path():
    return os.environ.get("DATABASE_PATH") or os.environ.get("DB_PATH") or "/data/database.db"


def _connect():
    p = Path(_db_path())
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    con = sqlite3.connect(str(p), timeout=10)
    con.row_factory = sqlite3.Row
    return con


def _now_ts():
    return int(time.time())


def _now_iso():
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _iso_plus(minutes):
    return (datetime.utcnow() + timedelta(minutes=int(minutes))).replace(microsecond=0).isoformat() + "Z"


def _init():
    con = _connect()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS automation_jobs_v191 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_key TEXT UNIQUE,
            title TEXT,
            description TEXT,
            job_type TEXT,
            enabled INTEGER DEFAULT 1,
            interval_minutes INTEGER DEFAULT 60,
            last_run_at TEXT,
            next_run_at TEXT,
            last_status TEXT,
            last_message TEXT,
            run_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS automation_runs_v191 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_key TEXT,
            status TEXT,
            message TEXT,
            payload_json TEXT,
            duration_ms INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS automation_locks_v191 (
            lock_key TEXT PRIMARY KEY,
            locked_until INTEGER,
            updated_at INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS automation_cache_warm_v191 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route TEXT,
            status TEXT,
            duration_ms INTEGER DEFAULT 0,
            detail TEXT,
            created_at INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS telegram_dispatch_queue_v191 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dispatch_type TEXT,
            target TEXT,
            title TEXT,
            payload_json TEXT,
            status TEXT DEFAULT 'queued',
            attempts INTEGER DEFAULT 0,
            last_error TEXT,
            created_at INTEGER,
            sent_at INTEGER
        )
    """)
    defaults = [
        ("fixtures_auto_sync", "Auto sync fixtures reales", "Sincroniza/activa conectores de fixtures reales si están disponibles.", "fixtures_sync", 1, 180),
        ("data_snapshots", "Auto snapshots históricos", "Ejecuta V190 Data Collection para guardar histórico real.", "data_collection", 1, 240),
        ("cache_warming", "Auto cache warming", "Calienta endpoints internos de estado/cliente/admin sin inventar datos.", "cache_warming", 1, 60),
        ("auto_close_picks", "Auto close picks", "Marca candidatos y revisa picks cerrables con datos reales existentes.", "close_picks", 1, 120),
        ("telegram_dispatch", "Auto Telegram dispatch", "Prepara/envía resúmenes reales si hay token y chat configurados.", "telegram_dispatch", 1, 180),
        ("system_guard", "Guardia de sistema", "Comprueba salud, tablas, entorno y frescura del motor de datos.", "health", 1, 45),
    ]
    for key, title, desc, typ, enabled, interval in defaults:
        cur.execute("""
            INSERT OR IGNORE INTO automation_jobs_v191
            (job_key,title,description,job_type,enabled,interval_minutes,next_run_at,last_status,last_message)
            VALUES(?,?,?,?,?,?,?,?,?)
        """, (key, title, desc, typ, enabled, interval, _iso_plus(interval), "pendiente", "Preparado"))
    con.commit()
    con.close()


def _authorized():
    secret = os.environ.get("AUTOMATION_SECRET") or os.environ.get("CRON_SECRET")
    if not secret:
        return True
    return request.headers.get("X-Automation-Secret") == secret or request.args.get("secret") == secret


def _tables():
    con = _connect()
    try:
        return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    finally:
        con.close()


def _count(table):
    if table not in _tables():
        return 0
    con = _connect()
    try:
        return int(con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] or 0)
    except Exception:
        return 0
    finally:
        con.close()


def _log(job_key, status, message, payload=None, duration_ms=0):
    con = _connect()
    try:
        interval = con.execute("SELECT interval_minutes FROM automation_jobs_v191 WHERE job_key=?", (job_key,)).fetchone()
        minutes = int(interval[0]) if interval else 60
        con.execute("""
            INSERT INTO automation_runs_v191(job_key,status,message,payload_json,duration_ms,created_at)
            VALUES(?,?,?,?,?,?)
        """, (job_key, status, message, json.dumps(payload or {}, ensure_ascii=False, default=str), int(duration_ms), _now_iso()))
        con.execute("""
            UPDATE automation_jobs_v191
            SET last_run_at=?, next_run_at=?, last_status=?, last_message=?, run_count=COALESCE(run_count,0)+1
            WHERE job_key=?
        """, (_now_iso(), _iso_plus(minutes), status, message, job_key))
        con.commit()
    finally:
        con.close()


def _lock(name, ttl=240):
    con = _connect()
    now = _now_ts()
    try:
        row = con.execute("SELECT locked_until FROM automation_locks_v191 WHERE lock_key=?", (name,)).fetchone()
        if row and int(row[0] or 0) > now:
            return False
        con.execute("INSERT OR REPLACE INTO automation_locks_v191(lock_key,locked_until,updated_at) VALUES(?,?,?)", (name, now + int(ttl), now))
        con.commit()
        return True
    finally:
        con.close()


def _release(name):
    con = _connect()
    try:
        con.execute("DELETE FROM automation_locks_v191 WHERE lock_key=?", (name,))
        con.commit()
    finally:
        con.close()


def _call_local_path(path, timeout=8):
    base = os.environ.get("PUBLIC_BASE_URL") or os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("APP_BASE_URL")
    if not base:
        return {"ok": False, "status": "skipped", "detail": "Sin PUBLIC_BASE_URL/RENDER_EXTERNAL_URL para llamada HTTP interna", "path": path}
    url = base.rstrip("/") + path
    start = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "NeMeSiS-Automation-V191"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(600).decode("utf-8", errors="ignore")
            return {"ok": 200 <= r.status < 400, "status_code": r.status, "duration_ms": int((time.time()-start)*1000), "sample": body[:240], "path": path}
    except Exception as e:
        return {"ok": False, "status": "error", "duration_ms": int((time.time()-start)*1000), "detail": str(e), "path": path}


def _job_fixtures_sync():
    paths = ["/admin/fixtures-sync", "/api/v146/fixtures/sync", "/fixtures/today-pro"]
    results = [_call_local_path(p) for p in paths]
    ok = any(r.get("ok") for r in results)
    msg = "Fixtures reales sincronizados o calentados" if ok else "No se pudo confirmar sync HTTP; revisa base URL/conector"
    return ("ok" if ok else "warning", msg, {"paths": results, "policy": "No crea partidos fake"})


def _job_data_collection():
    try:
        from data_collection_engine_v190.routes import _run_collection, _status
        result = _run_collection("automation_v191")
        status_data = _status()
        ok = result.get("status") == "ok"
        return ("ok" if ok else "error", "Snapshots históricos V190 ejecutados" if ok else result.get("detail", "Error en V190"), {"result": result, "warehouse": status_data.get("warehouse", {})})
    except Exception as e:
        return ("error", f"No se pudo ejecutar V190 Data Collection: {e}", {})


def _job_cache_warming():
    paths = ["/home-live-real", "/cliente/live-depth", "/cliente/advanced-stats", "/data-visual-richness-pro", "/ml-data-foundation-pro", "/data-collection-engine-pro"]
    results = []
    con = _connect()
    try:
        for p in paths:
            r = _call_local_path(p, timeout=6)
            results.append(r)
            con.execute("INSERT INTO automation_cache_warm_v191(route,status,duration_ms,detail,created_at) VALUES(?,?,?,?,?)", (p, "ok" if r.get("ok") else "warning", int(r.get("duration_ms") or 0), json.dumps(r, ensure_ascii=False, default=str), _now_ts()))
        con.commit()
    finally:
        con.close()
    ok_count = sum(1 for r in results if r.get("ok"))
    return ("ok" if ok_count else "warning", f"Cache warming completado: {ok_count}/{len(paths)} rutas OK", {"routes": results})


def _job_close_picks():
    tables = _tables()
    candidates = []
    for table in ["picks", "real_picks", "admin_picks", "closed_picks", "pick_lifecycle_v190"]:
        if table in tables:
            candidates.append({"table": table, "rows": _count(table)})
    payload = {"candidate_tables": candidates, "note": "V191 no cierra picks sin resultado real verificable; deja trazabilidad para motores existentes V161-V190."}
    if "pick_lifecycle_v190" in tables:
        con = _connect()
        try:
            closed = con.execute("SELECT COUNT(*) FROM pick_lifecycle_v190 WHERE result_label IN ('WIN','LOSS','VOID')").fetchone()[0]
            payload["closed_lifecycle_rows"] = int(closed or 0)
        except Exception:
            pass
        finally:
            con.close()
    return ("ok", "Revisión de cierre ejecutada sin datos inventados", payload)


def _send_telegram(text):
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_ADMIN_CHAT_ID") or os.environ.get("ADMIN_CHAT_ID")
    if not token or not chat_id:
        return {"ok": False, "status": "skipped", "detail": "Falta TELEGRAM_BOT_TOKEN/BOT_TOKEN o TELEGRAM_ADMIN_CHAT_ID/ADMIN_CHAT_ID"}
    try:
        data = urllib.parse.urlencode({"chat_id": chat_id, "text": text[:3900], "parse_mode": "HTML"}).encode()
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        with urllib.request.urlopen(url, data=data, timeout=10) as r:
            body = r.read(800).decode("utf-8", errors="ignore")
            return {"ok": 200 <= r.status < 400, "status_code": r.status, "body": body[:300]}
    except Exception as e:
        return {"ok": False, "status": "error", "detail": str(e)}


def _job_telegram_dispatch():
    summary = {
        "fixtures_rows": sum(_count(t) for t in ["fixtures_cache", "fixtures", "real_fixtures", "matches_cache", "matches"]),
        "picks_rows": sum(_count(t) for t in ["picks", "real_picks", "admin_picks", "closed_picks"]),
        "snapshots_v190": _count("data_snapshots_v190"),
        "odds_history_v190": _count("odds_history_v190"),
        "result_history_v190": _count("result_history_v190"),
        "generated_at": _now_iso(),
    }
    text = "🦈 <b>NeMeSiS SHARK PRO · Auto resumen</b>\n" + "\n".join([f"• {k}: {v}" for k, v in summary.items()])
    sent = _send_telegram(text)
    con = _connect()
    try:
        con.execute("""
            INSERT INTO telegram_dispatch_queue_v191(dispatch_type,target,title,payload_json,status,attempts,last_error,created_at,sent_at)
            VALUES(?,?,?,?,?,?,?,?,?)
        """, ("admin_summary", os.environ.get("TELEGRAM_ADMIN_CHAT_ID") or os.environ.get("ADMIN_CHAT_ID") or "not_configured", "Auto resumen V191", json.dumps(summary, ensure_ascii=False), "sent" if sent.get("ok") else sent.get("status", "warning"), 1, sent.get("detail"), _now_ts(), _now_ts() if sent.get("ok") else None))
        con.commit()
    finally:
        con.close()
    status = "ok" if sent.get("ok") else "warning"
    return (status, "Telegram dispatch ejecutado" if sent.get("ok") else "Telegram preparado pero no enviado por configuración/error", {"summary": summary, "telegram": sent})


def _job_health():
    tables = sorted(list(_tables()))
    payload = {
        "database_path": _db_path(),
        "tables_total": len(tables),
        "critical_tables": {t: (t in tables) for t in ["data_snapshots_v190", "odds_history_v190", "result_history_v190", "pick_lifecycle_v190", "automation_jobs_v191", "automation_runs_v191"]},
        "env": {
            "public_base_url": bool(os.environ.get("PUBLIC_BASE_URL") or os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("APP_BASE_URL")),
            "telegram_token": bool(os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN")),
            "telegram_admin_chat": bool(os.environ.get("TELEGRAM_ADMIN_CHAT_ID") or os.environ.get("ADMIN_CHAT_ID")),
            "automation_secret": bool(os.environ.get("AUTOMATION_SECRET") or os.environ.get("CRON_SECRET")),
        },
        "counts": {
            "snapshots": _count("data_snapshots_v190"),
            "odds_history": _count("odds_history_v190"),
            "result_history": _count("result_history_v190"),
            "pick_lifecycle": _count("pick_lifecycle_v190"),
            "automation_runs": _count("automation_runs_v191"),
        },
        "policy": "REAL ONLY: no genera partidos, picks ni scores falsos.",
    }
    missing = [k for k, v in payload["critical_tables"].items() if not v]
    status = "ok" if not missing else "warning"
    msg = "Sistema V191 operativo" if not missing else "Faltan tablas que se crearán al ejecutar los motores: " + ", ".join(missing)
    return (status, msg, payload)


def run_job(job_key, force=False):
    _init()
    if not _lock("job_" + job_key, ttl=300):
        return {"ok": True, "status": "locked", "message": "Job ya está en ejecución o bloqueado temporalmente"}
    start = time.time()
    try:
        con = _connect()
        try:
            row = con.execute("SELECT * FROM automation_jobs_v191 WHERE job_key=?", (job_key,)).fetchone()
        finally:
            con.close()
        if not row:
            return {"ok": False, "status": "error", "message": "job_not_found"}
        job = dict(row)
        if not int(job.get("enabled") or 0) and not force:
            _log(job_key, "skipped", "Job desactivado", {"enabled": False}, int((time.time()-start)*1000))
            return {"ok": True, "status": "skipped", "message": "Job desactivado"}
        handlers = {
            "fixtures_sync": _job_fixtures_sync,
            "data_collection": _job_data_collection,
            "cache_warming": _job_cache_warming,
            "close_picks": _job_close_picks,
            "telegram_dispatch": _job_telegram_dispatch,
            "health": _job_health,
        }
        handler = handlers.get(job.get("job_type"), _job_health)
        status, message, payload = handler()
        duration = int((time.time()-start)*1000)
        _log(job_key, status, message, payload, duration)
        return {"ok": status in ("ok", "warning"), "status": status, "message": message, "duration_ms": duration, "payload": payload}
    finally:
        _release("job_" + job_key)


def _status():
    _init()
    con = _connect()
    try:
        jobs = [dict(r) for r in con.execute("SELECT * FROM automation_jobs_v191 ORDER BY enabled DESC, job_key ASC").fetchall()]
        runs = [dict(r) for r in con.execute("SELECT * FROM automation_runs_v191 ORDER BY id DESC LIMIT 30").fetchall()]
        cache = [dict(r) for r in con.execute("SELECT * FROM automation_cache_warm_v191 ORDER BY id DESC LIMIT 12").fetchall()]
        telegram = [dict(r) for r in con.execute("SELECT * FROM telegram_dispatch_queue_v191 ORDER BY id DESC LIMIT 12").fetchall()]
    finally:
        con.close()
    due = 0
    now = datetime.utcnow()
    for j in jobs:
        try:
            if j.get("next_run_at") and datetime.fromisoformat(j["next_run_at"].replace("Z", "")) <= now and int(j.get("enabled") or 0):
                due += 1
        except Exception:
            pass
    return {
        "version": VERSION,
        "generated_at": _now_iso(),
        "summary": {
            "jobs_total": len(jobs),
            "jobs_enabled": sum(1 for j in jobs if int(j.get("enabled") or 0)),
            "jobs_due": due,
            "runs_shown": len(runs),
            "status": "operativo" if jobs else "sin_jobs",
        },
        "jobs": jobs,
        "runs": runs,
        "cache_warm": cache,
        "telegram_dispatch": telegram,
        "routes": {
            "panel": "/automation-engine-pro",
            "admin": "/admin/automation-engine-pro",
            "status": "/api/v191/automation/status",
            "run_due": "/api/v191/automation/run-due",
            "run_job": "/api/v191/automation/run/<job_key>",
        },
        "policy": "REAL ONLY: automatiza motores reales/cache existentes, no genera datos deportivos ficticios.",
    }


@bp_automation_engine_v191.route("/automation-engine-pro")
@bp_automation_engine_v191.route("/admin/automation-engine-pro")
@bp_automation_engine_v191.route("/admin/automation-v191")
def page():
    data = _status()
    return render_template_string("""
<!doctype html><html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Automation Engine V191 · NeMeSiS SHARK PRO</title>
<style>
:root{--bg:#06111f;--panel:#0b1c31;--line:#1b4169;--txt:#eafbff;--mut:#91b4c9;--cyan:#22d3ee;--green:#35f0a1;--gold:#ffd166;--red:#ff5b7a}
body{margin:0;background:radial-gradient(circle at top,#153d68,#06111f 52%,#02060b);font-family:Inter,system-ui,Arial;color:var(--txt)}
.wrap{max-width:1260px;margin:auto;padding:24px}.hero,.card{border:1px solid var(--line);background:rgba(11,28,49,.88);border-radius:26px;padding:22px;box-shadow:0 20px 80px rgba(0,0,0,.28)}
.badge{display:inline-flex;padding:8px 12px;border-radius:99px;background:rgba(34,211,238,.14);border:1px solid rgba(34,211,238,.35);color:#c9f9ff;font-weight:950;font-size:12px}
.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;margin-top:16px}.grid2{display:grid;grid-template-columns:1.2fr .8fr;gap:16px;margin-top:16px}.jobs{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:16px}
.k{font-size:34px;font-weight:950;margin-top:6px}.mut{color:var(--mut)}.ok{color:var(--green)}.gold{color:var(--gold)}.red{color:var(--red)}
.btn{display:inline-block;margin:8px 8px 0 0;padding:12px 16px;border-radius:14px;text-decoration:none;background:linear-gradient(135deg,#22d3ee,#2dd4bf);color:#021018;font-weight:950;border:0;cursor:pointer}.btn2{background:#102a45;color:#dff8ff;border:1px solid #245078}.pill{display:inline-flex;padding:6px 9px;border-radius:99px;background:#071526;border:1px solid #234869;color:#cff6ff;font-size:12px;font-weight:900}.job{position:relative;overflow:hidden}.job:before{content:"";position:absolute;inset:0 0 auto 0;height:3px;background:linear-gradient(90deg,#22d3ee,#35f0a1,#ffd166)}
pre{white-space:pre-wrap;background:#05101d;border:1px solid #183759;border-radius:16px;padding:14px;color:#e6fbff;overflow:auto;max-height:430px}
@media(max-width:1050px){.grid,.grid2,.jobs{grid-template-columns:1fr}.wrap{padding:16px}}
</style></head><body><div class="wrap">
 <div class="hero">
  <div class="badge">⚙️ V191 AUTOMATION ENGINE PRO</div>
  <h1>Motor de automatización real</h1>
  <p class="mut">Auto sync fixtures, snapshots históricos, cache warming, cierre de picks, Telegram dispatch y guardia de sistema. No inventa partidos, picks ni resultados.</p>
  <button class="btn" onclick="runDue()">Ejecutar pendientes</button>
  <a class="btn btn2" href="/data-collection-engine-pro">Data Collection V190</a>
  <a class="btn btn2" href="/admin/data-engine">Admin Data Engine</a>
  <a class="btn btn2" href="/api/v191/automation/status">API estado</a>
 </div>
 <div class="grid">
  <div class="card"><div class="mut">Jobs totales</div><div class="k">{{ data.summary.jobs_total }}</div></div>
  <div class="card"><div class="mut">Activos</div><div class="k ok">{{ data.summary.jobs_enabled }}</div></div>
  <div class="card"><div class="mut">Pendientes</div><div class="k gold">{{ data.summary.jobs_due }}</div></div>
  <div class="card"><div class="mut">Estado</div><div class="k">{{ data.summary.status }}</div></div>
 </div>
 <div class="jobs">
 {% for j in data.jobs %}
  <div class="card job">
   <span class="pill">{{ j.job_key }}</span>
   <h3>{{ j.title }}</h3>
   <p class="mut">{{ j.description }}</p>
   <p><b>Tipo:</b> {{ j.job_type }} · <b>Intervalo:</b> {{ j.interval_minutes }} min</p>
   <p><b>Último:</b> <span class="{{ 'ok' if j.last_status == 'ok' else 'gold' if j.last_status in ['warning','pendiente'] else 'red' }}">{{ j.last_status }}</span></p>
   <p class="mut">{{ j.last_message }}</p>
   <button class="btn" onclick="runJob('{{ j.job_key }}')">Ejecutar</button>
   <button class="btn btn2" onclick="toggleJob('{{ j.job_key }}')">{{ 'Desactivar' if j.enabled else 'Activar' }}</button>
  </div>
 {% endfor %}
 </div>
 <div class="grid2">
  <div class="card"><h2>Últimas ejecuciones</h2><pre id="runs">{{ data.runs | tojson(indent=2) }}</pre></div>
  <div class="card"><h2>Estado completo</h2><pre id="out">{{ data | tojson(indent=2) }}</pre></div>
 </div>
</div><script>
async function runDue(){const r=await fetch('/api/v191/automation/run-due',{method:'POST'}).then(r=>r.json());document.getElementById('out').textContent=JSON.stringify(r,null,2)}
async function runJob(k){const r=await fetch('/api/v191/automation/run/'+k,{method:'POST'}).then(r=>r.json());document.getElementById('out').textContent=JSON.stringify(r,null,2)}
async function toggleJob(k){const r=await fetch('/api/v191/automation/toggle/'+k,{method:'POST'}).then(r=>r.json());document.getElementById('out').textContent=JSON.stringify(r,null,2);setTimeout(()=>location.reload(),700)}
</script></body></html>
    """, data=data)


@bp_automation_engine_v191.route("/api/v191/automation/status")
def api_status():
    return jsonify({"ok": True, "automation": _status()})


@bp_automation_engine_v191.route("/api/v191/automation/run/<job_key>", methods=["GET", "POST"])
def api_run_job(job_key):
    if not _authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    return jsonify(run_job(job_key, force=True))


@bp_automation_engine_v191.route("/api/v191/automation/run-due", methods=["GET", "POST"])
def api_run_due():
    if not _authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    _init()
    con = _connect()
    try:
        jobs = [dict(r) for r in con.execute("SELECT * FROM automation_jobs_v191 WHERE enabled=1").fetchall()]
    finally:
        con.close()
    results = []
    now = datetime.utcnow()
    for job in jobs:
        due = True
        try:
            if job.get("next_run_at"):
                due = datetime.fromisoformat(job["next_run_at"].replace("Z", "")) <= now
        except Exception:
            due = True
        if due or request.args.get("force") == "1":
            results.append({"job_key": job["job_key"], "result": run_job(job["job_key"], force=False)})
    return jsonify({"ok": True, "ran": len(results), "results": results, "generated_at": _now_iso()})


@bp_automation_engine_v191.route("/api/v191/automation/toggle/<job_key>", methods=["POST"])
def api_toggle(job_key):
    if not _authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    _init()
    con = _connect()
    try:
        row = con.execute("SELECT enabled FROM automation_jobs_v191 WHERE job_key=?", (job_key,)).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "job_not_found"}), 404
        enabled = 0 if int(row[0] or 0) else 1
        con.execute("UPDATE automation_jobs_v191 SET enabled=? WHERE job_key=?", (enabled, job_key))
        con.commit()
    finally:
        con.close()
    return jsonify({"ok": True, "job_key": job_key, "enabled": bool(enabled)})
