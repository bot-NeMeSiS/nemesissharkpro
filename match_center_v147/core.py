
import os, json, sqlite3
from pathlib import Path
from datetime import datetime

def db_path():
    return os.environ.get("DATABASE_PATH") or os.environ.get("DB_PATH") or "/data/app.db"

def connect():
    path = db_path()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con

def ensure_schema():
    con = connect()
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS match_center_events_v147(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fixture_id INTEGER,
        event_minute TEXT,
        event_type TEXT,
        team TEXT,
        text TEXT,
        raw_json TEXT,
        created_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS match_center_stats_v147(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fixture_id INTEGER,
        stat_key TEXT,
        home_value TEXT,
        away_value TEXT,
        created_at TEXT,
        UNIQUE(fixture_id, stat_key)
    )
    """)
    con.commit()
    con.close()

def now():
    return datetime.utcnow().isoformat() + "Z"

def get_fixture(fixture_id=None, external_id=None):
    con = connect()
    row = None
    try:
        if fixture_id:
            row = con.execute("SELECT * FROM real_fixtures_v146 WHERE id=?", (int(fixture_id),)).fetchone()
        elif external_id:
            row = con.execute("SELECT * FROM real_fixtures_v146 WHERE external_id=? ORDER BY id DESC LIMIT 1", (external_id,)).fetchone()
    except Exception:
        row = None
    con.close()
    return dict(row) if row else None

def events(fixture_id):
    ensure_schema()
    con = connect()
    rows = [dict(r) for r in con.execute("SELECT * FROM match_center_events_v147 WHERE fixture_id=? ORDER BY id ASC", (int(fixture_id),))]
    con.close()
    return rows

def stats(fixture_id):
    ensure_schema()
    con = connect()
    rows = [dict(r) for r in con.execute("SELECT * FROM match_center_stats_v147 WHERE fixture_id=? ORDER BY id ASC", (int(fixture_id),))]
    con.close()
    return rows

def add_events(fixture_id, items):
    ensure_schema()
    con = connect()
    saved = 0
    for e in items or []:
        con.execute("INSERT INTO match_center_events_v147(fixture_id,event_minute,event_type,team,text,raw_json,created_at) VALUES(?,?,?,?,?,?,?)",
            (int(fixture_id), e.get("minute") or "", e.get("type") or "INFO", e.get("team") or "", e.get("text") or "", json.dumps(e, ensure_ascii=False), now()))
        saved += 1
    con.commit()
    con.close()
    return {"ok": True, "saved": saved}

def upsert_stats(fixture_id, items):
    ensure_schema()
    con = connect()
    saved = 0
    for s in items or []:
        key = s.get("key") or s.get("name") or s.get("stat_key")
        if not key:
            continue
        con.execute("""
        INSERT INTO match_center_stats_v147(fixture_id,stat_key,home_value,away_value,created_at)
        VALUES(?,?,?,?,?)
        ON CONFLICT(fixture_id,stat_key) DO UPDATE SET home_value=excluded.home_value, away_value=excluded.away_value, created_at=excluded.created_at
        """, (int(fixture_id), key, str(s.get("home") or ""), str(s.get("away") or ""), now()))
        saved += 1
    con.commit()
    con.close()
    return {"ok": True, "saved": saved}

def build_center(fixture_id=None, external_id=None):
    ensure_schema()
    fx = get_fixture(fixture_id, external_id)
    if not fx:
        return {"version":"V147_REAL_MATCH_CENTER_CONNECTOR","empty_state":True,"message":"Partido real no encontrado en V146.","fixture":None,"events":[],"stats":[],"shark_reading":"Sin fixture real no se inventa análisis.","policy":{"no_fake_data":True}}
    ev = events(fx["id"])
    st = stats(fx["id"])
    fx["score"] = "N/A" if fx.get("score_home") is None or fx.get("score_away") is None else f"{fx.get('score_home')}-{fx.get('score_away')}"
    reading = f"{fx.get('home_team')} vs {fx.get('away_team')}: fixture real cargado. Eventos: {len(ev)}. Stats: {len(st)}. Sin datos extra no se inventa timeline."
    return {"version":"V147_REAL_MATCH_CENTER_CONNECTOR","empty_state":False,"fixture":fx,"events":ev,"stats":st,"shark_reading":reading,"policy":{"no_fake_data":True}}
