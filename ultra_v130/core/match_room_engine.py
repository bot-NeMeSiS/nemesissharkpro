
from datetime import datetime

def _num(v, default=0):
    try:
        return float(v)
    except Exception:
        return default

def build_match_room(match):
    home = match.get("home_team") or match.get("home") or "Local"
    away = match.get("away_team") or match.get("away") or "Visitante"
    league = match.get("league") or "Liga no especificada"
    pick = match.get("pick") or match.get("prediction") or "Sin pick activo"
    odds = match.get("odds") or match.get("price") or "N/A"
    score = _num(match.get("shark_score") or match.get("score"), 0)
    ev = str(match.get("ev") or match.get("expected_value") or "N/A").upper()
    risk = str(match.get("risk") or "MEDIUM").upper()
    momentum = match.get("momentum") or "Esperando datos live reales"

    reasons_for = []
    reasons_against = []

    if score >= 80:
        reasons_for.append("SHARK Score alto para lectura premium.")
    else:
        reasons_against.append("SHARK Score todavía no confirma entrada fuerte.")

    if ev in ["HIGH", "POSITIVE", "VALUE", "+EV", "ALTO"]:
        reasons_for.append("Value positivo detectado en datos disponibles.")
    else:
        reasons_against.append("EV no confirmado como alto.")

    if risk in ["LOW", "MEDIUM"]:
        reasons_for.append("Riesgo compatible con stake controlado.")
    else:
        reasons_against.append("Riesgo alto: evitar entrada agresiva.")

    if score >= 85 and risk in ["LOW", "MEDIUM"]:
        recommendation = "ENTRADA CONTROLADA"
    elif score >= 70:
        recommendation = "WATCHLIST PREMIUM"
    else:
        recommendation = "NO ENTRAR"

    return {
        "version": "V127_SHARK_MATCH_ROOM",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "match": f"{home} vs {away}",
        "home_team": home,
        "away_team": away,
        "league": league,
        "pick": pick,
        "odds": odds,
        "shark_score": score,
        "ev": ev,
        "risk": risk,
        "momentum": momentum,
        "recommendation": recommendation,
        "reasons_for": reasons_for,
        "reasons_against": reasons_against,
        "ai_reading": f"{home} vs {away}: {recommendation}. Pick {pick}, score {score}, riesgo {risk}, EV {ev}.",
        "no_fake_policy": True
    }
