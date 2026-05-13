from flask import Blueprint, jsonify, render_template_string, request
import os, sqlite3, time, json
from pathlib import Path

bp_app_feel_v193 = Blueprint("app_feel_v193", __name__)
VERSION = "V193_APP_FEEL_ULTRA_PREMIUM"


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
        CREATE TABLE IF NOT EXISTS app_feel_events_v193 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT,
            page TEXT,
            payload_json TEXT,
            created_at INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS app_feel_health_v193 (
            metric_key TEXT PRIMARY KEY,
            metric_value TEXT,
            updated_at INTEGER
        )
    """)
    con.commit(); con.close()


def _tables():
    con = _connect()
    try:
        return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    except Exception:
        return set()
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


def _read_recent(table, limit=20):
    if table not in _tables():
        return []
    con = _connect()
    try:
        return [dict(r) for r in con.execute(f"SELECT * FROM {table} ORDER BY id DESC LIMIT ?", (int(limit),)).fetchall()]
    except Exception:
        return []
    finally:
        con.close()


def _score_app_feel():
    tables = _tables()
    signals = _count("match_intelligence_signals_v192")
    snapshots = _count("data_snapshots_v190")
    fixtures = sum(_count(t) for t in ["fixtures_cache", "fixtures", "real_fixtures", "matches_cache", "matches"] if t in tables)
    automation = _count("automation_runs_v191") if "automation_runs_v191" in tables else _count("automation_engine_runs_v191")
    base = 72
    base += 7 if fixtures else 0
    base += 6 if snapshots else 0
    base += 6 if signals else 0
    base += 4 if automation else 0
    return max(1, min(99, base))


def _payload():
    _init()
    return {
        "version": VERSION,
        "estado": "activo",
        "idioma": "español",
        "filosofia": "REAL ONLY: sin partidos falsos, sin picks falsos, sin marcadores falsos",
        "app_feel_score": _score_app_feel(),
        "mejoras": [
            "Skeleton loaders premium para cargas reales sin sensación vacía.",
            "Transiciones suaves entre tarjetas, paneles y estados live.",
            "Microinteracciones móviles para botones, cards, tabs y navegación inferior.",
            "Pulido PWA con safe-area, tacto móvil y reducción de saltos visuales.",
            "Estados vacíos en español, más elegantes y sin mensajes feos para cliente.",
            "Observabilidad ligera de experiencia sin consumir APIs deportivas."
        ],
        "rutas": {
            "cliente": ["/cliente/app-feel", "/cliente/ultra-premium"],
            "admin": ["/admin/app-feel"],
            "api": ["/api/v193/app-feel/status", "/api/v193/app-feel/track"]
        },
        "contadores_reales": {
            "fixtures": sum(_count(t) for t in ["fixtures_cache", "fixtures", "real_fixtures", "matches_cache", "matches"] if t in _tables()),
            "snapshots_v190": _count("data_snapshots_v190"),
            "senales_v192": _count("match_intelligence_signals_v192"),
            "eventos_app_v193": _count("app_feel_events_v193")
        },
        "timestamp": int(time.time())
    }


@bp_app_feel_v193.after_app_request
def _headers(resp):
    resp.headers.setdefault("X-NeMeSiS-App-Feel", VERSION)
    # Mantiene PWA ágil sin forzar caché agresiva sobre APIs reales.
    if request.path.startswith("/api/"):
        resp.headers.setdefault("Cache-Control", "no-store")
    return resp


@bp_app_feel_v193.route("/api/v193/app-feel/status")
def api_status():
    return jsonify(_payload())


@bp_app_feel_v193.route("/api/v193/app-feel/track", methods=["POST"])
def api_track():
    _init()
    data = request.get_json(silent=True) or {}
    event_type = str(data.get("event_type") or "interaccion")[:80]
    page = str(data.get("page") or request.headers.get("Referer") or "")[:240]
    payload = json.dumps(data.get("payload") or {}, ensure_ascii=False, default=str)[:4000]
    con = _connect()
    con.execute("INSERT INTO app_feel_events_v193(event_type,page,payload_json,created_at) VALUES(?,?,?,?)", (event_type, page, payload, int(time.time())))
    con.commit(); con.close()
    return jsonify({"ok": True, "mensaje": "Evento de experiencia guardado", "version": VERSION})


PAGE = """
<!doctype html><html lang='es'><head>
<meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1,viewport-fit=cover'>
<title>NeMeSiS SHARK PRO · App Feel Ultra Premium</title>
<link rel='stylesheet' href='/static/app.css'>
<link rel='stylesheet' href='/static/css/v193_app_feel_ultra_premium.css'>
</head><body class='v193-body'>
<main class='v193-shell'>
  <section class='v193-hero v193-reveal'>
    <div><p class='v193-kicker'>V193 · APP FEEL ULTRA PREMIUM</p><h1>La app ahora se siente más rápida, suave y premium.</h1>
    <p>Este módulo no inventa datos: mejora la experiencia visual, la navegación móvil, los estados de carga y los vacíos elegantes usando el core real ya montado.</p>
    <div class='v193-actions'><a class='v193-btn primary' href='/cliente/pro'>Ir al panel cliente</a><a class='v193-btn' href='/match-intelligence-real'>Ver inteligencia de partido</a></div></div>
    <aside class='v193-score-card'><span>App Feel Score</span><strong>{{ data.app_feel_score }}/100</strong><small>Basado en módulos reales disponibles, snapshots y señales.</small></aside>
  </section>
  <section class='v193-grid'>
    {% for item in data.mejoras %}<article class='v193-card v193-reveal'><span class='v193-dot'></span><h3>{{ item.split(' para ')[0] }}</h3><p>{{ item }}</p></article>{% endfor %}
  </section>
  <section class='v193-panel v193-reveal'><h2>Contadores reales</h2><div class='v193-metrics'>
    {% for k,v in data.contadores_reales.items() %}<div><span>{{ k.replace('_',' ') }}</span><strong>{{ v }}</strong></div>{% endfor %}
  </div><p class='v193-note'>Si algún contador está a cero, se muestra como estado real vacío. No se rellenan datos falsos.</p></section>
</main><script src='/static/js/v193_app_feel_ultra_premium.js'></script></body></html>
"""


@bp_app_feel_v193.route("/cliente/app-feel")
@bp_app_feel_v193.route("/cliente/ultra-premium")
def cliente_app_feel():
    return render_template_string(PAGE, data=_payload())


@bp_app_feel_v193.route("/admin/app-feel")
def admin_app_feel():
    data = _payload()
    data["eventos_recientes"] = _read_recent("app_feel_events_v193", 15)
    return render_template_string(PAGE.replace("Contadores reales", "Panel admin · experiencia app").replace("Ir al panel cliente", "Volver al panel cliente"), data=data)
