
"""
NeMeSiS SHARK PRO V91 — Real Core Engine

Regla principal:
- Toda pantalla pública debe leer de este núcleo.
- Datos reales o vacío seguro.
- Sin demo, sin seeds fake, sin fallback inventado.
"""

import os
import time
import hashlib
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

try:
    import requests
except Exception:
    requests = None


TZ = ZoneInfo(os.getenv("DISPLAY_TIMEZONE", "Europe/Madrid"))
CACHE_SECONDS = int(os.getenv("V91_CORE_CACHE_SECONDS", "300"))
MAX_FUTURE_DAYS = int(os.getenv("V91_MAX_FUTURE_DAYS", "7"))
MAX_PAST_HOURS = int(os.getenv("V91_MAX_PAST_HOURS", "4"))
MIN_REAL_SCORE = int(os.getenv("V91_MIN_REAL_SCORE", "70"))

_CORE_CACHE = {
    "ts": 0,
    "feed": None,
}

FAKE_TERMS = {
    "team a", "team b", "home", "away", "local", "visitante",
    "demo", "test", "mock", "example", "equipo local", "equipo visitante",
    "liverpool", "chelsea", "elche cf", "alavés", "alaves", "napoli",
    "bologna", "rayo vallecano", "girona", "tondela", "moreirense",
    "cf estrela", "famalicão", "famalicao", "santa clara", "nacional",
    "augsburg", "borussia monchengladbach", "vfb stuttgart", "bayer leverkusen",
}

BLOCKED_DATE_TERMS = {
    "09/05/2026",
    "11/05/2026",
    "saturday 09/05/2026",
    "monday 11/05/2026",
    "h madrid",
}


def utc_now():
    return datetime.now(timezone.utc)


def local_now():
    return datetime.now(TZ)


def env_first(*names):
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return None


def clean_text(value):
    return " ".join(str(value or "").strip().split())


def parse_datetime(value):
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


def stable_id(*parts):
    raw = "|".join([str(p or "") for p in parts])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:18]


