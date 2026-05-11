
from datetime import datetime

def build_alert_from_candidate(candidate):
    score = float(candidate.get("auto_pick_score") or 0)
    tier = candidate.get("tier") or "UNKNOWN"
    risk = candidate.get("risk") or "MEDIUM"

    priority = "LOW"
    if tier == "AUTO_PICK_STRONG" and score >= 88 and risk in ["LOW", "MEDIUM"]:
        priority = "CRITICAL"
    elif tier in ["AUTO_PICK_STRONG", "AUTO_PICK_VALUE"]:
        priority = "HIGH"
    elif tier == "WATCHLIST":
        priority = "MEDIUM"

    return {
        "version": "V105_AUTO_ALERTS_ENGINE",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "priority": priority,
        "tier": tier,
        "match": candidate.get("match"),
        "pick": candidate.get("pick"),
        "odds": candidate.get("odds"),
        "risk": risk,
        "ev": candidate.get("ev"),
        "score": score,
        "title": f"SHARK ALERT · {priority}",
        "message": (
            f"🦈 SHARK ALERT\\n\\n"
            f"Partido: {candidate.get('match')}\\n"
            f"Pick: {candidate.get('pick')}\\n"
            f"Score: {score}\\n"
            f"Riesgo: {risk}\\n"
            f"EV: {candidate.get('ev')}\\n"
            f"Acción: {candidate.get('action')}"
        ),
        "requires_admin_approval": priority in ["CRITICAL", "HIGH"],
        "channels": {
            "telegram_ready": True,
            "dashboard_ready": True,
            "push_ready": True
        },
        "reasons": candidate.get("reasons", []),
        "blockers": candidate.get("blockers", [])
    }

def build_alert_batch(candidates, min_priority="MEDIUM"):
    order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
    min_rank = order.get(min_priority, 1)

    alerts = [build_alert_from_candidate(c) for c in (candidates or [])]
    alerts = [a for a in alerts if order.get(a["priority"], 0) >= min_rank]
    alerts = sorted(alerts, key=lambda a: order.get(a["priority"], 0), reverse=True)

    return {
        "version": "V105",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_alerts": len(alerts),
        "critical": len([a for a in alerts if a["priority"] == "CRITICAL"]),
        "high": len([a for a in alerts if a["priority"] == "HIGH"]),
        "medium": len([a for a in alerts if a["priority"] == "MEDIUM"]),
        "alerts": alerts,
        "policy": "No envía automáticamente sin aprobación admin; deja la alerta lista para Telegram/dashboard."
    }
