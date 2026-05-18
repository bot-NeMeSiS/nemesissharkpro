
def _match_cards(limit=6):
    try:
        from services.match_center_real_data_binding_v355 import match_center_cards
        return match_center_cards(limit=limit)
    except Exception as exc:
        return {"ok": False, "cards": [], "error": str(exc), "low_data": True}

def _analyst_text(card):
    if card.get("low_data"):
        return "LOW DATA: SHARK esperaría a tener cuotas reales suficientes antes de valorar este partido."
    rec = card.get("recommended_1x2") or "LOW_DATA"
    conf = int(card.get("confidence") or 0)
    risk = card.get("risk_label") or "Moderado"
    home = card.get("home") or "Local"
    away = card.get("away") or "Visitante"
    if conf >= 75:
        tone = "lectura bastante sólida"
    elif conf >= 60:
        tone = "lectura interesante pero no agresiva"
    else:
        tone = "lectura débil; mejor esperar"
    return f"SHARK ve {tone} en {home} vs {away}. Señal 1X2 marcada: {rec}. Riesgo: {risk}. Confianza: {conf}/100."

def shark_real_analysis(limit=6):
    data = _match_cards(limit=limit)
    cards = data.get("cards") or []
    analyses = []
    for c in cards:
        analyses.append({
            "match_id": c.get("id"),
            "title": c.get("title"),
            "league": c.get("league"),
            "score": c.get("score"),
            "minute": c.get("minute"),
            "recommended_1x2": c.get("recommended_1x2"),
            "confidence": c.get("confidence"),
            "risk_label": c.get("risk_label"),
            "analysis": _analyst_text(c),
            "low_data": bool(c.get("low_data")),
            "source": "V355_MATCH_CENTER_REAL_DATA"
        })
    return {
        "ok": bool(analyses),
        "version": "V356",
        "count": len(analyses),
        "analyses": analyses,
        "low_data": not bool(analyses),
        "message": "SHARK enlazado a Match Center real V355" if analyses else "Sin datos reales. Ejecuta /api/provider/refresh/odds-v353",
        "real_only": True
    }

def shark_binding_status():
    return {
        "ok": True,
        "version": "V356",
        "name": "SHARK_REAL_DATA_ANALYST_BINDING_PRO",
        "uses": ["V353 provider cache", "V354 1X2", "V355 Match Center real"],
        "routes": [
            "/cliente/shark-real-analyst",
            "/api/shark/real-analysis-v356",
            "/api/shark/real-binding-status-v356"
        ],
        "real_only": True
    }
