
def _one_x2(limit=8):
    try:
        from services.one_x2_real_cache_binding_v354 import build_1x2_recommendations
        return build_1x2_recommendations(limit=limit)
    except Exception as exc:
        return {"ok": False, "recommendations": [], "error": str(exc), "low_data": True}

def match_center_cards(limit=8):
    data = _one_x2(limit=limit)
    recs = data.get("recommendations") or []
    cards = []
    for r in recs:
        odds = r.get("odds_1x2") or {}
        cards.append({
            "id": r.get("id"),
            "title": f"{r.get('home','Local')} vs {r.get('away','Visitante')}",
            "home": r.get("home"),
            "away": r.get("away"),
            "league": r.get("league"),
            "minute": r.get("minute") or "Pre",
            "score": r.get("score") or "vs",
            "recommended_1x2": r.get("recommended") or "LOW_DATA",
            "confidence": r.get("confidence") or 0,
            "odds": odds,
            "shark_read": "Contexto revisable para 1X2 real" if not r.get("low_data") else "LOW DATA: faltan cuotas suficientes",
            "risk_label": "Moderado" if (r.get("confidence") or 0) >= 60 else "Esperar",
            "low_data": bool(r.get("low_data")),
            "source": r.get("source", "provider_cache_v353")
        })
    return {
        "ok": bool(cards),
        "version": "V355",
        "count": len(cards),
        "cards": cards,
        "low_data": not bool(cards),
        "message": "Match Center enlazado a caché real V354" if cards else "Sin datos cacheados. Ejecuta /api/provider/refresh/odds-v353",
        "real_only": True
    }

def match_center_binding_status():
    return {
        "ok": True,
        "version": "V355",
        "name": "MATCH_CENTER_REAL_DATA_BINDING_PRO",
        "uses": ["V353 provider cache", "V354 1X2 real recommendations", "LOW DATA fallback"],
        "routes": [
            "/cliente/match-center-real",
            "/api/client/match-center/real-data-v355",
            "/api/provider/refresh/odds-v353",
            "/api/client/1x2/real-cache-v354"
        ],
        "real_only": True
    }
