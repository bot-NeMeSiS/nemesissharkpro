
"""
NeMeSiS SHARK PRO V83
Live Experience Engine

Objetivo:
- Mejorar sensación Flashscore/Sofascore.
- Estados inteligentes.
- Countdown.
- Match cards premium.
- Momentum visual.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import random

TZ = ZoneInfo(os.getenv("DISPLAY_TIMEZONE", "Europe/Madrid"))


def now_madrid():
    return datetime.now(TZ)


def parse_iso(value):
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
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(TZ)


def infer_match_status(commence_time=None, raw_status=None):
    status = (raw_status or "").lower()
    if status in ["live", "in_play", "inplay", "en juego"]:
        return {"key": "LIVE", "label": "LIVE", "class": "live", "priority": 1}
    if status in ["finished", "final", "ended", "finalizado"]:
        return {"key": "FINISHED", "label": "FINAL", "class": "finished", "priority": 4}
    if status in ["halftime", "descanso", "ht"]:
        return {"key": "HT", "label": "DESCANSO", "class": "warning", "priority": 2}

    dt = parse_iso(commence_time)
    if not dt:
        return {"key": "SCHEDULED", "label": "PROGRAMADO", "class": "scheduled", "priority": 3}

    now = now_madrid()
    diff_min = int((dt - now).total_seconds() // 60)

    if -130 <= diff_min <= 130:
        return {"key": "LIVE", "label": "LIVE", "class": "live", "priority": 1}
    if diff_min < -130:
        return {"key": "FINISHED", "label": "FINAL / RECIENTE", "class": "finished", "priority": 4}
    if diff_min <= 60:
        return {"key": "SOON", "label": "PRÓXIMO", "class": "soon", "priority": 2}
    return {"key": "SCHEDULED", "label": "PROGRAMADO", "class": "scheduled", "priority": 3}


def countdown_label(commence_time=None, raw_status=None):
    status = infer_match_status(commence_time, raw_status)
    if status["key"] == "LIVE":
        minute = live_minute(commence_time)
        return f"LIVE · {minute}'" if minute else "LIVE"
    if status["key"] == "HT":
        return "DESCANSO"
    if status["key"] == "FINISHED":
        return "FINALIZADO"

    dt = parse_iso(commence_time)
    if not dt:
        return "Horario pendiente"

    diff = dt - now_madrid()
    minutes = int(diff.total_seconds() // 60)

    if minutes <= 0:
        return "Empezando"
    if minutes < 60:
        return f"Empieza en {minutes} min"
    if minutes < 24 * 60:
        return f"Empieza en {minutes // 60} h"
    return f"Empieza en {minutes // (24 * 60)} días"


def live_minute(commence_time=None):
    dt = parse_iso(commence_time)
    if not dt:
        return None
    minutes = int((now_madrid() - dt).total_seconds() // 60)
    if minutes < 0:
        return None
    if minutes <= 45:
        return max(minutes, 1)
    if minutes <= 60:
        return 45
    if minutes <= 105:
        return min(minutes - 15, 90)
    return 90


def momentum_payload(match=None):
    """
    Momentum visual ligero.
    Si en el futuro hay stats reales, sustituir random por tiros/corners/ataques.
    """
    match = match or {}
    seed = str(match.get("id") or match.get("match_name") or match.get("home_team") or "nsp")
    value = sum(ord(c) for c in seed) % 100

    if value >= 78:
        label = "Presión ofensiva alta"
        icon = "🔥"
        level = "high"
    elif value >= 55:
        label = "Momentum favorable"
        icon = "⚡"
        level = "medium"
    elif value >= 35:
        label = "Partido equilibrado"
        icon = "⚖️"
        level = "balanced"
    else:
        label = "Ritmo bajo"
        icon = "🧊"
        level = "low"

    return {
        "value": value,
        "label": label,
        "icon": icon,
        "level": level,
    }


def heat_level(match=None, shark_score=None):
    score = float(shark_score or 0)
    momentum = momentum_payload(match)["value"]

    heat = min(round(score * 0.65 + momentum * 0.35, 2), 99)

    if heat >= 82:
        label = "EXTREMO"
        css = "extreme"
    elif heat >= 68:
        label = "ALTO"
        css = "high"
    elif heat >= 48:
        label = "MEDIO"
        css = "medium"
    else:
        label = "BAJO"
        css = "low"

    return {"value": heat, "label": label, "class": css}


def enhance_match(match):
    if not isinstance(match, dict):
        return match

    commence = (
        match.get("commence_time")
        or match.get("start_time")
        or match.get("match_time")
        or match.get("datetime")
        or match.get("date")
    )
    status = infer_match_status(commence, match.get("status"))
    match["live_status"] = status
    match["live_countdown"] = countdown_label(commence, match.get("status"))
    match["live_minute"] = live_minute(commence)
    match["momentum"] = momentum_payload(match)
    match["heat"] = heat_level(match, match.get("shark_score") or match.get("score") or 72)
    return match


def enhance_matches(matches):
    if not isinstance(matches, list):
        return matches
    return sorted([enhance_match(dict(m)) for m in matches], key=lambda x: x.get("live_status", {}).get("priority", 9))


def demo_live_matches():
    now = now_madrid()
    sample = [
        {
            "id": "demo-live-1",
            "league": "Premier",
            "home_team": "Liverpool",
            "away_team": "Chelsea",
            "match_name": "Liverpool vs Chelsea",
            "commence_time": (now - timedelta(minutes=67)).isoformat(),
            "status": "live",
            "shark_score": 87,
            "market": "Empate gana",
            "odds": 1.92,
        },
        {
            "id": "demo-soon-1",
            "league": "LaLiga",
            "home_team": "Elche CF",
            "away_team": "Alavés",
            "match_name": "Elche CF vs Alavés",
            "commence_time": (now + timedelta(minutes=32)).isoformat(),
            "status": "scheduled",
            "shark_score": 74,
            "market": "Gana Alavés",
            "odds": 2.15,
        },
        {
            "id": "demo-scheduled-1",
            "league": "Champions",
            "home_team": "Inter",
            "away_team": "Arsenal",
            "match_name": "Inter vs Arsenal",
            "commence_time": (now + timedelta(hours=5)).isoformat(),
            "status": "scheduled",
            "shark_score": 69,
            "market": "Over 2.5",
            "odds": 1.78,
        },
    ]
    return enhance_matches(sample)


def get_live_experience_status():
    matches = demo_live_matches()
    return {
        "status": "LIVE EXPERIENCE ACTIVO",
        "version": "V83",
        "timezone": "Europe/Madrid",
        "live_count": len([m for m in matches if m["live_status"]["key"] == "LIVE"]),
        "soon_count": len([m for m in matches if m["live_status"]["key"] == "SOON"]),
        "matches": matches,
        "modules": [
            {"name": "Live badges", "status": "ACTIVO"},
            {"name": "Countdown Engine", "status": "ACTIVO"},
            {"name": "Smart Match Cards", "status": "ACTIVO"},
            {"name": "Momentum visual", "status": "ACTIVO"},
            {"name": "Heat levels", "status": "ACTIVO"},
            {"name": "Mobile live polish", "status": "ACTIVO"},
        ],
    }
