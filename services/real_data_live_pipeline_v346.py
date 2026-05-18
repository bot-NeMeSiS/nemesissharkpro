
import os, sqlite3, time
from pathlib import Path

DB_PATH = os.getenv("DATABASE_PATH") or os.getenv("DB_PATH") or "/data/database.db"

API_KEYS = {
    "THE_ODDS_API_KEY": ["THE_ODDS_API_KEY", "ODDS_API_KEY"],
    "TELEGRAM_BOT_TOKEN": ["TELEGRAM_BOT_TOKEN", "TELEGRAM_TOKEN", "BOT_TOKEN"],
    "PUBLIC_BASE_URL": ["PUBLIC_BASE_URL", "RENDER_EXTERNAL_URL", "BASE_URL"],
    "OPENAI_API_KEY": ["OPENAI_API_KEY"],
}

LIVE_FIELD_CONTRACT = {
    "score": ["home_score", "away_score", "score", "home_goals", "away_goals"],
    "minute": ["minute", "elapsed", "time", "match_minute", "status_minute"],
    "crest": ["home_logo", "away_logo", "home_crest", "away_crest", "badge", "logo", "team_logo"],
    "odds_1x2": ["odd_1", "odd_x", "odd_2", "home_odd", "draw_odd", "away_odd", "cuota_1", "cuota_x", "cuota_2"],
}

def _env_present(names):
    for name in names:
        value = os.getenv(name)
        if value:
            return {"present": True, "env_name": name, "length": len(value)}
    return {"present": False, "env_name": None, "length": 0}

def _connect():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def ensure_cache_tables():
    con = _connect()
    cur = con.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS real_data_cache_v346 (
      cache_key TEXT PRIMARY KEY,
      cache_group TEXT NOT NULL,
      payload TEXT,
      source TEXT,
      status TEXT DEFAULT 'ready',
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
      ttl_seconds INTEGER DEFAULT 900
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS real_data_health_events_v346 (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      event_type TEXT,
      severity TEXT DEFAULT 'info',
      message TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    con.commit()
    con.close()

def db_tables():
    try:
        con = _connect()
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r["name"] for r in cur.fetchall()]
        con.close()
        return tables
    except Exception:
        return []

def inspect_possible_data_tables():
    tables = db_tables()
    keywords = ["match", "fixture", "event", "odds", "partido", "live", "cache"]
    possible = [t for t in tables if any(k in t.lower() for k in keywords)]
    return possible[:80]

def cache_summary():
    ensure_cache_tables()
    try:
        con = _connect()
        cur = con.cursor()
        cur.execute("SELECT cache_group, COUNT(*) AS n FROM real_data_cache_v346 GROUP BY cache_group")
        rows = [dict(r) for r in cur.fetchall()]
        con.close()
        return {"ok": True, "groups": rows}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "groups": []}

def api_key_status():
    return {public_name: _env_present(names) for public_name, names in API_KEYS.items()}

def real_data_pipeline_status():
    ensure_cache_tables()
    tables = db_tables()
    possible = inspect_possible_data_tables()
    keys = api_key_status()
    missing_critical = []
    if not keys["THE_ODDS_API_KEY"]["present"]:
        missing_critical.append("THE_ODDS_API_KEY")
    return {
        "ok": True,
        "version": "V346",
        "name": "REAL_DATA_LIVE_API_PIPELINE_CONSOLIDATION_PRO",
        "real_only": True,
        "db": {
            "path": DB_PATH,
            "tables_count": len(tables),
            "possible_data_tables": possible,
        },
        "api_keys": keys,
        "missing_critical": missing_critical,
        "cache": cache_summary(),
        "live_contract": LIVE_FIELD_CONTRACT,
        "routes_to_check": [
            "/api/real-data/pipeline/status-v346",
            "/api/real-data/cache/status-v346",
            "/cliente/real-data-pipeline",
            "/cliente/1x2",
            "/cliente/live-command-center",
            "/api/client/1x2/recommendations-v319",
            "/api/stability/full-status-v321",
        ],
        "diagnosis": build_diagnosis(keys, possible),
    }

def build_diagnosis(keys, possible_tables):
    notes = []
    if not keys["THE_ODDS_API_KEY"]["present"]:
        notes.append("Falta THE_ODDS_API_KEY/ODDS_API_KEY: cuotas y 1X2 pueden no cargar desde API real.")
    if not possible_tables:
        notes.append("No se detectan tablas de partidos/cache/live en SQLite: puede faltar ingesta o caché inicial.")
    if not notes:
        notes.append("Base de datos y variables principales parecen preparadas. Si no salen partidos, revisar respuesta de proveedor/API.")
    return notes
