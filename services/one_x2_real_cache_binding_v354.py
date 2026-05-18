
def _load_cached():
    try:
        from services.real_provider_connector_v353 import cached_odds
        return cached_odds()
    except Exception as exc:
        return {"ok": False, "matches": [], "error": str(exc), "low_data": True}

def _score_match(match):
    odds = match.get("odds_1x2") or {}
    values = [odds.get("1"), odds.get("X"), odds.get("2")]
    real_values = [v for v in values if isinstance(v, (int,float))]
    if len(real_values) < 2:
        return 0
    # simple consistency score, not betting advice
    spread = max(real_values) - min(real_values)
    return max(30, min(92, int(86 - spread * 6)))

def build_1x2_recommendations(limit=12):
    data = _load_cached()
    matches = data.get("matches") or []
    recs = []
    for m in matches[:limit]:
        odds = m.get("odds_1x2") or {}
        best_key = None
        best_val = None
        for k in ["1","X","2"]:
            v = odds.get(k)
            if isinstance(v, (int,float)) and (best_val is None or v < best_val):
                best_key, best_val = k, v
        recs.append({
            "id": m.get("id"),
            "home": m.get("home"),
            "away": m.get("away"),
            "league": m.get("league"),
            "minute": (m.get("minute") or {}).get("text", "Pre"),
            "score": (m.get("score") or {}).get("text", "vs"),
            "odds_1x2": odds,
            "recommended": best_key or "LOW_DATA",
            "confidence": _score_match(m),
            "source": m.get("source", "provider_cache_v353"),
            "low_data": best_key is None,
            "reason": "Cuotas reales cacheadas desde proveedor" if best_key else "Faltan cuotas reales suficientes"
        })
    return {
        "ok": bool(recs),
        "version": "V354",
        "source_ok": data.get("ok", False),
        "from_cache": True,
        "count": len(recs),
        "recommendations": recs,
        "low_data": not bool(recs),
        "message": "Sin cuotas cacheadas. Ejecuta /api/provider/refresh/odds-v353" if not recs else "1X2 enlazado al caché real V353",
        "real_only": True
    }

def one_x2_binding_status():
    return {
        "ok": True,
        "version": "V354",
        "name": "1X2_REAL_CACHE_BINDING_PRO",
        "uses": ["provider_cache_v353", "The Odds API connector", "LOW DATA fallback"],
        "routes": [
            "/api/client/1x2/real-cache-v354",
            "/cliente/1x2-real-cache",
            "/api/provider/refresh/odds-v353",
            "/api/provider/cache/odds-v353"
        ],
        "real_only": True
    }
