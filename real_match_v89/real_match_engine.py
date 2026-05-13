
import os, time, hashlib
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

try:
    import requests
except Exception:
    requests = None

TZ = ZoneInfo(os.getenv("DISPLAY_TIMEZONE", "Europe/Madrid"))
CACHE = {"ts": 0, "payload": None}
CACHE_SECONDS = int(os.getenv("V89_REAL_MATCH_CACHE_SECONDS", "300"))
MAX_FUTURE_DAYS = int(os.getenv("V89_MAX_FUTURE_DAYS", "7"))
MAX_PAST_HOURS = int(os.getenv("V89_MAX_PAST_HOURS", "4"))
MIN_REAL_SCORE = int(os.getenv("V89_MIN_REAL_SCORE", "65"))

BLOCKED_TEAM_NAMES = {
    "team a","team b","home","away","local","visitante","demo","test","example",
    "equipo local","equipo visitante","liverpool","chelsea","rayo vallecano",
    "girona","tondela","moreirense fc"
}
BLOCKED_LEAGUES = {"demo league","test league","mock league","example league"}

def now_local():
    return datetime.now(TZ)

def env_first(*names):
    for n in names:
        v = os.getenv(n)
        if v:
            return v
    return None

def parse_dt(value):
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        raw = str(value).strip()
        try:
            if raw.endswith("Z"):
                raw = raw[:-1] + "+00:00"
            dt = datetime.fromisoformat(raw)
        except Exception:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(TZ)

