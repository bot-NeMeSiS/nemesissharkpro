
from datetime import datetime

def get_core_feed(force=False):
    try:
        from core.real_core_engine import RealCoreEngine
        return RealCoreEngine.fetch(force=force)
    except Exception as exc:
        return {
            "ok": False, "version": "V92", "source": "none",
            "message": "Real Core no disponible. Panel cliente en modo seguro.",
            "error": str(exc), "matches": [], "picks": [],
            "buckets": {"live": [], "today": [], "upcoming": []},
            "counts": {"total": 0, "live": 0, "today": 0, "upcoming": 0},
            "generated_at": datetime.utcnow().isoformat(),
        }

def safe_user_context():
    return {
        "name": "Cliente", "plan": "ELITE", "plan_status": "Activo",
        "bankroll": "10.00€", "telegram": "OFF", "roi": "Sin datos",
        "winrate": "Sin datos", "closed_picks": 0, "risk_profile": "Conservador",
        "sport": "Fútbol", "favorite_league": "Sin configurar",
    }

def pick_quality(match):
    score = int(match.get("shark_score") or match.get("quality_score") or 0)
    if score >= 88: return "TOP"
    if score >= 78: return "Buena"
    if score >= 70: return "Media"
    return "Pendiente"

def card_vm(match):
    return {
        "id": match.get("id"),
        "league": match.get("league", "Competición"),
        "home": match.get("home_team", ""),
        "away": match.get("away_team", ""),
        "date": match.get("date", "SIN FECHA"),
        "date_full": match.get("date_full", ""),
        "time": match.get("time", "--:--"),
        "status": match.get("status", "PROGRAMADO"),
        "relative": match.get("relative", ""),
        "market": match.get("market", "Mercado pendiente"),
        "odds": match.get("odds") or "Pendiente",
        "bookmaker": match.get("bookmaker") or "Bookmaker pendiente",
        "source": match.get("source") or "real",
        "score": match.get("shark_score") or match.get("quality_score") or 0,
        "risk": match.get("risk") or "Pendiente",
        "stake": match.get("stake") or "Pendiente",
        "quality": pick_quality(match),
        "ev": match.get("ev") or "Pendiente",
        "detail_url": f"/partido/{match.get('id')}",
    }

def build_client_dashboard(force=False):
    feed = get_core_feed(force=force)
    user = safe_user_context()
    matches = [card_vm(m) for m in feed.get("matches", [])]
    live = [card_vm(m) for m in feed.get("buckets", {}).get("live", [])]
    today = [card_vm(m) for m in feed.get("buckets", {}).get("today", [])]
    upcoming = [card_vm(m) for m in feed.get("buckets", {}).get("upcoming", [])]
    recommended = sorted(matches, key=lambda m: int(m.get("score") or 0), reverse=True)[:8]
    return {
        "version": "V92", "feed": feed, "user": user,
        "counts": feed.get("counts", {"total": 0, "live": 0, "today": 0, "upcoming": 0}),
        "recommended": recommended, "live": live, "today": today,
        "upcoming": upcoming, "all_matches": matches,
        "health": {"real_core": feed.get("ok", False), "source": feed.get("source", "none"),
                   "no_demo": True, "safe_empty": True, "message": feed.get("message"), "error": feed.get("error")},
    }
