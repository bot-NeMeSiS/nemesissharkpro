
from flask import Blueprint, jsonify, request, render_template_string, Response
import os, sqlite3, json, time, hashlib, re
from pathlib import Path

bp_sports_visual_v185 = Blueprint("sports_visual_v185", __name__)

COUNTRY_FLAGS = {
    "spain": "🇪🇸", "españa": "🇪🇸", "england": "🏴", "inglaterra": "🏴",
    "italy": "🇮🇹", "italia": "🇮🇹", "germany": "🇩🇪", "alemania": "🇩🇪",
    "france": "🇫🇷", "francia": "🇫🇷", "portugal": "🇵🇹", "netherlands": "🇳🇱",
    "brazil": "🇧🇷", "brasil": "🇧🇷", "argentina": "🇦🇷", "usa": "🇺🇸",
    "united states": "🇺🇸", "mexico": "🇲🇽", "world": "🌍", "europe": "🇪🇺"
}
LEAGUE_BADGES = {
    "laliga": "🇪🇸", "la liga": "🇪🇸", "premier": "🏴", "serie a": "🇮🇹",
    "bundesliga": "🇩🇪", "ligue 1": "🇫🇷", "champions": "🏆", "europa": "🏆",
    "nba": "🏀", "euroleague": "🏀", "nfl": "🏈", "mlb": "⚾", "nhl": "🏒"
}

def _db_path():
    return os.environ.get("DATABASE_PATH") or os.environ.get("DB_PATH") or "/data/database.db"

def _connect():
    Path(_db_path()).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(_db_path())

def _init():
    con = _connect()
    cur = con.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS sports_visual_assets_v185 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_type TEXT,
            entity_name TEXT,
            entity_key TEXT UNIQUE,
            logo_url TEXT,
            local_path TEXT,
            fallback_svg TEXT,
            color_a TEXT,
            color_b TEXT,
            source TEXT,
            status TEXT DEFAULT 'fallback',
            updated_at INTEGER,
            created_at INTEGER
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS sports_visual_logs_v185 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT,
            event TEXT,
            detail TEXT,
            created_at INTEGER
        )
    ''')
    con.commit()
    con.close()

def _slug(s):
    s = str(s or "").strip().lower()
    s = re.sub(r"[^a-z0-9áéíóúñü]+", "-", s)
    return s.strip("-") or "unknown"

def _colors(name):
    h = hashlib.md5(str(name or "team").encode("utf-8")).hexdigest()
    return "#" + h[:6], "#" + h[6:12]

def _initials(name):
    words = re.findall(r"[A-Za-zÁÉÍÓÚÑÜáéíóúñü0-9]+", str(name or "TEAM"))
    if not words:
        return "NS"
    if len(words) == 1:
        return words[0][:3].upper()
    return (words[0][0] + words[-1][0]).upper()

def _svg_badge(name, asset_type="team"):
    a, b = _colors(name)
    ini = _initials(name)
    icon = "🦈" if asset_type == "shark" else ("🏆" if asset_type == "league" else "")
    y = 50 if not icon else 42
    fs = 24 if len(ini) <= 2 else 20
    extra = ""
    if icon:
        extra = f'<text x="48" y="68" font-size="16" text-anchor="middle" dominant-baseline="middle">{icon}</text>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96">
<defs><linearGradient id="g" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient>
<filter id="s"><feDropShadow dx="0" dy="6" stdDeviation="7" flood-color="#000" flood-opacity=".45"/></filter></defs>
<rect width="96" height="96" rx="24" fill="#06111f"/>
<circle cx="48" cy="48" r="38" fill="url(#g)" filter="url(#s)" opacity=".92"/>
<circle cx="48" cy="48" r="31" fill="none" stroke="rgba(255,255,255,.45)" stroke-width="2"/>
<text x="48" y="{y}" font-family="Inter,Arial,sans-serif" font-size="{fs}" font-weight="900" text-anchor="middle" dominant-baseline="middle" fill="white">{ini}</text>
{extra}
</svg>'''

def _ensure_asset(entity_name, asset_type="team", logo_url=None, source="fallback"):
    _init()
    entity_key = f"{asset_type}:{_slug(entity_name)}"
    svg = _svg_badge(entity_name, asset_type)
    a, b = _colors(entity_name)
    con = _connect()
    now = int(time.time())
    con.execute('''
        INSERT INTO sports_visual_assets_v185(asset_type,entity_name,entity_key,logo_url,fallback_svg,color_a,color_b,source,status,updated_at,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(entity_key) DO UPDATE SET
            entity_name=excluded.entity_name,
            logo_url=COALESCE(NULLIF(excluded.logo_url,''), sports_visual_assets_v185.logo_url),
            fallback_svg=excluded.fallback_svg,
            color_a=excluded.color_a,
            color_b=excluded.color_b,
            source=excluded.source,
            updated_at=excluded.updated_at
    ''', (asset_type, str(entity_name or "Equipo"), entity_key, logo_url or "", svg, a, b, source, "remote" if logo_url else "fallback", now, now))
    con.commit()
    con.close()
    return _asset_payload(entity_name, asset_type)