def fmt_time(dt):
    if not dt:
        return {"date":"SIN FECHA","time":"--:--","status":"SIN HORARIO","relative":"Sin horario","iso":None}
    now = now_local()
    dias = ["LUN","MAR","MIÉ","JUE","VIE","SÁB","DOM"]
    meses = ["ENE","FEB","MAR","ABR","MAY","JUN","JUL","AGO","SEP","OCT","NOV","DIC"]
    if dt.date() == now.date():
        date_label = "HOY"
    elif dt.date() == (now + timedelta(days=1)).date():
        date_label = "MAÑANA"
    else:
        date_label = f"{dias[dt.weekday()]} {dt.day} {meses[dt.month-1]}"
    minutes = int((dt-now).total_seconds()//60)
    if -130 <= minutes <= 130:
        status, rel = "EN DIRECTO", "En juego / cerca"
    elif minutes > 0:
        status = "PROGRAMADO"
        rel = f"Empieza en {minutes} min" if minutes < 60 else (f"Empieza en {minutes//60} h" if minutes < 1440 else f"Empieza en {minutes//1440} días")
    else:
        status, rel = "RECIENTE", "Reciente"
    return {"date":date_label,"date_full":dt.strftime("%d/%m/%Y"),"time":dt.strftime("%H:%M"),"status":status,"relative":rel,"iso":dt.isoformat()}

def norm(name):
    return " ".join(str(name or "").strip().split())

def is_blocked_team(name):
    c = norm(name).lower()
    return (not c) or c in BLOCKED_TEAM_NAMES or c.startswith("team ") or c.endswith(" demo")

def sid(*parts):
    return hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()[:16]

def build_match(event, sport_key=None):
    home = norm(event.get("home_team"))
    away = norm(event.get("away_team"))
    league = event.get("sport_title") or sport_key or "Competición"
    commence = event.get("commence_time")
    dt = parse_dt(commence)
    t = fmt_time(dt)
    odds = None
    market = "Ganador del partido"
    for book in event.get("bookmakers") or []:
        for m in book.get("markets") or []:
            if m.get("key") == "h2h":
                outcomes = m.get("outcomes") or []
                try:
                    outcomes = sorted(outcomes, key=lambda x: float(x.get("price", 999)))
                    if outcomes:
                        odds = outcomes[0].get("price")
                        market = f"Gana {outcomes[0].get('name')}"
                except Exception:
                    pass
                break
        if odds:
            break
    match = {"id":event.get("id") or sid(home, away, commence, league), "source":"the_odds_api",
             "league":league, "home_team":home, "away_team":away, "commence_time":commence,
             "date":t["date"], "date_full":t.get("date_full",""), "time":t["time"],
             "status":t["status"], "relative":t["relative"], "iso":t["iso"],
             "market":market, "odds":odds, "real":True}
    val = validate_match(match)
    match.update({"valid":val["valid"],"quality_score":val["score"],"reasons":val["reasons"]})
    return match

def validate_match(m):
    reasons, score = [], 100
    home, away, league = norm(m.get("home_team")), norm(m.get("away_team")), norm(m.get("league"))
    if not home or not away:
        score -= 40; reasons.append("faltan equipos")
    if home.lower() == away.lower() and home:
        score -= 40; reasons.append("equipos duplicados")
    if is_blocked_team(home) or is_blocked_team(away):
        score -= 60; reasons.append("equipo demo/bloqueado")
    if league.lower() in BLOCKED_LEAGUES:
        score -= 50; reasons.append("liga demo/bloqueada")
    dt = parse_dt(m.get("commence_time") or m.get("iso"))
    now = now_local()
    if not dt:
        score -= 50; reasons.append("sin fecha real")
    else:
        if dt < now - timedelta(hours=MAX_PAST_HOURS):
            score -= 45; reasons.append("partido viejo")
        if dt > now + timedelta(days=MAX_FUTURE_DAYS):
            score -= 35; reasons.append("partido demasiado futuro")
        if dt.year > now.year + 1:
            score -= 60; reasons.append("año sospechoso")
    score = max(0, min(100, score))
    return {"valid": score >= MIN_REAL_SCORE, "score": score, "reasons": reasons or ["OK"]}

def dedupe(matches):
    seen, out = set(), []
    for m in matches:
        key = (norm(m.get("home_team")).lower(), norm(m.get("away_team")).lower(), str(m.get("commence_time") or m.get("iso")))
        if key in seen:
            continue
        seen.add(key); out.append(m)
    return out

def buckets(matches):
    b = {"live": [], "today": [], "upcoming": []}
    today = now_local().date()
    for m in matches:
        dt = parse_dt(m.get("commence_time") or m.get("iso"))
        if m.get("status") == "EN DIRECTO":
            b["live"].append(m)
        elif dt and dt.date() == today:
            b["today"].append(m)
        else:
            b["upcoming"].append(m)
    return b

def fetch_the_odds_api():
    if requests is None:
        return {"ok":False,"error":"requests no disponible","matches":[]}
    api_key = env_first("THE_ODDS_API_KEY","ODDS_API_KEY")
    if not api_key:
        return {"ok":False,"error":"Falta ODDS_API_KEY / THE_ODDS_API_KEY","matches":[]}
    sports = [s.strip() for s in os.getenv("V89_ODDS_SPORTS","soccer_epl,soccer_spain_la_liga,soccer_italy_serie_a,soccer_germany_bundesliga,soccer_uefa_champs_league").split(",") if s.strip()]
    regions = os.getenv("ODDS_REGIONS","eu")
    markets = os.getenv("ODDS_MARKETS","h2h")
    timeout = int(os.getenv("HTTP_TIMEOUT_SECONDS","8"))
    matches, errors = [], []
    for sport in sports:
        try:
            r = requests.get(f"https://api.the-odds-api.com/v4/sports/{sport}/odds",
                             params={"apiKey":api_key,"regions":regions,"markets":markets,"oddsFormat":"decimal"},
                             timeout=timeout)
            if r.status_code != 200:
                errors.append(f"{sport}: HTTP {r.status_code}")
                continue
            data = r.json()
            if not isinstance(data, list):
                errors.append(f"{sport}: respuesta inválida")
                continue
            for event in data:
                m = build_match(event, sport)
                if m["valid"]:
                    matches.append(m)
        except Exception as e:
            errors.append(f"{sport}: {e}")
    matches = dedupe(matches)
    matches.sort(key=lambda x: x.get("iso") or "")
    return {"ok":bool(matches),"error":"; ".join(errors) if errors else None,"matches":matches}

def get_real_feed(force=False):
    now_ts = time.time()
    if not force and CACHE["payload"] and now_ts - CACHE["ts"] < CACHE_SECONDS:
        return CACHE["payload"]
    fetched = fetch_the_odds_api()
    if not fetched["ok"]:
        payload = {"ok":False,"source":"none","message":"No hay partidos reales disponibles ahora mismo. No se muestran demos.",
                   "error":fetched.get("error"),"matches":[],"buckets":{"live":[],"today":[],"upcoming":[]},
                   "counts":{"total":0,"live":0,"today":0,"upcoming":0},"generated_at":datetime.utcnow().isoformat()}
    else:
        b = buckets(fetched["matches"])
        payload = {"ok":True,"source":"the_odds_api","message":"Partidos reales cargados","error":fetched.get("error"),
                   "matches":fetched["matches"],"buckets":b,
                   "counts":{"total":len(fetched["matches"]),"live":len(b["live"]),"today":len(b["today"]),"upcoming":len(b["upcoming"])},
                   "generated_at":datetime.utcnow().isoformat()}
    CACHE["ts"], CACHE["payload"] = now_ts, payload
    return payload

def get_v89_status():
    feed = get_real_feed(False)
    return {"version":"V89","status":"REAL MATCH ENGINE ACTIVO","strict_real_only":True,
            "max_future_days":MAX_FUTURE_DAYS,"max_past_hours":MAX_PAST_HOURS,"cache_seconds":CACHE_SECONDS,
            "feed":feed,"modules":["Solo partidos reales","Sin demos/fallbacks inventados","Bloqueo de partidos viejos",
            "Bloqueo años sospechosos","Anti duplicados","LIVE / HOY / PRÓXIMOS","Hora limpia","The Odds API real feed"]}
