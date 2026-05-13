
import os, json, sqlite3
from pathlib import Path
from datetime import datetime, date

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
    CREATE TABLE IF NOT EXISTS real_fixtures_v146 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        external_id TEXT,
        source TEXT DEFAULT 'real_core',
        sport TEXT DEFAULT 'football',
        league TEXT,
        home_team TEXT NOT NULL,
        away_team TEXT NOT NULL,
        kickoff TEXT,
        status TEXT DEFAULT 'upcoming',
        minute TEXT,
        score_home INTEGER,
        score_away INTEGER,
        raw_json TEXT,
        updated_at TEXT,
        UNIQUE(source, external_id)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS fixture_sync_log_v146 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        status TEXT,
        message TEXT,
        created_at TEXT
    )
    """)
    con.commit()
    con.close()

def now():
    return datetime.utcnow().isoformat() + "Z"

def log(source, status, msg):
    ensure_schema()
    con = connect()
    con.execute("INSERT INTO fixture_sync_log_v146(source,status,message,created_at) VALUES(?,?,?,?)", (source,status,msg,now()))
    con.commit()
    con.close()

def normalize(item, source):
    home = item.get("home_team") or item.get("home") or item.get("team_home")
    away = item.get("away_team") or item.get("away") or item.get("team_away")
    if not home or not away:
        raise ValueError("Fixture sin equipos reales")
    ext = item.get("id") or item.get("external_id") or item.get("match_id") or f"{home}-{away}-{item.get('kickoff','')}"
    return {
        "external_id": str(ext),
        "source": source,
        "sport": item.get("sport") or "football",
        "league": item.get("league") or item.get("competition") or "",
        "home_team": home,
        "away_team": away,
        "kickoff": item.get("kickoff") or item.get("commence_time") or item.get("date") or "",
        "status": str(item.get("status") or "upcoming").lower(),
        "minute": item.get("minute") or "",
        "score_home": item.get("score_home") if item.get("score_home") is not None else item.get("home_score"),
        "score_away": item.get("score_away") if item.get("score_away") is not None else item.get("away_score"),
        "raw_json": json.dumps(item, ensure_ascii=False, default=str),
    }

def sync_fixtures(fixtures, source="real_core"):
    ensure_schema()
    saved, skipped, errors = 0, 0, []
    con = connect()
    cur = con.cursor()
    for item in fixtures or []:
        try:
            f = normalize(item, source)
            cur.execute("""
            INSERT INTO real_fixtures_v146(external_id,source,sport,league,home_team,away_team,kickoff,status,minute,score_home,score_away,raw_json,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(source, external_id) DO UPDATE SET
              sport=excluded.sport, league=excluded.league, home_team=excluded.home_team, away_team=excluded.away_team,
              kickoff=excluded.kickoff, status=excluded.status, minute=excluded.minute,
              score_home=excluded.score_home, score_away=excluded.score_away, raw_json=excluded.raw_json, updated_at=excluded.updated_at
            """, (f["external_id"],f["source"],f["sport"],f["league"],f["home_team"],f["away_team"],f["kickoff"],f["status"],f["minute"],f["score_home"],f["score_away"],f["raw_json"],now()))
            saved += 1
        except Exception as e:
            skipped += 1
            errors.append(str(e))
    con.commit()
    con.close()
    log(source, "OK" if not errors else "PARTIAL", f"Guardados {saved}, saltados {skipped}")
    return {"ok": True, "saved": saved, "skipped": skipped, "errors": errors[:10]}

def parse_day(kickoff):
    if not kickoff:
        return None
    try:
        return datetime.fromisoformat(str(kickoff).replace("Z","+00:00")).date()
    except Exception:
        try:
            return datetime.strptime(str(kickoff)[:10], "%Y-%m-%d").date()
        except Exception:
            return None


def rows_from_picks(limit=250):
    """Fallback REAL ONLY: lee partidos reales ya guardados en la tabla principal picks.
    No crea partidos, no inventa cuotas y solo muestra registros con origen/ID externo real.
    """
    ensure_schema()
    con = connect()
    try:
        cur = con.cursor()
        cur.execute("""
            SELECT id, sport, league, title, pick, kickoff_time, live_status, live_minute,
                   live_score, odds_decimal, odds_bookmaker, external_event_id, source, created_at
            FROM picks
            WHERE COALESCE(active,1)=1
              AND (
                COALESCE(external_event_id,'') <> ''
                OR LOWER(COALESCE(source,'')) LIKE '%odds%'
                OR LOWER(COALESCE(source,'')) LIKE '%api%'
                OR COALESCE(odds_decimal,'') <> ''
              )
            ORDER BY COALESCE(kickoff_time, created_at) ASC, id DESC
            LIMIT ?
        """, (int(limit),))
        rows = [dict(r) for r in cur.fetchall()]
    except Exception:
        rows = []
    finally:
        con.close()

    out = []
    for r in rows:
        title = (r.get('title') or '').strip()
        home, away = '', ''
        for sep in [' vs ', ' VS ', ' v ', ' - ', '–']:
            if sep in title:
                parts = title.split(sep, 1)
                home, away = parts[0].strip(), parts[1].strip()
                break
        if not home or not away:
            # Mantiene REAL ONLY: si no se pueden separar equipos, se muestra como partido real genérico sin inventar rival.
            home = title or 'Partido real'
            away = ''
        score_home, score_away = None, None
        live_score = str(r.get('live_score') or '').strip()
        if '-' in live_score:
            try:
                a,b = live_score.split('-',1)
                score_home, score_away = int(a.strip()), int(b.strip())
            except Exception:
                pass
        st = str(r.get('live_status') or 'upcoming').lower()
        out.append({
            'id': 'pick_' + str(r.get('id')),
            'external_id': str(r.get('external_event_id') or r.get('id') or ''),
            'source': r.get('source') or 'picks_real_core',
            'sport': r.get('sport') or 'football',
            'league': r.get('league') or '',
            'home_team': home,
            'away_team': away,
            'kickoff': r.get('kickoff_time') or r.get('created_at') or '',
            'status': st,
            'minute': r.get('live_minute') or '',
            'score_home': score_home,
            'score_away': score_away,
            'raw_json': '',
            'updated_at': r.get('created_at') or '',
            'pick': r.get('pick') or '',
            'odds_decimal': r.get('odds_decimal') or '',
            'odds_bookmaker': r.get('odds_bookmaker') or '',
            '_from_picks': True,
        })
    return out

def _filter_fixture_rows(rows, filter_name="today"):
    today = date.today()
    out = []
    seen = set()
    for r in rows:
        st = str(r.get("status") or "").lower()
        d = parse_day(r.get("kickoff"))
        keep = filter_name == "all"
        if filter_name == "today": keep = d == today
        if filter_name == "live": keep = st in ["live","inplay","in_play","1h","2h","ht","en vivo","en directo"]
        if filter_name == "upcoming": keep = st in ["upcoming","scheduled","not_started","pre", ""] or (d and d >= today)
        if filter_name == "finished": keep = st in ["finished","ft","ended","closed","finalizado"]
        if keep:
            key = (str(r.get("external_id") or ""), str(r.get("home_team") or "").lower(), str(r.get("away_team") or "").lower(), str(r.get("kickoff") or "")[:16])
            if key in seen:
                continue
            seen.add(key)
            r["score"] = "N/A" if r.get("score_home") is None or r.get("score_away") is None else f"{r.get('score_home')}-{r.get('score_away')}"
            out.append(r)
    return out

def list_fixtures(filter_name="today", limit=250):
    ensure_schema()
    con = connect()
    rows = [dict(r) for r in con.execute("SELECT * FROM real_fixtures_v146 ORDER BY kickoff ASC,id DESC LIMIT ?", (int(limit),))]
    con.close()
    # V206.1: une con picks/cuotas reales para evitar pantallas vacías cuando el conector V146 aún no ha sincronizado.
    rows.extend(rows_from_picks(limit))
    out = _filter_fixture_rows(rows, filter_name)
    # UX real: si 'hoy' está vacío, muestra próximos reales. No inventa nada, solo evita pantalla muerta.
    if filter_name == "today" and not out:
        out = _filter_fixture_rows(rows, "upcoming")[:int(limit)]
        for r in out:
            r["smart_fallback"] = True
    return out[:int(limit)]

def logs(limit=30):
    ensure_schema()
    con = connect()
    rows = [dict(r) for r in con.execute("SELECT * FROM fixture_sync_log_v146 ORDER BY id DESC LIMIT ?", (int(limit),))]
    con.close()
    return rows

def status():
    picks_fallback = len(rows_from_picks(500))
    return {
        "version": "V206_1_REAL_FIXTURES_RECOVERY_PRO",
        "db_path": db_path(),
        "total": len(list_fixtures("all")),
        "today": len(list_fixtures("today")),
        "live": len(list_fixtures("live")),
        "upcoming": len(list_fixtures("upcoming")),
        "finished": len(list_fixtures("finished")),
        "picks_real_core": picks_fallback,
        "policy": {"no_fake_matches": True, "no_fake_scores": True, "real_core_first": True, "fallback_from_real_picks": True}
    }