def _asset_payload(entity_name, asset_type="team"):
    _init()
    entity_key = f"{asset_type}:{_slug(entity_name)}"
    con = _connect()
    con.row_factory = sqlite3.Row
    row = con.execute("SELECT * FROM sports_visual_assets_v185 WHERE entity_key=?", (entity_key,)).fetchone()
    con.close()
    if not row:
        return _ensure_asset(entity_name, asset_type)
    d = dict(row)
    fallback = f"/api/v185/visual/asset/{d.get('entity_key')}.svg"
    return {
        "name": d.get("entity_name"),
        "type": d.get("asset_type"),
        "key": d.get("entity_key"),
        "logo_url": d.get("logo_url") or "",
        "fallback_url": fallback,
        "display_url": d.get("logo_url") or fallback,
        "color_a": d.get("color_a"),
        "color_b": d.get("color_b"),
        "status": d.get("status") or "fallback",
        "source": d.get("source") or "fallback"
    }

def _tables():
    con = _connect()
    try:
        return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    except Exception:
        return set()
    finally:
        con.close()

def _rows_from_table(table, limit=40):
    con = _connect()
    con.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in con.execute(f"SELECT * FROM {table} LIMIT {int(limit)}").fetchall()]
    except Exception:
        return []
    finally:
        con.close()

def _pick(row, names):
    lower = {k.lower(): k for k in row.keys()}
    for n in names:
        k = lower.get(n)
        if k and row.get(k) not in (None, ""):
            return row.get(k)
    for k in row.keys():
        lk = k.lower()
        if any(n in lk for n in names) and row.get(k) not in (None, ""):
            return row.get(k)
    return ""

def _flag_for(text):
    t = str(text or "").lower()
    for k, v in COUNTRY_FLAGS.items():
        if k in t:
            return v
    return "🌍"

def _league_badge(text):
    t = str(text or "").lower()
    for k, v in LEAGUE_BADGES.items():
        if k in t:
            return v
    return "🏆"

def _extract_match(row):
    if not row:
        return None
    home = _pick(row, ["home_team", "home", "team_home", "home_name", "local"])
    away = _pick(row, ["away_team", "away", "team_away", "away_name", "visitor", "visitante"])
    league = _pick(row, ["league", "competition", "competition_name", "sport_title", "liga"])
    country = _pick(row, ["country", "region", "area"])
    status = _pick(row, ["status", "state", "fixture_status", "match_status"]) or "scheduled"
    minute = _pick(row, ["minute", "elapsed", "time", "match_minute"])
    score_home = _pick(row, ["home_score", "score_home", "goals_home", "home_goals"])
    score_away = _pick(row, ["away_score", "score_away", "goals_away", "away_goals"])
    mid = _pick(row, ["id", "fixture_id", "match_id", "event_id"]) or hashlib.md5(json.dumps(row, sort_keys=True, default=str).encode()).hexdigest()[:12]
    home_logo = _pick(row, ["home_logo", "home_team_logo", "logo_home"])
    away_logo = _pick(row, ["away_logo", "away_team_logo", "logo_away"])
    league_logo = _pick(row, ["league_logo", "competition_logo"])
    home = str(home or "Local")
    away = str(away or "Visitante")
    league = str(league or "Competición")
    _ensure_asset(home, "team", home_logo, "fixture" if home_logo else "fallback")
    _ensure_asset(away, "team", away_logo, "fixture" if away_logo else "fallback")
    _ensure_asset(league, "league", league_logo, "fixture" if league_logo else "fallback")
    return {
        "id": str(mid),
        "home": home,
        "away": away,
        "league": league,
        "country": str(country or ""),
        "country_flag": _flag_for(country or league),
        "league_badge": _league_badge(league),
        "status": str(status),
        "minute": str(minute or ""),
        "score_home": str(score_home or ""),
        "score_away": str(score_away or ""),
        "home_asset": _asset_payload(home, "team"),
        "away_asset": _asset_payload(away, "team"),
        "league_asset": _asset_payload(league, "league"),
        "raw": row
    }

