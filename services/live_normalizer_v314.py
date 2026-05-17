
"""V314 · Live normalizer helpers.
REAL ONLY: normaliza datos existentes, no inventa marcador/minuto/escudos.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional


def first_present(*values: Any) -> Any:
    for value in values:
        if value is not None and value != "" and value != [] and value != {}:
            return value
    return None


def safe_team_name(team: Any) -> str:
    if isinstance(team, dict):
        return str(first_present(team.get("name"), team.get("team"), team.get("displayName"), "Equipo") or "Equipo")
    if team:
        return str(team)
    return "Equipo"


def safe_crest(team: Any, fallback: str = "") -> str:
    if isinstance(team, dict):
        return str(first_present(
            team.get("crest"),
            team.get("logo"),
            team.get("badge"),
            team.get("badge_url"),
            team.get("image"),
            team.get("team_logo"),
            fallback
        ) or fallback)
    return fallback


def normalize_live_match(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Devuelve un contrato estable para tarjetas live."""
    raw = raw or {}

    home = first_present(raw.get("home_team"), raw.get("home"), raw.get("team_home"), raw.get("localTeam"), raw.get("local_team"), {})
    away = first_present(raw.get("away_team"), raw.get("away"), raw.get("team_away"), raw.get("visitorTeam"), raw.get("away_team"), {})

    score = first_present(raw.get("score"), raw.get("goals"), raw.get("result"), raw.get("scores"), {})
    home_score = first_present(
        raw.get("home_score"),
        raw.get("score_home"),
        raw.get("home_goals"),
        score.get("home") if isinstance(score, dict) else None,
        score.get("home_score") if isinstance(score, dict) else None,
    )
    away_score = first_present(
        raw.get("away_score"),
        raw.get("score_away"),
        raw.get("away_goals"),
        score.get("away") if isinstance(score, dict) else None,
        score.get("away_score") if isinstance(score, dict) else None,
    )

    minute = first_present(
        raw.get("minute"),
        raw.get("elapsed"),
        raw.get("time"),
        raw.get("match_minute"),
        raw.get("current_minute"),
        raw.get("status_minute"),
    )

    status = first_present(raw.get("status"), raw.get("match_status"), raw.get("state"), raw.get("short_status"), "LIVE")

    return {
        "id": first_present(raw.get("id"), raw.get("fixture_id"), raw.get("event_id"), raw.get("match_id"), ""),
        "home_name": safe_team_name(home),
        "away_name": safe_team_name(away),
        "home_crest": safe_crest(home),
        "away_crest": safe_crest(away),
        "home_score": home_score,
        "away_score": away_score,
        "minute": minute,
        "status": status,
        "league": first_present(raw.get("league"), raw.get("competition"), raw.get("sport_key"), ""),
        "source": first_present(raw.get("source"), raw.get("provider"), "real_api"),
        "has_score": home_score is not None and away_score is not None,
        "has_minute": minute is not None,
        "has_crests": bool(safe_crest(home)) or bool(safe_crest(away)),
        "raw": raw,
    }


def vapid_is_configured() -> bool:
    return bool(os.getenv("VAPID_PUBLIC_KEY") and os.getenv("VAPID_PRIVATE_KEY"))


def client_vapid_state() -> Dict[str, Any]:
    configured = vapid_is_configured()
    return {
        "configured": configured,
        "client_message": "" if configured else "Notificaciones push no activadas todavía. La app funciona igualmente.",
        "hide_warning_for_client": True,
    }
