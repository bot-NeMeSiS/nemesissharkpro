
from datetime import datetime

def _num(v, default=0):
    try:
        return float(v)
    except Exception:
        return default

def build_momentum(match):
    home_pressure = _num(match.get("home_pressure") or match.get("pressure_home") or match.get("home_attack_pressure"), 50)
    away_pressure = _num(match.get("away_pressure") or match.get("pressure_away") or match.get("away_attack_pressure"), 50)
    shots = _num(match.get("shots") or match.get("total_shots"), 0)
    corners = _num(match.get("corners") or match.get("total_corners"), 0)
    odds_shift = _num(match.get("odds_shift") or match.get("line_movement"), 0)

    dominant = "LOCAL" if home_pressure >= away_pressure else "VISITANTE"
    pressure = max(home_pressure, away_pressure)
    momentum_score = min(100, round(pressure * 0.68 + shots * 1.2 + corners * 1.4 + abs(odds_shift) * 3, 2))

    if momentum_score >= 85:
        signal = "HIGH_MOMENTUM"
    elif momentum_score >= 72:
        signal = "VALUE_WATCH"
    elif momentum_score >= 60:
        signal = "WATCH"
    else:
        signal = "NO_SIGNAL"

    return {
        "version": "V122_LIVE_MOMENTUM_ENGINE",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "match": match.get("match") or f"{match.get('home_team','Local')} vs {match.get('away_team','Visitante')}",
        "minute": match.get("minute") or "LIVE",
        "dominant": dominant,
        "momentum_score": momentum_score,
        "signal": signal,
        "reading": f"Momentum {dominant} con score {momentum_score}. Señal: {signal}.",
        "data_policy": "Interpreta solo datos recibidos; no inventa eventos."
    }
