
from datetime import datetime

def _num(value, default=0):
    try:
        return float(value)
    except Exception:
        return default

def build_live_signal(match):
    """
    Real Live Intelligence.
    Interpreta campos existentes del Real Core/feed. No inventa datos externos.
    """
    home = match.get("home_team") or match.get("home") or "Local"
    away = match.get("away_team") or match.get("away") or "Visitante"
    minute = match.get("minute") or match.get("live_minute") or "LIVE"
    scoreline = match.get("scoreline") or match.get("result") or "N/A"

    home_pressure = _num(match.get("home_pressure") or match.get("pressure_home") or match.get("home_attack_pressure"), 50)
    away_pressure = _num(match.get("away_pressure") or match.get("pressure_away") or match.get("away_attack_pressure"), 50)
    shark_score = _num(match.get("shark_score") or match.get("score") or ((home_pressure + away_pressure) / 2), 0)
    odds = match.get("odds") or match.get("price") or "N/A"
    ev = str(match.get("ev") or match.get("expected_value") or "N/A").upper()
    risk = str(match.get("risk") or "MEDIUM").upper()

    dominant_team = "LOCAL" if home_pressure >= away_pressure else "VISITANTE"
    pressure_gap = abs(home_pressure - away_pressure)

    momentum_score = min(100, max(0, round((max(home_pressure, away_pressure) * 0.65) + (shark_score * 0.35), 2)))

    if momentum_score >= 85 and risk in ["LOW", "MEDIUM"]:
        signal = "LIVE_STRONG_SIGNAL"
        suggested_pick = "Buscar value live controlado"
    elif momentum_score >= 74:
        signal = "LIVE_VALUE_WATCH"
        suggested_pick = "Vigilar entrada live"
    elif momentum_score >= 62:
        signal = "LIVE_WATCHLIST"
        suggested_pick = "Esperar confirmación"
    else:
        signal = "NO_LIVE_ENTRY"
        suggested_pick = "No entrar"

    reasons = []
    warnings = []

    if pressure_gap >= 18:
        reasons.append("Diferencia de presión clara entre equipos.")
    else:
        warnings.append("Presión equilibrada; entrada menos clara.")

    if ev in ["HIGH", "POSITIVE", "VALUE", "+EV", "ALTO"]:
        reasons.append("EV positivo detectado en datos disponibles.")
    else:
        warnings.append("EV no confirmado como alto.")

    if risk == "HIGH":
        warnings.append("Riesgo alto: evitar stake agresivo.")

    ai_reading = (
        f"{home} vs {away}: momentum {dominant_team}, score live {momentum_score}. "
        f"Señal: {signal}. Recomendación: {suggested_pick}."
    )

    return {
        "version": "V109_REAL_LIVE_INTELLIGENCE",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "match": f"{home} vs {away}",
        "home_team": home,
        "away_team": away,
        "minute": minute,
        "scoreline": scoreline,
        "home_pressure": home_pressure,
        "away_pressure": away_pressure,
        "dominant_team": dominant_team,
        "momentum_score": momentum_score,
        "shark_score": shark_score,
        "odds": odds,
        "ev": ev,
        "risk": risk,
        "signal": signal,
        "suggested_pick": suggested_pick,
        "reasons": reasons,
        "warnings": warnings,
        "ai_reading": ai_reading,
    }

def build_live_center(matches):
    readings = [build_live_signal(m) for m in (matches or [])]
    readings = sorted(readings, key=lambda r: r["momentum_score"], reverse=True)

    return {
        "version": "V109_REAL_LIVE_INTELLIGENCE",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total": len(readings),
        "strong": len([r for r in readings if r["signal"] == "LIVE_STRONG_SIGNAL"]),
        "watch": len([r for r in readings if r["signal"] in ["LIVE_VALUE_WATCH", "LIVE_WATCHLIST"]]),
        "readings": readings,
    }

def empty_live_center():
    return build_live_center([])
