from datetime import datetime

def _num(value, default=0):
    try:
        return float(value)
    except Exception:
        return default

def classify_live_signal(match):
    """
    Interprets existing Real Core/live feed fields only.
    Does not invent external stats.
    """
    shark_score = _num(match.get("shark_score") or match.get("score"), 0)
    live_score = _num(match.get("live_score") or match.get("live_trading_score"), shark_score)
    pressure = _num(match.get("pressure") or match.get("attack_pressure"), 0)
    momentum = str(match.get("momentum") or "").lower()
    risk = str(match.get("risk") or "MEDIUM").upper()
    ev = str(match.get("ev") or match.get("expected_value") or "N/A").upper()

    signal_score = max(shark_score, live_score)

    if pressure >= 75:
        signal_score += 5
    if "high" in momentum or "alto" in momentum or "positivo" in momentum:
        signal_score += 5
    if ev in ["HIGH", "POSITIVE", "VALUE", "+EV"]:
        signal_score += 5
    if risk == "HIGH":
        signal_score -= 8

    if signal_score >= 90 and risk in ["LOW", "MEDIUM"]:
        return "LIVE_STRONG_ENTRY"
    if signal_score >= 80:
        return "LIVE_VALUE_ENTRY"
    if signal_score >= 68:
        return "LIVE_WATCHLIST"
    return "NO_LIVE_ENTRY"

def build_live_trading_reading(match):
    home = match.get("home_team") or match.get("home") or "Local"
    away = match.get("away_team") or match.get("away") or "Visitante"
    minute = match.get("minute") or match.get("live_minute") or "N/A"
    scoreline = match.get("scoreline") or match.get("result") or "N/A"
    pick = match.get("pick") or match.get("prediction") or "Sin pick activo"
    odds = match.get("odds") or match.get("price") or "N/A"
    shark_score = _num(match.get("shark_score") or match.get("score"), 0)
    pressure = _num(match.get("pressure") or match.get("attack_pressure"), 0)
    momentum = match.get("momentum") or "Momentum no disponible"
    risk = str(match.get("risk") or "MEDIUM").upper()
    ev = str(match.get("ev") or match.get("expected_value") or "N/A").upper()

    signal = classify_live_signal(match)

    alerts = []
    if signal == "LIVE_STRONG_ENTRY":
        alerts.append("Entrada live fuerte controlada detectada.")
    elif signal == "LIVE_VALUE_ENTRY":
        alerts.append("Value live detectado, revisar cuota y stake.")
    elif signal == "LIVE_WATCHLIST":
        alerts.append("Partido en vigilancia: esperar confirmación de momentum.")
    else:
        alerts.append("Sin entrada live recomendable ahora mismo.")

    if pressure >= 75:
        alerts.append("Presión ofensiva alta detectada en los datos disponibles.")
    if risk == "HIGH":
        alerts.append("Riesgo alto: reducir stake o evitar entrada automática.")
    if ev not in ["HIGH", "POSITIVE", "VALUE", "+EV"]:
        alerts.append("EV no confirmado como alto: evitar forzar la entrada.")

    cashout = "NO_CASHOUT_SIGNAL"
    if signal in ["NO_LIVE_ENTRY", "LIVE_WATCHLIST"] and risk == "HIGH":
        cashout = "CONSIDER_PROTECTION"
    elif signal in ["LIVE_STRONG_ENTRY", "LIVE_VALUE_ENTRY"]:
        cashout = "HOLD_OR_ENTER_CONTROLLED"

    return {
        "version": "V101_LIVE_TRADING_CENTER",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "match": f"{home} vs {away}",
        "minute": minute,
        "scoreline": scoreline,
        "pick": pick,
        "odds": odds,
        "shark_score": shark_score,
        "pressure": pressure,
        "momentum": momentum,
        "risk": risk,
        "ev": ev,
        "live_signal": signal,
        "alerts": alerts,
        "cashout_signal": cashout,
        "trading_reading": (
            f"Lectura live para {home} vs {away}: minuto {minute}, marcador {scoreline}, "
            f"pick {pick}, señal {signal}, riesgo {risk}, EV {ev}."
        )
    }

def build_live_center(matches):
    matches = matches or []
    readings = [build_live_trading_reading(m) for m in matches]
    strong = [r for r in readings if r["live_signal"] == "LIVE_STRONG_ENTRY"]
    value = [r for r in readings if r["live_signal"] == "LIVE_VALUE_ENTRY"]

    return {
        "version": "V101",
        "total_live_matches": len(readings),
        "strong_entries": len(strong),
        "value_entries": len(value),
        "readings": readings
    }
