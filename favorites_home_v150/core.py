
import os, sqlite3, json
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

def now():
    return datetime.utcnow().isoformat() + "Z"

def ensure_schema():
    con = connect()
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS favorites_v149 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT DEFAULT 'default',
        fav_type TEXT NOT NULL,
        fav_key TEXT NOT NULL,
        label TEXT NOT NULL,
        meta_json TEXT,
        created_at TEXT,
        UNIQUE(user_id, fav_type, fav_key)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS home_feed_v150 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        feed_type TEXT NOT NULL,
        title TEXT NOT NULL,
        text TEXT,
        href TEXT,
        priority INTEGER DEFAULT 0,
        source TEXT DEFAULT 'real_core',
        meta_json TEXT,
        created_at TEXT
    )
    """)
    con.commit()
    con.close()

def add_favorite(data):
    ensure_schema()
    user_id = data.get("user_id") or "default"
    fav_type = data.get("type") or data.get("fav_type") or "team"
    fav_key = data.get("key") or data.get("fav_key") or data.get("label")
    label = data.get("label") or fav_key
    if not fav_key or not label:
        return {"ok": False, "error": "Falta key/label"}
    con = connect()
    con.execute("""
    INSERT INTO favorites_v149(user_id,fav_type,fav_key,label,meta_json,created_at)
    VALUES(?,?,?,?,?,?)
    ON CONFLICT(user_id,fav_type,fav_key) DO UPDATE SET label=excluded.label, meta_json=excluded.meta_json
    """, (user_id, fav_type, fav_key, label, json.dumps(data.get("meta") or {}, ensure_ascii=False), now()))
    con.commit()
    con.close()
    return {"ok": True, "favorite": {"user_id": user_id, "type": fav_type, "key": fav_key, "label": label}}

def remove_favorite(user_id="default", fav_type=None, fav_key=None):
    ensure_schema()
    con = connect()
    if fav_type and fav_key:
        con.execute("DELETE FROM favorites_v149 WHERE user_id=? AND fav_type=? AND fav_key=?", (user_id, fav_type, fav_key))
    else:
        con.execute("DELETE FROM favorites_v149 WHERE user_id=?", (user_id,))
    con.commit()
    con.close()
    return {"ok": True}

def list_favorites(user_id="default"):
    ensure_schema()
    con = connect()
    rows = [dict(r) for r in con.execute("SELECT * FROM favorites_v149 WHERE user_id=? ORDER BY id DESC", (user_id,))]
    con.close()
    for r in rows:
        try:
            r["meta"] = json.loads(r.get("meta_json") or "{}")
        except Exception:
            r["meta"] = {}
    return rows

def read_real_fixtures(limit=80):
    ensure_schema()
    con = connect()
    try:
        rows = [dict(r) for r in con.execute("SELECT * FROM real_fixtures_v146 ORDER BY kickoff ASC, id DESC LIMIT ?", (int(limit),))]
    except Exception:
        rows = []
    con.close()
    return rows

def add_feed_item(data):
    ensure_schema()
    title = data.get("title")
    if not title:
        return {"ok": False, "error": "Falta title"}
    con = connect()
    con.execute("""
    INSERT INTO home_feed_v150(feed_type,title,text,href,priority,source,meta_json,created_at)
    VALUES(?,?,?,?,?,?,?,?)
    """, (
        data.get("type") or data.get("feed_type") or "info",
        title,
        data.get("text") or "",
        data.get("href") or "",
        int(data.get("priority") or 0),
        data.get("source") or "real_core",
        json.dumps(data.get("meta") or {}, ensure_ascii=False),
        now()
    ))
    con.commit()
    con.close()
    return {"ok": True}

def list_feed(limit=50):
    ensure_schema()
    con = connect()
    rows = [dict(r) for r in con.execute("SELECT * FROM home_feed_v150 ORDER BY priority DESC, id DESC LIMIT ?", (int(limit),))]
    con.close()
    return rows

def build_home_live(user_id="default"):
    favorites = list_favorites(user_id)
    fixtures = read_real_fixtures()
    feed = list_feed()

    fav_labels = {f["label"].lower() for f in favorites}
    fav_matches = []
    for fx in fixtures:
        home = str(fx.get("home_team") or "").lower()
        away = str(fx.get("away_team") or "").lower()
        league = str(fx.get("league") or "").lower()
        if home in fav_labels or away in fav_labels or league in fav_labels:
            fav_matches.append(fx)

    live = [f for f in fixtures if str(f.get("status") or "").lower() in ["live","inplay","in_play","1h","2h","ht"]]
    upcoming = [f for f in fixtures if str(f.get("status") or "").lower() in ["upcoming","scheduled","not_started","pre"]][:10]

    return {
        "version": "V150_HOME_LIVE_FEED_REAL",
        "generated_at": now(),
        "favorites": favorites,
        "favorite_matches": fav_matches,
        "live_matches": live,
        "upcoming_matches": upcoming,
        "feed": feed,
        "empty_state": not bool(favorites or fixtures or feed),
        "policy": {
            "no_fake_matches": True,
            "no_fake_feed": True,
            "real_core_first": True
        }
    }

def status():
    return {
        "version": "V149_V150_FAVORITES_HOME_LIVE_FEED",
        "favorites": len(list_favorites()),
        "fixtures": len(read_real_fixtures()),
        "feed": len(list_feed()),
        "db_path": db_path(),
        "policy": {"no_fake_data": True}
    }