def _real_matches(limit=30):
    tables = ["fixtures_cache", "fixtures", "real_fixtures", "matches_cache", "matches"]
    found = []
    present = _tables()
    for table in tables:
        if table not in present:
            continue
        for row in _rows_from_table(table, limit=limit):
            m = _extract_match(row)
            if m:
                m["source_table"] = table
                found.append(m)
            if len(found) >= limit:
                return found
    return found

@bp_sports_visual_v185.route("/api/v185/visual/asset/<path:key>.svg")
def api_asset_svg(key):
    _init()
    entity_key = key.replace(".svg", "")
    con = _connect()
    row = con.execute("SELECT fallback_svg FROM sports_visual_assets_v185 WHERE entity_key=?", (entity_key,)).fetchone()
    con.close()
    svg = row[0] if row and row[0] else _svg_badge(entity_key.split(":")[-1], "team")
    return Response(svg, mimetype="image/svg+xml")

@bp_sports_visual_v185.route("/api/v185/visual/team")
def api_team_asset():
    name = request.args.get("name") or "Equipo"
    return jsonify({"ok": True, "asset": _ensure_asset(name, "team")})

@bp_sports_visual_v185.route("/api/v185/visual/league")
def api_league_asset():
    name = request.args.get("name") or "Liga"
    return jsonify({"ok": True, "asset": _ensure_asset(name, "league")})

@bp_sports_visual_v185.route("/api/v185/visual/matches")
def api_visual_matches():
    limit = int(request.args.get("limit", 30))
    matches = _real_matches(limit)
    return jsonify({"ok": True, "count": len(matches), "matches": matches, "policy": "real-only; fallback visual allowed para identidad, no inventa partidos"})

@bp_sports_visual_v185.route("/api/v185/visual/status")
def api_visual_status():
    _init()
    con = _connect()
    cur = con.cursor()
    def one(sql):
        try:
            return cur.execute(sql).fetchone()[0]
        except Exception:
            return 0
    data = {
        "assets_total": one("SELECT COUNT(*) FROM sports_visual_assets_v185"),
        "team_assets": one("SELECT COUNT(*) FROM sports_visual_assets_v185 WHERE asset_type='team'"),
        "league_assets": one("SELECT COUNT(*) FROM sports_visual_assets_v185 WHERE asset_type='league'"),
        "remote_logos": one("SELECT COUNT(*) FROM sports_visual_assets_v185 WHERE status='remote'"),
        "fallback_logos": one("SELECT COUNT(*) FROM sports_visual_assets_v185 WHERE status='fallback'"),
        "real_matches_detected": len(_real_matches(50)),
        "tables_detected": sorted(list(_tables()))[:80]
    }
    con.close()
    return jsonify({"ok": True, "visual_system": data})

