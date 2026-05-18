
import os, json, sqlite3, time, urllib.request, urllib.parse
from pathlib import Path

DB_PATH = os.getenv("DATABASE_PATH") or os.getenv("DB_PATH") or "/data/database.db"
ODDS_API_BASE = os.getenv("ODDS_API_BASE", "https://api.the-odds-api.com/v4")
DEFAULT_SPORT = os.getenv("ODDS_DEFAULT_SPORT", "soccer_epl")
DEFAULT_REGIONS = os.getenv("ODDS_REGIONS", "eu,uk")
DEFAULT_MARKETS = os.getenv("ODDS_MARKETS", "h2h")
DEFAULT_ODDS_FORMAT = os.getenv("ODDS_FORMAT", "decimal")

def _key():
    return os.getenv("THE_ODDS_API_KEY") or os.getenv("ODDS_API_KEY")

def _connect():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def ensure_tables():
    con = _connect()
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS provider_cache_v353 (
      cache_key TEXT PRIMARY KEY,
      provider TEXT DEFAULT 'the_odds_api',
      group_name TEXT,
      sport_key TEXT,
      payload TEXT,
      status TEXT DEFAULT 'cold',
      http_status INTEGER,
      message TEXT,
      fetched_ts INTEGER DEFAULT 0,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS provider_events_v353 (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      provider TEXT,
      group_name TEXT,
      sport_key TEXT,
      severity TEXT DEFAULT 'info',
      message TEXT,
      created_ts INTEGER DEFAULT 0,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    con.commit()
    con.close()

def _log(group, sport, severity, message):
    ensure_tables()
    con = _connect()
    cur = con.cursor()
    cur.execute("""
    INSERT INTO provider_events_v353(provider,group_name,sport_key,severity,message,created_ts)
    VALUES(?,?,?,?,?,?)
    """, ("the_odds_api", group, sport, severity, message, int(time.time())))
    con.commit()
    con.close()

def save_cache(cache_key, group, sport, payload, status="ok", http_status=200, message="OK"):
    ensure_tables()
    con = _connect()
    cur = con.cursor()
    cur.execute("""
    INSERT INTO provider_cache_v353(cache_key,provider,group_name,sport_key,payload,status,http_status,message,fetched_ts)
    VALUES(?,?,?,?,?,?,?,?,?)
    ON CONFLICT(cache_key) DO UPDATE SET
      payload=excluded.payload,
      status=excluded.status,
      http_status=excluded.http_status,
      message=excluded.message,
      fetched_ts=excluded.fetched_ts,
      updated_at=CURRENT_TIMESTAMP
    """, (cache_key, "the_odds_api", group, sport, json.dumps(payload, ensure_ascii=False), status, http_status, message, int(time.time())))
    con.commit()
    con.close()

def get_cache(cache_key):
    ensure_tables()
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT * FROM provider_cache_v353 WHERE cache_key=?", (cache_key,))
    row = cur.fetchone()
    con.close()
    if not row:
        return None
    d = dict(row)
    try:
        d["payload"] = json.loads(d.get("payload") or "null")
    except Exception:
        pass
    return d

def _request_json(path, params):
    api_key = _key()
    if not api_key:
        return {"ok": False, "status": 0, "error": "missing THE_ODDS_API_KEY/ODDS_API_KEY", "data": None}
    params = dict(params or {})
    params["apiKey"] = api_key
    url = ODDS_API_BASE.rstrip("/") + path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "NeMeSiS-SHARK-PRO/353"})
    try:
        with urllib.request.urlopen(req, timeout=18) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            data = json.loads(raw) if raw else None
            return {"ok": True, "status": getattr(resp, "status", 200), "data": data, "error": None}
    except Exception as exc:
        return {"ok": False, "status": 0, "error": str(exc), "data": None}

