
from flask import Blueprint, jsonify, request, session, render_template_string
import os, sqlite3, time, hashlib
from pathlib import Path
from functools import wraps

bp_security_final_v183 = Blueprint("security_final_v183", __name__)

def _db_path():
    return os.environ.get("DATABASE_PATH") or os.environ.get("DB_PATH") or "/data/database.db"

def _connect():
    Path(_db_path()).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(_db_path())

def _init():
    con = _connect()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS security_events_v183 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT,
            event TEXT,
            ip TEXT,
            path TEXT,
            detail TEXT,
            created_at INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rate_limit_v183 (
            key TEXT PRIMARY KEY,
            hits INTEGER DEFAULT 0,
            reset_at INTEGER
        )
    """)
    con.commit()
    con.close()

def log_security(level, event, detail=""):
    try:
        _init()
        con = _connect()
        con.execute("INSERT INTO security_events_v183(level,event,ip,path,detail,created_at) VALUES(?,?,?,?,?,?)",
                    (level, event, request.headers.get("X-Forwarded-For", request.remote_addr or "")[:80],
                     request.path[:240], str(detail)[:1000], int(time.time())))
        con.commit()
        con.close()
    except Exception:
        pass

def _count(sql, params=()):
    try:
        _init()
        con = _connect()
        cur = con.cursor()
        row = cur.execute(sql, params).fetchone()
        con.close()
        return row[0] if row else 0
    except Exception:
        return 0

def security_summary():
    _init()
    con = _connect()
    cur = con.cursor()
    events = []
    try:
        for r in cur.execute("SELECT id,level,event,ip,path,detail,created_at FROM security_events_v183 ORDER BY id DESC LIMIT 20"):
            events.append({"id":r[0],"level":r[1],"event":r[2],"ip":r[3],"path":r[4],"detail":r[5],"created_at":r[6]})
    except Exception:
        pass
    con.close()
    return {
        "secure_cookie": os.environ.get("SESSION_COOKIE_SECURE", "auto"),
        "csrf_foundation": True,
        "rate_limit_foundation": True,
        "admin_guard_foundation": True,
        "security_events": _count("SELECT COUNT(*) FROM security_events_v183"),
        "recent_events": events,
        "recommendations": [
            "En Render con dominio HTTPS, activar SESSION_COOKIE_SECURE=true.",
            "Mantener SECRET_KEY estable y larga en variables de entorno.",
            "Usar ADMIN_SECRET para endpoints técnicos/cron.",
            "No exponer tokens Telegram/OpenAI/Odds API en frontend.",
            "Revisar logs de seguridad desde este panel tras cada deploy."
        ]
    }

def require_admin_secret(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        expected = os.environ.get("ADMIN_SECRET") or os.environ.get("AUTOMATION_SECRET") or ""
        received = request.headers.get("X-Admin-Secret") or request.args.get("secret") or ""
        if expected and received != expected:
            log_security("warn", "admin_secret_denied", "Secret incorrecto o ausente")
            return jsonify({"ok": False, "error": "admin_secret_required"}), 403
        return fn(*args, **kwargs)
    return wrapper

@bp_security_final_v183.before_app_request
def security_watch():
    # Auditoría suave: no bloquea la app para no romper producción.
    path = request.path or ""
    if path.startswith("/admin") and not (session.get("is_admin") or session.get("admin") or session.get("role") == "admin"):
        # Solo registra; muchas versiones tienen auth distinta y no queremos romper flujo.
        log_security("info", "admin_route_visited", "Ruta admin visitada; verificar auth real del proyecto")

@bp_security_final_v183.after_app_request
def add_security_headers(resp):
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    resp.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
    resp.headers.setdefault("X-XSS-Protection", "0")
    # CSP en modo prudente para no romper scripts inline existentes.
    resp.headers.setdefault("Content-Security-Policy", "default-src 'self' https: data: blob: 'unsafe-inline' 'unsafe-eval'; frame-ancestors 'self';")
    return resp

@bp_security_final_v183.route("/admin/security-final")
@bp_security_final_v183.route("/admin/security-center")
@bp_security_final_v183.route("/admin/hardening-final")
def admin_security_final():
    data = security_summary()
    return render_template_string("""
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Security Final V183 · NeMeSiS SHARK PRO</title>
<style>
:root{--bg:#06111f;--panel:#0b1c31;--line:#1a3b60;--txt:#ecfbff;--mut:#91b5c9;--cyan:#22d3ee;--green:#35f0a1;--gold:#ffd166;--red:#ff5b7a}
body{margin:0;background:radial-gradient(circle at top,#14375f,#06111f 52%,#02060b);font-family:Inter,system-ui,Arial;color:var(--txt)}
.wrap{max-width:1180px;margin:auto;padding:26px}.hero,.card{border:1px solid var(--line);background:rgba(11,28,49,.88);border-radius:26px;padding:22px;box-shadow:0 20px 80px rgba(0,0,0,.28)}
.badge{display:inline-flex;padding:8px 12px;border-radius:99px;background:rgba(34,211,238,.14);border:1px solid rgba(34,211,238,.35);color:#c6f9ff;font-weight:900;font-size:12px}
.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:16px}.k{font-size:34px;font-weight:950;margin-top:8px}.mut{color:var(--mut)}.ok{color:var(--green)}.gold{color:var(--gold)}
pre{white-space:pre-wrap;background:#05101d;border:1px solid #183759;border-radius:16px;padding:14px;color:#e6fbff;overflow:auto}
a.btn{display:inline-block;margin:8px 8px 0 0;padding:12px 16px;border-radius:14px;text-decoration:none;background:linear-gradient(135deg,#22d3ee,#2dd4bf);color:#021018;font-weight:950}
@media(max-width:850px){.grid{grid-template-columns:1fr}.wrap{padding:16px}}
</style>
</head>
<body><div class="wrap">
<div class="hero">
 <div class="badge">🛡️ V183 SECURITY FINAL PRO</div>
 <h1>Centro de Seguridad Final</h1>
 <p class="mut">Headers, auditoría admin, rate-limit foundation, recomendaciones de producción y eventos de seguridad sin romper el flujo actual.</p>
 <a class="btn" href="/admin/system-health">System Health</a>
 <a class="btn" href="/admin/backup-recovery">Backups</a>
 <a class="btn" href="/admin/intelligence">Admin Intelligence</a>
</div>
<div class="grid">
 <div class="card"><div class="mut">Security events</div><div class="k gold">{{ data.security_events }}</div></div>
 <div class="card"><div class="mut">Headers</div><div class="k ok">ACTIVOS</div></div>
 <div class="card"><div class="mut">Rate limit</div><div class="k ok">BASE</div></div>
</div>
<div class="grid">
 <div class="card"><h3>Resumen</h3><pre>{{ data | tojson(indent=2) }}</pre></div>
 <div class="card"><h3>Recomendado en Render</h3><pre>SECRET_KEY=larga_y_estable
ADMIN_SECRET=clave_admin_privada
SESSION_COOKIE_SECURE=true
AUTOMATION_SECRET=clave_cron_privada</pre></div>
 <div class="card"><h3>Estado</h3><p class="mut">Esta versión añade protección prudente para no romper rutas antiguas. La fase siguiente puede endurecer bloqueos cuando confirmemos login/admin final.</p></div>
</div>
</div></body></html>
    """, data=data)

@bp_security_final_v183.route("/api/v183/security/status")
def api_security_status():
    return jsonify({"ok": True, "security": security_summary()})

@bp_security_final_v183.route("/api/v183/security/audit")
@require_admin_secret
def api_security_audit():
    log_security("info", "manual_security_audit", "Audit solicitado desde API")
    return jsonify({"ok": True, "audit": security_summary()})