@bp_sports_visual_v185.route("/sports-visual-pro")
@bp_sports_visual_v185.route("/cliente/sports-visual")
@bp_sports_visual_v185.route("/admin/sports-visual")
def sports_visual_page():
    _init()
    matches = _real_matches(18)
    con = _connect()
    cur = con.cursor()
    def one(sql):
        try:
            return cur.execute(sql).fetchone()[0]
        except Exception:
            return 0
    status = {
        "assets_total": one("SELECT COUNT(*) FROM sports_visual_assets_v185"),
        "team_assets": one("SELECT COUNT(*) FROM sports_visual_assets_v185 WHERE asset_type='team'"),
        "league_assets": one("SELECT COUNT(*) FROM sports_visual_assets_v185 WHERE asset_type='league'"),
        "remote_logos": one("SELECT COUNT(*) FROM sports_visual_assets_v185 WHERE status='remote'"),
        "fallback_logos": one("SELECT COUNT(*) FROM sports_visual_assets_v185 WHERE status='fallback'"),
        "real_matches_detected": len(matches)
    }
    con.close()
    return render_template_string('''
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sports Visual V185 · NeMeSiS SHARK PRO</title>
<style>
:root{--bg:#06111f;--panel:#0b1c31;--line:#1b4169;--txt:#eafbff;--mut:#91b4c9;--cyan:#22d3ee;--green:#35f0a1;--gold:#ffd166;--red:#ff5b7a}
body{margin:0;background:radial-gradient(circle at top,#153c66,#06111f 52%,#02060b);font-family:Inter,system-ui,Arial;color:var(--txt)}
.wrap{max-width:1220px;margin:auto;padding:24px}.hero,.card{border:1px solid var(--line);background:rgba(11,28,49,.88);border-radius:26px;padding:22px;box-shadow:0 20px 80px rgba(0,0,0,.28)}
.badge{display:inline-flex;padding:8px 12px;border-radius:99px;background:rgba(34,211,238,.14);border:1px solid rgba(34,211,238,.35);color:#c9f9ff;font-weight:900;font-size:12px}
.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:16px}.grid4{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;margin-top:16px}
.match{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:12px;border:1px solid #183b61;background:linear-gradient(135deg,rgba(34,211,238,.08),rgba(255,209,102,.05));border-radius:24px;padding:16px}
.team{text-align:center}.logo{width:64px;height:64px;border-radius:20px;object-fit:cover;box-shadow:0 12px 35px rgba(0,0,0,.35);border:1px solid rgba(255,255,255,.16);background:#071526}.name{font-weight:950;margin-top:8px}
.vs{text-align:center}.score{font-size:26px;font-weight:950}.league{color:var(--mut);font-size:13px}.pill{display:inline-flex;padding:6px 10px;border-radius:99px;background:rgba(34,211,238,.12);border:1px solid rgba(34,211,238,.28);font-size:12px;font-weight:850;color:#d9fbff}
.k{font-size:32px;font-weight:950;margin-top:6px}.mut{color:var(--mut)}.ok{color:var(--green)}.gold{color:var(--gold)}
.btn{display:inline-block;margin:8px 8px 0 0;padding:12px 16px;border-radius:14px;text-decoration:none;background:linear-gradient(135deg,#22d3ee,#2dd4bf);color:#021018;font-weight:950;border:0;cursor:pointer}
.btn2{background:#102a45;color:#dff8ff;border:1px solid #245078}
pre{white-space:pre-wrap;background:#05101d;border:1px solid #183759;border-radius:16px;padding:14px;color:#e6fbff;overflow:auto}
.empty{padding:28px;border:1px dashed #2b5f92;border-radius:24px;text-align:center;color:var(--mut)}
@media(max-width:900px){.grid,.grid4{grid-template-columns:1fr}.wrap{padding:16px}.match{grid-template-columns:1fr}.logo{width:56px;height:56px}}
</style>
</head>
<body>
<div class="wrap">
 <div class="hero">
  <div class="badge">🎨 V185 REAL SPORTS VISUAL SYSTEM</div>
  <h1>Escudos, ligas, banderas y match cards PRO</h1>
  <p class="mut">Sistema visual deportivo real-only: usa logos reales si vienen de la API/caché y fallback premium si no existen, sin inventar partidos ni marcadores.</p>
  <a class="btn" href="/api/v185/visual/matches">API partidos visuales</a>
  <a class="btn btn2" href="/match-intelligence-pro">Match Intelligence</a>
  <a class="btn btn2" href="/admin/match-analytics">Admin Match Analytics</a>
 </div>

 <div class="grid4">
  <div class="card"><div class="mut">Assets</div><div class="k ok">{{ status.assets_total }}</div></div>
  <div class="card"><div class="mut">Equipos</div><div class="k">{{ status.team_assets }}</div></div>
  <div class="card"><div class="mut">Ligas</div><div class="k gold">{{ status.league_assets }}</div></div>
  <div class="card"><div class="mut">Partidos reales detectados</div><div class="k">{{ status.real_matches_detected }}</div></div>
 </div>

 <div class="card" style="margin-top:16px">
  <h2>Match cards PRO</h2>
  {% if matches %}
   <div class="grid">
   {% for m in matches %}
    <div class="match">
      <div class="team">
        <img class="logo" src="{{ m.home_asset.display_url }}" alt="{{ m.home }}">
        <div class="name">{{ m.home }}</div>
      </div>
      <div class="vs">
        <div class="pill">{{ m.country_flag }} {{ m.league_badge }} {{ m.status }}</div>
        <div class="score">{{ m.score_home or '—' }} : {{ m.score_away or '—' }}</div>
        <div class="league">{{ m.league }}</div>
        {% if m.minute %}<div class="pill">Min {{ m.minute }}</div>{% endif %}
      </div>
      <div class="team">
        <img class="logo" src="{{ m.away_asset.display_url }}" alt="{{ m.away }}">
        <div class="name">{{ m.away }}</div>
      </div>
    </div>
   {% endfor %}
   </div>
  {% else %}
   <div class="empty">No hay partidos reales detectados ahora mismo. El sistema visual queda preparado y no inventa fixtures.</div>
  {% endif %}
 </div>

 <div class="card" style="margin-top:16px"><h3>Estado visual</h3><pre>{{ status | tojson(indent=2) }}</pre></div>
</div>
</body>
</html>
    ''', matches=matches, status=status)
