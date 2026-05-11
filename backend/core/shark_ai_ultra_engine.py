from datetime import datetime

def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default

def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default

def classify_confidence(score):
    score = _safe_int(score)
    if score >= 88:
        return "ELITE"
    if score >= 78:
        return "HIGH"
    if score >= 65:
        return "MEDIUM"
    return "LOW"

def classify_entry(score, risk):
    score = _safe_int(score)
    risk = str(risk or "").upper()
    if score >= 85 and risk in ["LOW", "MEDIUM"]:
        return "STRONG_ENTRY"
    if score >= 75:
        return "VALUE_ENTRY"
    if score >= 60:
        return "WATCHLIST"
    return "NO_ENTRY"

def build_shark_ultra_reading(match):
    """
    Builds a professional SHARK AI reading from an existing real match/pick object.
    This function does not invent external data. It only interprets fields already present.
    """
    home = match.get("home_team") or match.get("home") or "Local"
    away = match.get("away_team") or match.get("away") or "Visitante"
    league = match.get("league") or "Liga no especificada"
    pick = match.get("pick") or match.get("prediction") or "Sin pick activo"
    score = _safe_int(match.get("shark_score") or match.get("score") or 0)
    risk = str(match.get("risk") or "MEDIUM").upper()
    ev = str(match.get("ev") or match.get("expected_value") or "N/A").upper()
    stake = match.get("stake") or "Sin stake"
    odds = match.get("odds") or match.get("price") or "N/A"
    momentum = match.get("momentum") or "Momentum no disponible"
    status = match.get("status") or "unknown"

    confidence = classify_confidence(score)
    entry_type = classify_entry(score, risk)

    reasons_for = []
    reasons_against = []

    if score >= 80:
        reasons_for.append("SHARK Score alto para el estándar premium.")
    elif score >= 65:
        reasons_for.append("SHARK Score aceptable, pero requiere control de stake.")
    else:
        reasons_against.append("SHARK Score insuficiente para entrada fuerte.")

    if risk == "LOW":
        reasons_for.append("Riesgo bajo dentro del modelo.")
    elif risk == "MEDIUM":
        reasons_for.append("Riesgo medio asumible si el value acompaña.")
    else:
        reasons_against.append("Riesgo alto: entrada solo para perfiles agresivos o live muy claro.")

    if ev in ["HIGH", "POSITIVE", "VALUE", "+EV"]:
        reasons_for.append("Value detectado por el sistema.")
    elif ev in ["LOW", "NEGATIVE", "-EV"]:
        reasons_against.append("EV débil o negativo: conviene esperar mejor cuota o confirmación live.")
    else:
        reasons_against.append("EV no confirmado: lectura incompleta para entrada automática.")

    if str(momentum).lower() not in ["", "none", "momentum no disponible"]:
        reasons_for.append("Momentum disponible para apoyar la lectura.")
    else:
        reasons_against.append("Momentum no disponible: menor confianza en entradas live.")

    recommendation = "NO ENTRAR"
    if entry_type == "STRONG_ENTRY":
        recommendation = "ENTRADA FUERTE CONTROLADA"
    elif entry_type == "VALUE_ENTRY":
        recommendation = "ENTRADA VALUE"
    elif entry_type == "WATCHLIST":
        recommendation = "SEGUIR EN WATCHLIST"

    return {
        "version": "V100_SHARK_AI_ULTRA",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "match": f"{home} vs {away}",
        "league": league,
        "status": status,
        "pick": pick,
        "odds": odds,
        "stake": stake,
        "risk": risk,
        "ev": ev,
        "shark_score": score,
        "confidence": confidence,
        "entry_type": entry_type,
        "recommendation": recommendation,
        "momentum": momentum,
        "reasons_for": reasons_for,
        "reasons_against": reasons_against,
        "tipster_reading": (
            f"Lectura SHARK ULTRA para {home} vs {away}: "
            f"pick {pick}, score {score}, riesgo {risk}, EV {ev}. "
            f"Recomendación: {recommendation}."
        )
    }

def build_chat_answer(question, context=None):
    q = (question or "").strip().lower()
    context = context or {}

    if not q:
        return {
            "answer": "Pregúntame por value, stake, riesgo, momentum o si conviene entrar a un pick concreto.",
            "mode": "empty"
        }

    if "stake" in q:
        return {
            "answer": "Para stake, SHARK AI Ultra prioriza score, EV y riesgo. Score alto con riesgo bajo/medio permite stake superior; si el EV no está claro, se baja stake o se deja en watchlist.",
            "mode": "stake"
        }

    if "riesgo" in q or "risk" in q:
        return {
            "answer": "El riesgo se interpreta junto al SHARK Score. Un pick con score alto pero riesgo alto no se trata como entrada fuerte; se controla stake o se espera confirmación live.",
            "mode": "risk"
        }

    if "value" in q or "ev" in q:
        return {
            "answer": "El value es la base. Sin EV positivo o señal clara, SHARK AI Ultra no fuerza entradas aunque el partido parezca atractivo.",
            "mode": "value"
        }

    if "momentum" in q or "live" in q:
        return {
            "answer": "En live, el momentum manda. SHARK AI Ultra busca cambios de presión, ritmo, dominio y señales de entrada antes de lanzar una alerta.",
            "mode": "live"
        }

    return {
        "answer": "SHARK AI Ultra responde como analista premium: revisa score, EV, riesgo, stake y momentum antes de recomendar entrar, esperar o descartar.",
        "mode": "general"
    }
