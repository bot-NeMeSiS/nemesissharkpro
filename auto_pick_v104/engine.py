
from datetime import datetime

def _num(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default

def _txt(value, default=""):
    return str(value if value is not None else default).strip()

def normalize_candidate(match):
    home = match.get("home_team") or match.get("home") or match.get("team_home") or "Local"
    away = match.get("away_team") or match.get("away") or match.get("team_away") or "Visitante"
    league = match.get("league") or match.get("competition") or "Liga no especificada"
    sport = match.get("sport") or "football"
    pick = match.get("pick") or match.get("prediction") or match.get("market") or "Sin pick activo"

    odds = _num(match.get("odds") or match.get("price") or match.get("quota"), 0)
    base_score = _num(match.get("shark_score") or match.get("score") or match.get("confidence"), 0)
    ev_raw = _txt(match.get("ev") or match.get("expected_value") or match.get("value"), "N/A").upper()
    risk = _txt(match.get("risk"), "MEDIUM").upper()
    momentum = _txt(match.get("momentum"), "")
    pressure = _num(match.get("pressure") or match.get("attack_pressure"), 0)
    status = _txt(match.get("status"), "upcoming")

    score = base_score

    if ev_raw in ["HIGH", "POSITIVE", "VALUE", "+EV", "ALTO"]:
        score += 8
    elif ev_raw in ["LOW", "NEGATIVE", "-EV", "BAJO"]:
        score -= 10

    if odds >= 1.40 and odds <= 2.40:
        score += 5
    elif odds > 3.50:
        score -= 5

    if risk == "LOW":
        score += 5
    elif risk == "HIGH":
        score -= 12

    if pressure >= 75:
        score += 5

    if any(x in momentum.lower() for x in ["high", "alto", "positivo", "domin"]):
        score += 5

    score = max(0, min(100, round(score, 2)))

    if score >= 88 and risk in ["LOW", "MEDIUM"]:
        tier = "AUTO_PICK_STRONG"
        action = "CANDIDATO FUERTE"
    elif score >= 78:
        tier = "AUTO_PICK_VALUE"
        action = "CANDIDATO VALUE"
    elif score >= 68:
        tier = "WATCHLIST"
        action = "VIGILAR"
    else:
        tier = "REJECTED"
        action = "DESCARTAR"

    reasons = []
    blockers = []

    if base_score >= 75:
        reasons.append("Base SHARK Score sólida.")
    else:
        blockers.append("Base SHARK Score todavía baja para entrada automática.")

    if ev_raw in ["HIGH", "POSITIVE", "VALUE", "+EV", "ALTO"]:
        reasons.append("Value positivo detectado en el Real Core.")
    else:
        blockers.append("EV no confirmado como alto.")

    if risk in ["LOW", "MEDIUM"]:
        reasons.append("Riesgo compatible con entrada controlada.")
    else:
        blockers.append("Riesgo alto: no se fuerza entrada automática.")

    if odds:
        if 1.40 <= odds <= 2.40:
            reasons.append("Cuota en rango saludable para sistema premium.")
        elif odds > 3.50:
            blockers.append("Cuota alta: volatilidad elevada.")

    return {
        "match_id": match.get("id") or match.get("match_id") or f"{home}-{away}".replace(" ", "-").lower(),
        "match": f"{home} vs {away}",
        "home_team": home,
        "away_team": away,
        "league": league,
        "sport": sport,
        "pick": pick,
        "odds": odds or "N/A",
        "risk": risk,
        "ev": ev_raw,
        "momentum": momentum or "N/A",
        "pressure": pressure,
        "status": status,
        "base_score": base_score,
        "auto_pick_score": score,
        "tier": tier,
        "action": action,
        "reasons": reasons,
        "blockers": blockers,
    }

def scan_auto_picks(matches, min_score=68, max_results=20, include_rejected=False):
    candidates = [normalize_candidate(m) for m in (matches or [])]
    if not include_rejected:
        candidates = [c for c in candidates if c["auto_pick_score"] >= float(min_score) and c["tier"] != "REJECTED"]

    candidates = sorted(candidates, key=lambda x: x["auto_pick_score"], reverse=True)
    candidates = candidates[:int(max_results or 20)]

    strong = [c for c in candidates if c["tier"] == "AUTO_PICK_STRONG"]
    value = [c for c in candidates if c["tier"] == "AUTO_PICK_VALUE"]
    watch = [c for c in candidates if c["tier"] == "WATCHLIST"]

    return {
        "version": "V104_AUTO_PICK_ENGINE",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_input_matches": len(matches or []),
        "total_candidates": len(candidates),
        "strong_candidates": len(strong),
        "value_candidates": len(value),
        "watchlist": len(watch),
        "candidates": candidates,
        "rules": {
            "min_score": min_score,
            "max_results": max_results,
            "include_rejected": include_rejected,
            "data_policy": "No inventa datos; solo puntúa campos existentes del Real Core/feed."
        }
    }

def explain_candidate(candidate):
    return {
        "match": candidate.get("match"),
        "summary": f"{candidate.get('match')} queda como {candidate.get('action')} con Auto Pick Score {candidate.get('auto_pick_score')}.",
        "reasons": candidate.get("reasons", []),
        "blockers": candidate.get("blockers", []),
        "final_action": candidate.get("action"),
        "tier": candidate.get("tier")
    }
