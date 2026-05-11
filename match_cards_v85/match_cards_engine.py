
"""
NeMeSiS SHARK PRO V85
Match Cards PRO

Mejora principal:
- fecha visible
- hora limpia sin "Madrid"
- tarjeta más premium
- explicación SHARK AI más humana
"""

from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import os


TZ = ZoneInfo(os.getenv("DISPLAY_TIMEZONE", "Europe/Madrid"))


def _parse_dt(value):
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
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M"):
                try:
                    dt = datetime.strptime(raw, fmt)
                    break
                except Exception:
                    dt = None
            if dt is None:
                return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(TZ)


def format_card_time(value):
    dt = _parse_dt(value)
    if not dt:
        return {
            "date_short": "Fecha pendiente",
            "date_full": "Fecha pendiente",
            "time": "--:--",
            "day": "--",
            "month": "",
            "relative": "Horario sin confirmar",
            "iso": None,
            "valid": False,
        }

    now = datetime.now(TZ)
    dias = ["LUN", "MAR", "MIÉ", "JUE", "VIE", "SÁB", "DOM"]
    meses = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]

    if dt.date() == now.date():
        date_short = "HOY"
    elif dt.date() == (now + timedelta(days=1)).date():
        date_short = "MAÑANA"
    else:
        date_short = f"{dias[dt.weekday()]} {dt.day} {meses[dt.month-1]}"

    minutes = int((dt - now).total_seconds() // 60)
    if -130 <= minutes <= 130:
        relative = "En juego / cerca"
    elif minutes > 0:
        relative = f"Empieza en {minutes} min" if minutes < 60 else (f"Empieza en {minutes//60} h" if minutes < 1440 else f"Empieza en {minutes//1440} días")
    else:
        relative = "Reciente"

    return {
        "date_short": date_short,
        "date_full": dt.strftime("%d/%m/%Y"),
        "time": dt.strftime("%H:%M"),
        "day": dias[dt.weekday()],
        "month": meses[dt.month-1],
        "relative": relative,
        "iso": dt.isoformat(),
        "valid": True,
    }


def confidence_label(score):
    try:
        score = float(score or 0)
    except Exception:
        score = 0
    if score >= 88:
        return "ELITE"
    if score >= 78:
        return "ALTA"
    if score >= 65:
        return "MEDIA"
    return "BAJA"


def risk_label(risk=None, odds=None):
    if risk:
        r = str(risk).lower()
        if "baj" in r:
            return "Bajo"
        if "alt" in r:
            return "Alto"
        return "Medio"
    try:
        odds = float(odds or 0)
        if odds <= 2.20:
            return "Bajo"
        if odds <= 4.00:
            return "Medio"
        return "Alto"
    except Exception:
        return "Medio"


def build_ai_reason(match):
    team_home = match.get("home_team") or match.get("home") or match.get("team_home") or match.get("local") or "Local"
    team_away = match.get("away_team") or match.get("away") or match.get("team_away") or match.get("visitante") or "Visitante"
    market = match.get("market") or match.get("pick_market") or match.get("bet_type") or "mercado seleccionado"
    odds = match.get("odds") or match.get("cuota") or match.get("price") or "-"
    score = match.get("shark_score") or match.get("score") or match.get("confidence") or 75
    ev = match.get("ev") or match.get("expected_value") or None
    risk = risk_label(match.get("risk"), odds)

    parts = [
        f"SHARK AI ve valor en {market}",
        f"cuota {odds}",
        f"riesgo {risk.lower()}",
        f"score {score}%",
    ]

    if ev not in (None, "", "-"):
        parts.append(f"EV {ev}")

    return " · ".join(parts) + "."


def normalize_card_payload(match):
    if not isinstance(match, dict):
        return match

    raw_time = (
        match.get("commence_time")
        or match.get("start_time")
        or match.get("match_time")
        or match.get("datetime")
        or match.get("date")
    )

    t = format_card_time(raw_time)

    score = match.get("shark_score") or match.get("score") or match.get("confidence") or 75
    odds = match.get("odds") or match.get("cuota") or match.get("price") or "-"
    risk = risk_label(match.get("risk"), odds)

    match["v85_date"] = t["date_short"]
    match["v85_date_full"] = t["date_full"]
    match["v85_time"] = t["time"]
    match["v85_relative"] = t["relative"]
    match["v85_time_valid"] = t["valid"]
    match["v85_confidence"] = confidence_label(score)
    match["v85_risk"] = risk
    match["v85_ai_reason"] = match.get("ai_reason") or match.get("reason") or build_ai_reason(match)

    return match


def demo_cards():
    now = datetime.now(TZ)
    samples = [
        {
            "league": "LaLiga",
            "home_team": "Rayo Vallecano",
            "away_team": "Girona",
            "market": "Gana Hándicap: Rayo Vallecano",
            "odds": 3.80,
            "shark_score": 84,
            "ev": "+4.9%",
            "stake": "2%",
            "commence_time": (now + timedelta(hours=20)).isoformat(),
        },
        {
            "league": "Liga Portugal",
            "home_team": "Tondela",
            "away_team": "Moreirense FC",
            "market": "Gana Moreirense FC",
            "odds": 4.20,
            "shark_score": 89,
            "ev": "+5.6%",
            "stake": "3%",
            "commence_time": (now + timedelta(hours=21, minutes=15)).isoformat(),
        },
    ]
    return [normalize_card_payload(x) for x in samples]


def get_v85_status():
    return {
        "status": "MATCH CARDS PRO ACTIVO",
        "version": "V85",
        "modules": [
            "Fecha visible",
            "Hora limpia",
            "SHARK AI reason pro",
            "Value / risk / stake mejorado",
            "Tarjetas responsive",
            "Preparado para datos reales",
        ],
        "demo_cards": demo_cards(),
    }
