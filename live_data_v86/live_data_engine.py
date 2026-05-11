
"""
NeMeSiS SHARK PRO V86
Live/Data Real Engine

Objetivo:
- Limpiar partidos raros.
- Normalizar fechas y horas.
- Separar hoy / live / próximos.
- Detectar datos demo/fallback sospechosos.
- Dar score de calidad de datos.
"""

import os
import re
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo


TZ = ZoneInfo(os.getenv("DISPLAY_TIMEZONE", "Europe/Madrid"))
MAX_FUTURE_DAYS = int(os.getenv("V86_MAX_FUTURE_DAYS", os.getenv("MAX_FUTURE_DAYS", "30")))
MAX_PAST_HOURS = int(os.getenv("V86_MAX_PAST_HOURS", "12"))


SUSPICIOUS_TEAMS = {
    "team a", "team b", "home", "away", "local", "visitante",
    "demo", "test", "example", "equipo local", "equipo visitante",
}


def now_local():
    return datetime.now(TZ)


def parse_datetime(value):
    if not value:
        return None

    if isinstance(value, datetime):
        dt = value
    else:
        raw = str(value).strip()
        if not raw:
            return None
        try:
            if raw.endswith("Z"):
                raw = raw[:-1] + "+00:00"
            dt = datetime.fromisoformat(raw)
        except Exception:
            dt = None
            for fmt in (
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%d/%m/%Y %H:%M",
                "%d/%m/%Y",
            ):
                try:
                    dt = datetime.strptime(raw, fmt)
                    break
                except Exception:
                    pass
            if dt is None:
                return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(TZ)


def get_match_time(match):
    if not isinstance(match, dict):
        return None
    return (
        match.get("commence_time")
        or match.get("start_time")
        or match.get("match_time")
        or match.get("datetime")
        or match.get("date")
        or match.get("kickoff")
    )


