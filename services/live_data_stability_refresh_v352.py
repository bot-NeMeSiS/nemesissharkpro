
import os, sqlite3, json, time
from pathlib import Path

DB_PATH = os.getenv("DATABASE_PATH") or os.getenv("DB_PATH") or "/data/database.db"

LIVE_TTL_SECONDS = int(os.getenv("LIVE_CACHE_TTL_SECONDS", "45"))
FIXTURES_TTL_SECONDS = int(os.getenv("FIXTURES_CACHE_TTL_SECONDS", "900"))
ODDS_TTL_SECONDS = int(os.getenv("ODDS_CACHE_TTL_SECONDS", "600"))

def _connect():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def ensure_tables():
    con = _connect()
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS live_refresh_state_v352 (
      cache_group TEXT PRIMARY KEY,
      last_refresh_ts INTEGER DEFAULT 0,
      last_ok_ts INTEGER DEFAULT 0,
      status TEXT DEFAULT 'cold',
      last_message TEXT,
      ttl_seconds INTEGER DEFAULT 60,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS live_refresh_events_v352 (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      cache_group TEXT,
      event_type TEXT,
      severity TEXT DEFAULT 'info',
      message TEXT,
      created_ts INTEGER DEFAULT 0,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    for group, ttl in [("live", LIVE_TTL_SECONDS), ("fixtures", FIXTURES_TTL_SECONDS), ("odds_1x2", ODDS_TTL_SECONDS), ("crests", 86400)]:
        cur.execute("""
        INSERT OR IGNORE INTO live_refresh_state_v352(cache_group,last_refresh_ts,last_ok_ts,status,last_message,ttl_seconds)
        VALUES(?,?,?,?,?,?)
        """, (group, 0, 0, "cold", "Esperando primer refresco real", ttl))
    con.commit()
    con.close()

def _env_present(*names):
    for name in names:
        val = os.getenv(name)
        if val:
            return {"present": True, "name": name, "length": len(val)}
    return {"present": False, "name": None, "length": 0}

def mark_refresh(cache_group, ok=True, message="manual status check"):
    ensure_tables()
    now = int(time.time())
    status = "ok" if ok else "warning"
    con = _connect()
    cur = con.cursor()
    cur.execute("""
    INSERT INTO live_refresh_state_v352(cache_group,last_refresh_ts,last_ok_ts,status,last_message,ttl_seconds)
    VALUES(?,?,?,?,?,?)
    ON CONFLICT(cache_group) DO UPDATE SET
      last_refresh_ts=excluded.last_refresh_ts,
      last_ok_ts=CASE WHEN ? THEN excluded.last_ok_ts ELSE live_refresh_state_v352.last_ok_ts END,
      status=excluded.status,
      last_message=excluded.last_message,
      updated_at=CURRENT_TIMESTAMP
    """, (cache_group, now, now if ok else 0, status, message, LIVE_TTL_SECONDS, 1 if ok else 0))
    cur.execute("""
    INSERT INTO live_refresh_events_v352(cache_group,event_type,severity,message,created_ts)
    VALUES(?,?,?,?,?)
    """, (cache_group, "refresh", "info" if ok else "warning", message, now))
    con.commit()
    con.close()

def state_rows():
    ensure_tables()
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT * FROM live_refresh_state_v352 ORDER BY cache_group")
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows

def freshness(row):
    now = int(time.time())
    last = int(row.get("last_ok_ts") or 0)
    ttl = int(row.get("ttl_seconds") or 60)
    if last <= 0:
        return {"fresh": False, "age_seconds": None, "label": "Sin refresco"}
    age = now - last
    return {
        "fresh": age <= ttl,
        "age_seconds": age,
        "label": "Fresco" if age <= ttl else "Caducado"
    }

def live_refresh_status():
    ensure_tables()
    keys = {
        "THE_ODDS_API_KEY": _env_present("THE_ODDS_API_KEY", "ODDS_API_KEY"),
        "PUBLIC_BASE_URL": _env_present("PUBLIC_BASE_URL", "RENDER_EXTERNAL_URL", "BASE_URL"),
        "TELEGRAM_BOT_TOKEN": _env_present("TELEGRAM_BOT_TOKEN", "TELEGRAM_TOKEN", "BOT_TOKEN"),
    }
    rows = state_rows()
    enriched = []
    for r in rows:
        r["freshness"] = freshness(r)
        enriched.append(r)

    diagnosis = []
    if not keys["THE_ODDS_API_KEY"]["present"]:
        diagnosis.append("Falta THE_ODDS_API_KEY/ODDS_API_KEY: live odds y 1X2 pueden quedar en LOW DATA.")
    if not keys["PUBLIC_BASE_URL"]["present"]:
        diagnosis.append("Falta PUBLIC_BASE_URL/RENDER_EXTERNAL_URL: Telegram/webhooks pueden no construir enlaces correctamente.")
    stale = [r["cache_group"] for r in enriched if not r["freshness"]["fresh"]]
    if stale:
        diagnosis.append("Grupos sin refresco fresco: " + ", ".join(stale))
    if not diagnosis:
        diagnosis.append("Live refresh preparado. Si no ves minuto/marcador, revisar proveedor de datos y normalizador V347.")

    return {
        "ok": True,
        "version": "V352",
        "name": "LIVE_DATA_STABILITY_REFRESH_ENGINE_PRO",
        "db_path": DB_PATH,
        "ttl": {
            "live": LIVE_TTL_SECONDS,
            "fixtures": FIXTURES_TTL_SECONDS,
            "odds_1x2": ODDS_TTL_SECONDS
        },
        "api_keys": keys,
        "refresh_state": enriched,
        "diagnosis": diagnosis,
        "routes": [
            "/api/live/refresh/status-v352",
            "/api/live/refresh/ping-v352?group=live",
            "/api/live/normalizer/status-v347",
            "/api/live/normalizer/sample-v347",
            "/api/real-data/pipeline/status-v346",
            "/cliente/live-stability"
        ],
        "real_only": True
    }

def ping_group(group):
    group = (group or "live").strip().lower()
    valid = {"live", "fixtures", "odds_1x2", "crests"}
    if group not in valid:
        group = "live"
    mark_refresh(group, True, f"Refresh ping OK para {group}")
    return {"ok": True, "version": "V352", "group": group, "message": "Refresh ping registrado"}