def date_payload(dt):
    if not dt:
        return {
            "date_label": "SIN FECHA",
            "date_full": "",
            "time": "--:--",
            "status": "SIN HORARIO",
            "relative": "Sin horario real",
            "iso": None,
        }

    now = local_now()
    dias = ["LUN", "MAR", "MIÉ", "JUE", "VIE", "SÁB", "DOM"]
    meses = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]

    if dt.date() == now.date():
        date_label = "HOY"
    elif dt.date() == (now + timedelta(days=1)).date():
        date_label = "MAÑANA"
    else:
        date_label = f"{dias[dt.weekday()]} {dt.day} {meses[dt.month - 1]}"

    minutes = int((dt - now).total_seconds() // 60)

    if -130 <= minutes <= 130:
        status = "EN DIRECTO"
        relative = "En juego / cerca"
    elif minutes > 0:
        status = "PROGRAMADO"
        if minutes < 60:
            relative = f"Empieza en {minutes} min"
        elif minutes < 1440:
            relative = f"Empieza en {minutes // 60} h"
        else:
            relative = f"Empieza en {minutes // 1440} días"
    else:
        status = "RECIENTE"
        relative = "Reciente"

    return {
        "date_label": date_label,
        "date_full": dt.strftime("%d/%m/%Y"),
        "time": dt.strftime("%H:%M"),
        "status": status,
        "relative": relative,
        "iso": dt.isoformat(),
    }


def league_name(raw):
    mapping = {
        "soccer_epl": "Premier League",
        "soccer_spain_la_liga": "LaLiga",
        "soccer_italy_serie_a": "Serie A",
        "soccer_germany_bundesliga": "Bundesliga",
        "soccer_france_ligue_one": "Ligue 1",
        "soccer_portugal_primeira_liga": "Primeira Liga",
        "soccer_uefa_champs_league": "Champions League",
        "soccer_uefa_europa_league": "Europa League",
    }
    if not raw:
        return "Competición"
    return mapping.get(str(raw), str(raw).replace("_", " ").title())


def normalize_market(event):
    market = "Ganador del partido"
    odds = None
    selection = None
    bookmaker = None

    for book in event.get("bookmakers") or []:
        bookmaker = book.get("title") or book.get("key")
        for m in book.get("markets") or []:
            key = m.get("key")
            if key == "h2h":
                outcomes = m.get("outcomes") or []
                try:
                    outcomes = sorted(outcomes, key=lambda x: float(x.get("price", 999)))
                    if outcomes:
                        selection = outcomes[0].get("name")
                        odds = outcomes[0].get("price")
                        market = f"Gana {selection}"
                        return market, odds, selection, bookmaker
                except Exception:
                    pass
    return market, odds, selection, bookmaker


def build_real_match(event, sport_key):
    home = clean_text(event.get("home_team"))
    away = clean_text(event.get("away_team"))
    commence_time = event.get("commence_time")
    dt = parse_datetime(commence_time)
    time_info = date_payload(dt)
    market, odds, selection, bookmaker = normalize_market(event)
    league = clean_text(event.get("sport_title")) or league_name(sport_key)

    match = {
        "id": event.get("id") or stable_id(home, away, commence_time, league),
        "source": "the_odds_api",
        "provider": "The Odds API",
        "sport_key": sport_key,
        "league": league,
        "home_team": home,
        "away_team": away,
        "commence_time": commence_time,
        "iso": time_info["iso"],
        "date": time_info["date_label"],
        "date_full": time_info["date_full"],
        "time": time_info["time"],
        "status": time_info["status"],
        "relative": time_info["relative"],
        "market": market,
        "selection": selection,
        "odds": odds,
        "bookmaker": bookmaker,
        "real": True,
        "shark_score": None,
        "risk": "Pendiente",
        "ev": None,
        "stake": "Pendiente",
    }

    validation = validate_match(match)
    match["valid"] = validation["valid"]
    match["quality_score"] = validation["score"]  # calidad técnica del dato real, no confianza de apuesta
    match["reject_reasons"] = validation["reasons"]
    match["risk"] = risk_from_match(match)
    match["confidence_score"] = confidence_from_match(match, validation["score"])
    match["shark_score"] = match["confidence_score"]  # valor visible cliente: confianza estimada
    match["stake"] = stake_from_score(match["confidence_score"], match["risk"])
    match["ev"] = "Pendiente"

    return match


def has_fake_content(*values):
    text = " ".join([str(v or "") for v in values]).lower()
    if any(term in text for term in FAKE_TERMS):
        return True
    if any(term in text for term in BLOCKED_DATE_TERMS):
        return True
    return False


def validate_match(match):
    reasons = []
    score = 100

    home = clean_text(match.get("home_team"))
    away = clean_text(match.get("away_team"))
    league = clean_text(match.get("league"))
    source = clean_text(match.get("source")).lower()
    dt = parse_datetime(match.get("commence_time") or match.get("iso"))

    if not home or not away:
        score -= 50
        reasons.append("faltan equipos")

    if home.lower() == away.lower() and home:
        score -= 45
        reasons.append("equipos duplicados")

    if has_fake_content(home, away, league, match.get("date_full"), match.get("commence_time")):
        score -= 80
        reasons.append("contenido fake/legacy bloqueado")

    if source not in {"the_odds_api", "api-football", "real"}:
        score -= 35
        reasons.append("fuente no autorizada")

    now = local_now()
    if not dt:
        score -= 55
        reasons.append("sin fecha real")
    else:
        if dt < now - timedelta(hours=MAX_PAST_HOURS):
            score -= 55
            reasons.append("partido viejo")
        if dt > now + timedelta(days=MAX_FUTURE_DAYS):
            score -= 45
            reasons.append("partido demasiado futuro")
        if dt.year > now.year + 1:
            score -= 80
            reasons.append("año sospechoso")

    score = max(0, min(100, score))
    return {
        "valid": score >= MIN_REAL_SCORE,
        "score": score,
        "reasons": reasons or ["OK"],
    }



def confidence_from_match(match, data_quality_score):
    """Confianza estimada visible al cliente.

    No es probabilidad garantizada ni ML final: combina calidad del dato real,
    cuota disponible, riesgo, casa de apuestas y cercanía temporal para evitar
    mostrar siempre 100 cuando el dato simplemente es válido.
    """
    score = 58
    try:
        dq = int(data_quality_score or 0)
    except Exception:
        dq = 0
    score += max(0, min(18, int((dq - 60) * 0.45)))

    try:
        odds = float(str(match.get("odds") or "0").replace(",", "."))
    except Exception:
        odds = 0.0

    if 1.45 <= odds <= 2.20:
        score += 14
    elif 2.20 < odds <= 2.85:
        score += 8
    elif 1.20 <= odds < 1.45:
        score += 5
    elif odds > 3.25:
        score -= 12
    elif odds <= 0:
        score -= 10

    risk = clean_text(match.get("risk")).lower()
    if "alto" in risk:
        score -= 14
    elif "medio" in risk:
        score -= 6
    elif "bajo" in risk:
        score += 4

    if match.get("bookmaker"):
        score += 4

    status = clean_text(match.get("status")).upper()
    relative = clean_text(match.get("relative")).lower()
    if "EN DIRECTO" in status:
        score += 3
    elif "hoy" in relative or "empieza" in relative:
        score += 2

    return max(35, min(92, int(round(score))))

def risk_from_match(match):
    odds = match.get("odds")
    try:
        odds_f = float(odds)
    except Exception:
        return "Pendiente"

    if odds_f >= 4.0:
        return "Alto"
    if odds_f >= 2.4:
        return "Medio"
    return "Bajo"


def stake_from_score(score, risk):
    if risk == "Alto":
        return "0.5% banca"
    if score >= 88:
        return "2% banca"
    if score >= 78:
        return "1% banca"
    return "0.5% banca"


def dedupe(matches):
    seen = set()
    out = []
    for match in matches:
        key = (
            clean_text(match.get("home_team")).lower(),
            clean_text(match.get("away_team")).lower(),
            str(match.get("commence_time") or match.get("iso")),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(match)
    return out


def bucketize(matches):
    buckets = {
        "live": [],
        "today": [],
        "upcoming": [],
    }
    today = local_now().date()

    for match in matches:
        dt = parse_datetime(match.get("commence_time") or match.get("iso"))
        if match.get("status") == "EN DIRECTO":
            buckets["live"].append(match)
        elif dt and dt.date() == today:
            buckets["today"].append(match)
        else:
            buckets["upcoming"].append(match)

    return buckets


class RealCoreEngine:
    """Fuente única de verdad para partidos, picks y detalles."""

    @staticmethod
    def fetch(force=False):
        now_ts = time.time()
        if not force and _CORE_CACHE["feed"] and now_ts - _CORE_CACHE["ts"] < CACHE_SECONDS:
            return _CORE_CACHE["feed"]

        feed = RealCoreEngine._fetch_the_odds_api()
        _CORE_CACHE["ts"] = now_ts
        _CORE_CACHE["feed"] = feed
        return feed

    @staticmethod
    def _fetch_the_odds_api():
        if requests is None:
            return RealCoreEngine.empty("requests no disponible")

        api_key = env_first("THE_ODDS_API_KEY", "ODDS_API_KEY")
        if not api_key:
            return RealCoreEngine.empty("Falta ODDS_API_KEY / THE_ODDS_API_KEY")

        sports_raw = os.getenv(
            "V91_CORE_SPORTS",
            "soccer_epl,soccer_spain_la_liga,soccer_italy_serie_a,soccer_germany_bundesliga,soccer_france_ligue_one,soccer_portugal_primeira_liga,soccer_uefa_champs_league"
        )
        sports = [s.strip() for s in sports_raw.split(",") if s.strip()]
        regions = os.getenv("ODDS_REGIONS", "eu")
        markets = os.getenv("ODDS_MARKETS", "h2h")
        timeout = int(os.getenv("HTTP_TIMEOUT_SECONDS", "8"))

        matches = []
        errors = []

        for sport in sports:
            try:
                response = requests.get(
                    f"https://api.the-odds-api.com/v4/sports/{sport}/odds",
                    params={
                        "apiKey": api_key,
                        "regions": regions,
                        "markets": markets,
                        "oddsFormat": "decimal",
                    },
                    timeout=timeout,
                )

                if response.status_code != 200:
                    errors.append(f"{sport}: HTTP {response.status_code}")
                    continue

                data = response.json()
                if not isinstance(data, list):
                    errors.append(f"{sport}: respuesta inválida")
                    continue

                for event in data:
                    match = build_real_match(event, sport)
                    if match["valid"]:
                        matches.append(match)

            except Exception as exc:
                errors.append(f"{sport}: {exc}")

        matches = dedupe(matches)
        matches.sort(key=lambda m: m.get("iso") or "")
        buckets = bucketize(matches)

        if not matches:
            return RealCoreEngine.empty("; ".join(errors) if errors else "No hay partidos reales válidos")

        return {
            "ok": True,
            "version": "V91",
            "source": "the_odds_api",
            "message": "Feed real cargado desde Real Core Engine",
            "error": "; ".join(errors) if errors else None,
            "matches": matches,
            "picks": matches,
            "buckets": buckets,
            "counts": {
                "total": len(matches),
                "live": len(buckets["live"]),
                "today": len(buckets["today"]),
                "upcoming": len(buckets["upcoming"]),
            },
            "generated_at": utc_now().isoformat(),
        }

    @staticmethod
    def empty(error=None):
        return {
            "ok": False,
            "version": "V91",
            "source": "none",
            "message": "No hay datos reales disponibles. No se muestran demos.",
            "error": error,
            "matches": [],
            "picks": [],
            "buckets": {"live": [], "today": [], "upcoming": []},
            "counts": {"total": 0, "live": 0, "today": 0, "upcoming": 0},
            "generated_at": utc_now().isoformat(),
        }

    @staticmethod
    def today(force=False):
        return RealCoreEngine.fetch(force=force)["buckets"]["today"]

    @staticmethod
    def live(force=False):
        return RealCoreEngine.fetch(force=force)["buckets"]["live"]

    @staticmethod
    def upcoming(force=False):
        return RealCoreEngine.fetch(force=force)["buckets"]["upcoming"]

    @staticmethod
    def find(match_id, force=False):
        feed = RealCoreEngine.fetch(force=force)
        wanted = str(match_id)
        for match in feed.get("matches", []):
            if str(match.get("id")) == wanted or str(match.get("legacy_id", "")) == wanted:
                return match, feed
        return None, feed

    @staticmethod
    def status():
        feed = RealCoreEngine.fetch(force=False)
        return {
            "version": "V91",
            "status": "REAL CORE ENGINE ACTIVO",
            "single_source_of_truth": True,
            "no_demo_fallback": True,
            "strict_real_only": True,
            "cache_seconds": CACHE_SECONDS,
            "max_future_days": MAX_FUTURE_DAYS,
            "max_past_hours": MAX_PAST_HOURS,
            "min_real_score": MIN_REAL_SCORE,
            "feed": feed,
            "modules": [
                "Single source of truth",
                "Real match validator",
                "Anti legacy/fake terms",
                "Cache central",
                "LIVE / HOY / PRÓXIMOS",
                "Detalle real-only",
                "No demo fallback",
                "Market normalizer",
                "League mapper",
            ],
        }


def purge_legacy_db(get_db_func=None):
    if not get_db_func:
        return {"ok": False, "reason": "get_db no disponible"}

    try:
        conn = get_db_func()
        cur = conn.cursor()
        try:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cur.fetchall()]
        except Exception:
            tables = []

        affected = 0
        terms = list(FAKE_TERMS) + list(BLOCKED_DATE_TERMS)

        for table in ["picks", "matches", "events", "fixtures", "games"]:
            if table not in tables:
                continue

            for term in terms:
                like = f"%{term.upper()}%"
                column_sets = [
                    ("title", "pick", "league", "kickoff_time", "home_team", "away_team", "source"),
                    ("home_team", "away_team", "league", "commence_time", "source", "status"),
                    ("home", "away", "competition", "date", "source", "status"),
                    ("team_home", "team_away", "competition", "kickoff_time", "source", "status"),
                ]

                for cols in column_sets:
                    try:
                        condition = " OR ".join([f"UPPER(COALESCE({col},'')) LIKE ?" for col in cols])
                        cur.execute(
                            f"UPDATE {table} SET active=0 WHERE ({condition})",
                            tuple([like] * len(cols)),
                        )
                        affected += max(cur.rowcount or 0, 0)
                    except Exception:
                        pass

        conn.commit()
        conn.close()
        return {"ok": True, "affected": affected}

    except Exception as exc:
        return {"ok": False, "error": str(exc)}
