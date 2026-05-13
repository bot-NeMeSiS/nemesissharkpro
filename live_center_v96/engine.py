from datetime import datetime


def _score(match):
    try:
        return int(float(match.get("shark_score") or match.get("quality_score") or 0))
    except Exception:
        return 0


def _live_state(match):
    score = _score(match)
    status = (match.get("status") or "").upper()
    if status == "EN DIRECTO" and score >= 85:
        return "LIVE VALUE"
    if status == "EN DIRECTO":
        return "LIVE WATCH"
    if score >= 88:
        return "PREMIUM WATCH"
    if score >= 78:
        return "VALUE WATCH"
    return "OBSERVAR"


def build_live_center(feed):
    matches = feed.get("matches", []) if isinstance(feed, dict) else []
    buckets = feed.get("buckets", {}) if isinstance(feed, dict) else {}
    ranked = sorted(matches, key=lambda m: _score(m), reverse=True)

    cards = []
    for match in ranked[:18]:
        cards.append({
            "id": match.get("id"),
            "league": match.get("league"),
            "home_team": match.get("home_team"),
            "away_team": match.get("away_team"),
            "status": match.get("status"),
            "date": match.get("date"),
            "time": match.get("time"),
            "selection": match.get("selection") or match.get("market"),
            "odds": match.get("odds"),
            "bookmaker": match.get("bookmaker"),
            "shark_score": _score(match),
            "risk": match.get("risk"),
            "stake": match.get("stake"),
            "state": _live_state(match),
            "detail_url": f"/partido/{match.get('id')}",
        })

    strong = [c for c in cards if int(c.get("shark_score") or 0) >= 85]
    live = buckets.get("live", [])

    return {
        "version": "V96",
        "system": "SHARK LIVE CENTER PRO",
        "real_core_ok": bool(feed.get("ok")),
        "message": feed.get("message"),
        "error": feed.get("error"),
        "counts": feed.get("counts", {}),
        "cards": cards,
        "alerts": [
            {
                "type": "HIGH_VALUE",
                "title": "Picks fuertes detectados",
                "value": len(strong),
                "active": bool(strong),
            },
            {
                "type": "LIVE_MONITOR",
                "title": "Partidos live reales",
                "value": len(live),
                "active": bool(live),
            },
        ],
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
