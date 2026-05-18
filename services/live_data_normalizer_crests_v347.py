
import os, sqlite3, json, re
from pathlib import Path

DB_PATH = os.getenv("DATABASE_PATH") or os.getenv("DB_PATH") or "/data/database.db"

TEAM_ALIASES = {
    "man utd": "Manchester United",
    "man united": "Manchester United",
    "man city": "Manchester City",
    "psg": "Paris Saint-Germain",
    "atleti": "Atlético Madrid",
    "inter": "Inter Milan",
}

def _connect():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def _clean_team(name):
    if not name:
        return "Equipo"
    s = str(name).strip()
    s = re.sub(r"\s+", " ", s)
    key = s.lower()
    return TEAM_ALIASES.get(key, s)

def _first(row, keys, default=None):
    for key in keys:
        try:
            if isinstance(row, dict) and row.get(key) not in [None, ""]:
                return row.get(key)
            if hasattr(row, "keys") and key in row.keys() and row[key] not in [None, ""]:
                return row[key]
        except Exception:
            pass
    return default

def crest_fallback(team):
    team = _clean_team(team)
    initials = "".join([p[:1].upper() for p in team.split()[:2]]) or "FC"
    return {
        "url": None,
        "initials": initials,
        "fallback": True,
        "label": team
    }

def normalize_match(raw):
    home = _clean_team(_first(raw, ["home_team","home","local_team","team_home","home_name","homeTeam"], "Local"))
    away = _clean_team(_first(raw, ["away_team","away","visitor_team","team_away","away_name","awayTeam"], "Visitante"))

    home_score = _first(raw, ["home_score","home_goals","score_home","homeScore"], None)
    away_score = _first(raw, ["away_score","away_goals","score_away","awayScore"], None)
    minute = _first(raw, ["minute","elapsed","time","match_minute","status_minute"], None)
    status = _first(raw, ["status","state","match_status","live_status"], "scheduled")
    league = _first(raw, ["league","competition","sport_key","liga","tournament"], "")

    home_logo = _first(raw, ["home_logo","home_crest","home_badge","home_image","home_team_logo"], None)
    away_logo = _first(raw, ["away_logo","away_crest","away_badge","away_image","away_team_logo"], None)

    score_text = "vs"
    if home_score is not None and away_score is not None:
        score_text = f"{home_score}-{away_score}"

    minute_text = "Pre"
    if minute not in [None, ""]:
        minute_text = str(minute)
        if minute_text.isdigit():
            minute_text = minute_text + "'"

    return {
        "id": str(_first(raw, ["id","match_id","event_id","fixture_id"], f"{home}-{away}")),
        "home": home,
        "away": away,
        "league": league,
        "status": status,
        "score": {"home": home_score, "away": away_score, "text": score_text},
        "minute": {"raw": minute, "text": minute_text},
        "crests": {
            "home": {"url": home_logo, **crest_fallback(home)} if not home_logo else {"url": home_logo, "fallback": False, "initials": crest_fallback(home)["initials"], "label": home},
            "away": {"url": away_logo, **crest_fallback(away)} if not away_logo else {"url": away_logo, "fallback": False, "initials": crest_fallback(away)["initials"], "label": away},
        },
        "odds_1x2": {
            "1": _first(raw, ["odd_1","home_odd","cuota_1","odds_home"], None),
            "X": _first(raw, ["odd_x","draw_odd","cuota_x","odds_draw"], None),
            "2": _first(raw, ["odd_2","away_odd","cuota_2","odds_away"], None),
        },
        "real_only": True,
    }

def discover_candidate_tables():
    try:
        con = _connect()
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r["name"] for r in cur.fetchall()]
        con.close()
        return [t for t in tables if any(k in t.lower() for k in ["match","fixture","event","partido","live","odds","cache"])]
    except Exception:
        return []

def sample_normalized_matches(limit=12):
    tables = discover_candidate_tables()
    out = []
    errors = []
    try:
        con = _connect()
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        for table in tables:
            if len(out) >= limit:
                break
            try:
                cur.execute(f"SELECT * FROM {table} LIMIT ?", (limit,))
                rows = cur.fetchall()
                for r in rows:
                    nm = normalize_match(r)
                    if nm["home"] != "Local" or nm["away"] != "Visitante":
                        nm["source_table"] = table
                        out.append(nm)
                    if len(out) >= limit:
                        break
            except Exception as exc:
                errors.append({"table": table, "error": str(exc)})
        con.close()
    except Exception as exc:
        errors.append({"table": "*", "error": str(exc)})
    return {"ok": True, "version": "V347", "count": len(out), "matches": out, "candidate_tables": tables[:60], "errors": errors[:10], "real_only": True}

def normalizer_status():
    data = sample_normalized_matches(limit=5)
    return {
        "ok": True,
        "version": "V347",
        "name": "LIVE_DATA_NORMALIZER_CRESTS_ENGINE_PRO",
        "db_path": DB_PATH,
        "candidate_tables_count": len(data.get("candidate_tables", [])),
        "sample_count": data.get("count", 0),
        "crest_fallback": True,
        "normalizes": ["teams", "score", "minute", "crests", "1x2 odds", "league", "status"],
        "routes": [
            "/api/live/normalizer/status-v347",
            "/api/live/normalizer/sample-v347",
            "/cliente/live-normalizer",
            "/cliente/live-command-center",
            "/cliente/match-center-premium"
        ],
        "real_only": True
    }