def clean_team_name(name):
    text = str(name or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text


def get_teams(match):
    home = (
        match.get("home_team")
        or match.get("home")
        or match.get("team_home")
        or match.get("local")
        or match.get("equipo_local")
        or ""
    )
    away = (
        match.get("away_team")
        or match.get("away")
        or match.get("team_away")
        or match.get("visitante")
        or match.get("equipo_visitante")
        or ""
    )
    return clean_team_name(home), clean_team_name(away)


def format_date_time(dt):
    if not dt:
        return {
            "date": "Fecha pendiente",
            "date_full": "Fecha pendiente",
            "time": "--:--",
            "relative": "Horario sin confirmar",
            "status": "UNKNOWN",
        }

    now = now_local()
    dias = ["LUN", "MAR", "MIÉ", "JUE", "VIE", "SÁB", "DOM"]
    meses = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]

    if dt.date() == now.date():
        date = "HOY"
    elif dt.date() == (now + timedelta(days=1)).date():
        date = "MAÑANA"
    else:
        date = f"{dias[dt.weekday()]} {dt.day} {meses[dt.month - 1]}"

    minutes = int((dt - now).total_seconds() // 60)

    if -130 <= minutes <= 130:
        relative = "Live / cerca"
        status = "LIVE"
    elif minutes > 0:
        status = "UPCOMING"
        if minutes < 60:
            relative = f"Empieza en {minutes} min"
        elif minutes < 1440:
            relative = f"Empieza en {minutes // 60} h"
        else:
            relative = f"Empieza en {minutes // 1440} días"
    else:
        status = "RECENT"
        relative = "Reciente"

    return {
        "date": date,
        "date_full": dt.strftime("%d/%m/%Y"),
        "time": dt.strftime("%H:%M"),
        "relative": relative,
        "status": status,
    }


def validate_match(match):
    reasons = []
    score = 100

    if not isinstance(match, dict):
        return {
            "valid": False,
            "score": 0,
            "reasons": ["Formato inválido"],
        }

    home, away = get_teams(match)

    if not home or not away:
        score -= 30
        reasons.append("Equipo local o visitante no disponible")

    if home.lower() in SUSPICIOUS_TEAMS or away.lower() in SUSPICIOUS_TEAMS:
        score -= 35
        reasons.append("Nombre de equipo sospechoso/demo")

    if home and away and home.lower() == away.lower():
        score -= 35
        reasons.append("Local y visitante son iguales")

    dt = parse_datetime(get_match_time(match))
    now = now_local()

    if not dt:
        score -= 40
        reasons.append("Fecha/hora no disponible")
    else:
        if dt < now - timedelta(hours=MAX_PAST_HOURS):
            score -= 30
            reasons.append("Partido demasiado antiguo")
        if dt > now + timedelta(days=MAX_FUTURE_DAYS):
            score -= 35
            reasons.append("Partido demasiado futuro")
        if dt.year > now.year + 1:
            score -= 40
            reasons.append("Año sospechoso")

    odds = match.get("odds") or match.get("cuota") or match.get("price")
    try:
        odds_f = float(odds)
        if odds_f < 1.01 or odds_f > 100:
            score -= 25
            reasons.append("Cuota fuera de rango normal")
    except Exception:
        score -= 10
        reasons.append("Cuota no disponible")

    league = match.get("league") or match.get("sport_title") or match.get("competition")
    if not league:
        score -= 8
        reasons.append("Liga no disponible")

    score = max(min(score, 100), 0)

    return {
        "valid": score >= int(os.getenv("V86_MIN_DATA_SCORE", "55")),
        "score": score,
        "reasons": reasons or ["OK"],
    }


def normalize_match(match):
    if not isinstance(match, dict):
        return match

    home, away = get_teams(match)
    dt = parse_datetime(get_match_time(match))
    time_payload = format_date_time(dt)
    validation = validate_match(match)

    normalized = dict(match)
    normalized.update({
        "home_team": home,
        "away_team": away,
        "league": match.get("league") or match.get("sport_title") or match.get("competition") or "Competición",
        "v86_date": time_payload["date"],
        "v86_date_full": time_payload["date_full"],
        "v86_time": time_payload["time"],
        "v86_relative": time_payload["relative"],
        "v86_status": time_payload["status"],
        "v86_data_score": validation["score"],
        "v86_valid": validation["valid"],
        "v86_reasons": validation["reasons"],
        "v86_quality_label": quality_label(validation["score"]),
    })

    return normalized


def quality_label(score):
    try:
        score = float(score)
    except Exception:
        score = 0

    if score >= 90:
        return "Excelente"
    if score >= 75:
        return "Buena"
    if score >= 55:
        return "Aceptable"
    return "Revisar"


def normalize_matches(matches, hide_invalid=True):
    if not isinstance(matches, list):
        return []
    out = []
    for m in matches:
        item = normalize_match(m)
        if hide_invalid and not item.get("v86_valid", False):
            continue
        out.append(item)
    return out


def bucket_matches(matches):
    normalized = normalize_matches(matches, hide_invalid=False)
    buckets = {
        "live": [],
        "today": [],
        "upcoming": [],
        "recent": [],
        "invalid": [],
    }

    today = now_local().date()

    for m in normalized:
        if not m.get("v86_valid"):
            buckets["invalid"].append(m)
            continue

        status = m.get("v86_status")
        dt = parse_datetime(get_match_time(m))

        if status == "LIVE":
            buckets["live"].append(m)
        elif dt and dt.date() == today:
            buckets["today"].append(m)
        elif status == "RECENT":
            buckets["recent"].append(m)
        else:
            buckets["upcoming"].append(m)

    return buckets


def data_quality_report(matches):
    normalized = normalize_matches(matches, hide_invalid=False)

    total = len(normalized)
    valid = len([m for m in normalized if m.get("v86_valid")])
    invalid = total - valid
    avg = round(sum([m.get("v86_data_score", 0) for m in normalized]) / total, 2) if total else 0
    buckets = bucket_matches(matches)

    return {
        "total": total,
        "valid": valid,
        "invalid": invalid,
        "avg_quality_score": avg,
        "live": len(buckets["live"]),
        "today": len(buckets["today"]),
        "upcoming": len(buckets["upcoming"]),
        "recent": len(buckets["recent"]),
        "status": "DATA REAL OK" if total and invalid == 0 else ("DATA MIXTA / REVISAR" if total else "SIN DATOS"),
        "buckets": buckets,
    }


def demo_matches():
    now = now_local()
    return [
        {
            "league": "LaLiga",
            "home_team": "Rayo Vallecano",
            "away_team": "Girona",
            "market": "Gana Hándicap: Rayo Vallecano",
            "odds": 3.80,
            "shark_score": 84,
            "commence_time": (now + timedelta(hours=2)).isoformat(),
        },
        {
            "league": "Serie A",
            "home_team": "Cagliari",
            "away_team": "Udinese",
            "market": "Gana Hándicap: Cagliari",
            "odds": 4.55,
            "shark_score": 81,
            "commence_time": (now + timedelta(hours=22)).isoformat(),
        },
        {
            "league": "Demo League",
            "home_team": "Team A",
            "away_team": "Team B",
            "market": "Demo pick",
            "odds": 2.00,
            "commence_time": (now + timedelta(days=500)).isoformat(),
        },
    ]


def get_v86_status():
    report = data_quality_report(demo_matches())
    return {
        "version": "V86",
        "status": "LIVE DATA REAL ENGINE ACTIVO",
        "timezone": str(TZ),
        "now": now_local().strftime("%d/%m/%Y %H:%M"),
        "max_future_days": MAX_FUTURE_DAYS,
        "max_past_hours": MAX_PAST_HOURS,
        "min_data_score": int(os.getenv("V86_MIN_DATA_SCORE", "55")),
        "report": report,
        "modules": [
            "Normalización fechas",
            "Hora limpia",
            "Filtros hoy/live/próximos",
            "Bloqueo datos demo",
            "Quality score",
            "Panel admin data quality",
        ],
    }