def normalize_odds_event(event):
    home = event.get("home_team") or event.get("home") or "Local"
    away = event.get("away_team") or event.get("away") or "Visitante"
    league = event.get("sport_title") or event.get("sport_key") or ""
    commence = event.get("commence_time")
    odds = {"1": None, "X": None, "2": None}
    bookmakers = event.get("bookmakers") or []
    if bookmakers:
        markets = bookmakers[0].get("markets") or []
        for market in markets:
            if market.get("key") == "h2h":
                for outcome in market.get("outcomes") or []:
                    name = outcome.get("name")
                    price = outcome.get("price")
                    if name == home:
                        odds["1"] = price
                    elif name == away:
                        odds["2"] = price
                    elif str(name).lower() in ["draw", "empate", "x"]:
                        odds["X"] = price
    return {
        "id": str(event.get("id") or f"{home}-{away}-{commence}"),
        "home": home,
        "away": away,
        "league": league,
        "commence_time": commence,
        "status": "scheduled",
        "score": {"home": None, "away": None, "text": "vs"},
        "minute": {"raw": None, "text": "Pre"},
        "crests": {
            "home": {"url": None, "fallback": True, "initials": "".join([p[:1].upper() for p in home.split()[:2]]) or "FC", "label": home},
            "away": {"url": None, "fallback": True, "initials": "".join([p[:1].upper() for p in away.split()[:2]]) or "FC", "label": away},
        },
        "odds_1x2": odds,
        "real_only": True,
        "source": "the_odds_api"
    }

def fetch_odds(sport=None, regions=None, markets=None):
    sport = sport or DEFAULT_SPORT
    regions = regions or DEFAULT_REGIONS
    markets = markets or DEFAULT_MARKETS
    cache_key = f"odds:{sport}:{regions}:{markets}"
    result = _request_json(f"/sports/{sport}/odds", {
        "regions": regions,
        "markets": markets,
        "oddsFormat": DEFAULT_ODDS_FORMAT,
    })
    if result["ok"]:
        normalized = [normalize_odds_event(e) for e in (result["data"] or [])]
        payload = {"raw_count": len(result["data"] or []), "matches": normalized}
        save_cache(cache_key, "odds_1x2", sport, payload, "ok", result["status"], "API OK")
        _log("odds_1x2", sport, "info", f"API OK · {len(normalized)} eventos")
        return {"ok": True, "version": "V353", "cache_key": cache_key, **payload}
    cached = get_cache(cache_key)
    msg = result.get("error") or "API error"
    _log("odds_1x2", sport, "warning", msg)
    if cached and cached.get("payload"):
        return {"ok": True, "version": "V353", "cache_key": cache_key, "from_cache": True, "warning": msg, **cached["payload"]}
    save_cache(cache_key, "odds_1x2", sport, {"matches": [], "raw_count": 0, "error": msg}, "low_data", result["status"], msg)
    return {"ok": False, "version": "V353", "cache_key": cache_key, "matches": [], "raw_count": 0, "error": msg, "low_data": True}

def provider_status():
    ensure_tables()
    api_key = _key()
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT group_name, COUNT(*) AS n, MAX(fetched_ts) AS last_ts FROM provider_cache_v353 GROUP BY group_name")
    groups = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT severity, message, created_at FROM provider_events_v353 ORDER BY id DESC LIMIT 15")
    events = [dict(r) for r in cur.fetchall()]
    con.close()
    return {
        "ok": True,
        "version": "V353",
        "name": "REAL_PROVIDER_CONNECTOR_AUTO_REFRESH_PRO",
        "provider": "the_odds_api",
        "api_key_present": bool(api_key),
        "default_sport": DEFAULT_SPORT,
        "cache_groups": groups,
        "recent_events": events,
        "routes": [
            "/api/provider/status-v353",
            "/api/provider/refresh/odds-v353",
            "/api/provider/cache/odds-v353",
            "/cliente/provider-connector"
        ],
        "circuit": "API -> cache -> normalizer/UI -> cliente",
        "real_only": True
    }

def cached_odds(sport=None):
    sport = sport or DEFAULT_SPORT
    prefix = f"odds:{sport}:"
    ensure_tables()
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT * FROM provider_cache_v353 WHERE cache_key LIKE ? ORDER BY fetched_ts DESC LIMIT 1", (prefix + "%",))
    row = cur.fetchone()
    con.close()
    if not row:
        return {"ok": False, "version": "V353", "matches": [], "low_data": True, "message": "Sin caché de odds"}
    d = dict(row)
    try:
        payload = json.loads(d.get("payload") or "{}")
    except Exception:
        payload = {}
    return {"ok": True, "version": "V353", "cache_key": d.get("cache_key"), "status": d.get("status"), **payload}
