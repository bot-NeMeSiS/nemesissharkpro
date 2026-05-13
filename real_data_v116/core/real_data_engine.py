
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

def _db_path():
    for value in [
        os.environ.get("DATABASE_PATH"),
        os.environ.get("DB_PATH"),
        "/data/app.db",
        "/data/database.db",
        "app.db",
        "database.db",
    ]:
        if value:
            return value
    return "app.db"

def _connect():
    path = _db_path()
    if "/" in path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con

def ensure_real_data_schema():
    con = _connect()
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS real_data_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL,
        data_type TEXT NOT NULL,
        cache_key TEXT NOT NULL,
        payload TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        expires_at TEXT,
        UNIQUE(source, data_type, cache_key)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS real_data_sync_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        data_type TEXT,
        status TEXT,
        message TEXT,
        created_at TEXT NOT NULL
    )
    """)
    con.commit()
    con.close()

def log_sync(source, data_type, status, message):
    ensure_real_data_schema()
    con = _connect()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO real_data_sync_log (source, data_type, status, message, created_at) VALUES (?, ?, ?, ?, ?)",
        (source, data_type, status, message, datetime.utcnow().isoformat() + "Z")
    )
    con.commit()
    con.close()

def save_cache(source, data_type, cache_key, payload, ttl_minutes=10):
    ensure_real_data_schema()
    now = datetime.utcnow()
    expires = now + timedelta(minutes=ttl_minutes)
    con = _connect()
    cur = con.cursor()
    cur.execute("""
    INSERT INTO real_data_cache (source, data_type, cache_key, payload, created_at, updated_at, expires_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(source, data_type, cache_key)
    DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at, expires_at=excluded.expires_at
    """, (
        source,
        data_type,
        cache_key,
        json_dumps(payload),
        now.isoformat() + "Z",
        now.isoformat() + "Z",
        expires.isoformat() + "Z",
    ))
    con.commit()
    con.close()

def load_cache(source=None, data_type=None, cache_key=None, only_valid=False):
    ensure_real_data_schema()
    con = _connect()
    cur = con.cursor()

    where = []
    params = []
    if source:
        where.append("source=?")
        params.append(source)
    if data_type:
        where.append("data_type=?")
        params.append(data_type)
    if cache_key:
        where.append("cache_key=?")
        params.append(cache_key)

    sql = "SELECT * FROM real_data_cache"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY updated_at DESC LIMIT 100"

    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    con.close()

    now = datetime.utcnow()
    out = []
    for r in rows:
        expired = False
        if r.get("expires_at"):
            try:
                expired = datetime.fromisoformat(r["expires_at"].replace("Z", "")) < now
            except Exception:
                expired = False
        if only_valid and expired:
            continue
        r["expired"] = expired
        r["payload_json"] = json_loads(r.get("payload"))
        out.append(r)
    return out

def json_dumps(payload):
    import json
    return json.dumps(payload, ensure_ascii=False, default=str)

def json_loads(text):
    import json
    try:
        return json.loads(text or "{}")
    except Exception:
        return {}

def read_existing_real_tables():
    """
    Reads existing app tables if present.
    Does not create fake matches/picks.
    """
    con = _connect()
    cur = con.cursor()
    tables = ["matches", "partidos", "fixtures", "events", "picks", "managed_picks"]
    found = {}

    for table in tables:
        try:
            cur.execute(f"SELECT * FROM {table} ORDER BY 1 DESC LIMIT 30")
            found[table] = [dict(r) for r in cur.fetchall()]
        except Exception:
            continue

    con.close()
    return found

def build_real_data_status():
    ensure_real_data_schema()
    tables = read_existing_real_tables()
    cache = load_cache()
    valid_cache = load_cache(only_valid=True)

    sources = {
        "the_odds_api": bool(os.environ.get("THE_ODDS_API_KEY")),
        "telegram": bool(os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID")),
        "database": bool(_db_path()),
    }

    warnings = []
    if not sources["the_odds_api"]:
        warnings.append("THE_ODDS_API_KEY no configurada. No se debe mostrar contenido inventado.")
    if not tables:
        warnings.append("No se detectaron tablas reales comunes de partidos/picks todavía.")
    if not valid_cache:
        warnings.append("No hay cache real válido activo. Las pantallas deben mostrar estado vacío premium.")

    return {
        "version": "V116_REAL_DATA_SYNCHRONIZATION",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "db_path": _db_path(),
        "sources": sources,
        "real_tables_detected": list(tables.keys()),
        "real_tables_counts": {k: len(v) for k, v in tables.items()},
        "cache_items": len(cache),
        "valid_cache_items": len(valid_cache),
        "warnings": warnings,
        "policy": {
            "no_fake_matches": True,
            "no_fake_picks": True,
            "no_demo_for_clients": True,
            "empty_state_when_no_real_data": True,
            "real_core_first": True,
        }
    }

def build_client_real_feed():
    """
    Returns real data only: existing DB rows and valid cache.
    Never returns fabricated matches.
    """
    tables = read_existing_real_tables()
    cache = load_cache(only_valid=True)
    return {
        "version": "V116_REAL_CLIENT_FEED",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "has_real_data": bool(tables or cache),
        "tables": tables,
        "cache": cache,
        "empty_state": not bool(tables or cache),
        "message": "Sin datos reales activos ahora mismo." if not bool(tables or cache) else "Datos reales disponibles."
    }

def latest_sync_logs(limit=30):
    ensure_real_data_schema()
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT * FROM real_data_sync_log ORDER BY id DESC LIMIT ?", (int(limit),))
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows
