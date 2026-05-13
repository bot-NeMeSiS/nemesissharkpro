
"""
NeMeSiS SHARK PRO V87
SHARK AI Pick Quality Engine

Objetivo:
- Mejorar calidad visible de picks.
- Explicaciones humanas.
- Value/risk/stake más claro.
- Filtrar picks débiles.
- Quality score para admin.
"""

import os
from datetime import datetime


MIN_PUBLIC_SCORE = int(os.getenv("V87_MIN_PUBLIC_PICK_SCORE", "68"))
MIN_ELITE_SCORE = int(os.getenv("V87_MIN_ELITE_PICK_SCORE", "82"))


def safe_float(value, default=0.0):
    try:
        if value in (None, "", "-"):
            return default
        return float(str(value).replace("%", "").replace("+", ""))
    except Exception:
        return default


def safe_int(value, default=0):
    try:
        return int(round(safe_float(value, default)))
    except Exception:
        return default


def infer_risk(odds=None, market=None, score=None):
    odds_f = safe_float(odds, 0)
    score_i = safe_int(score, 0)
    market_text = str(market or "").lower()

    risk_points = 0

    if odds_f >= 5:
        risk_points += 35
    elif odds_f >= 3.5:
        risk_points += 25
    elif odds_f >= 2.4:
        risk_points += 15
    else:
        risk_points += 5

    if "hándicap" in market_text or "handicap" in market_text:
        risk_points += 12
    if "draw" in market_text or "empate" in market_text:
        risk_points += 18
    if "over" in market_text or "under" in market_text or "total" in market_text:
        risk_points += 8

    if score_i >= 85:
        risk_points -= 12
    elif score_i < 70:
        risk_points += 12

    if risk_points >= 38:
        return "Alto"
    if risk_points >= 20:
        return "Medio"
    return "Bajo"


def confidence_label(score):
    score = safe_int(score, 0)
    if score >= 90:
        return "ELITE"
    if score >= 82:
        return "MUY ALTA"
    if score >= 74:
        return "ALTA"
    if score >= 65:
        return "MEDIA"
    return "BAJA"


def quality_label(score):
    score = safe_int(score, 0)
    if score >= 90:
        return "Pick premium"
    if score >= 82:
        return "Pick fuerte"
    if score >= 74:
        return "Pick válido"
    if score >= 65:
        return "Pick prudente"
    return "Descartar"


def recommended_stake(score, risk, ev=None):
    score_i = safe_int(score, 0)
    ev_f = safe_float(ev, 0)
    risk = str(risk or "").lower()

    stake = 1.0

    if score_i >= 90:
        stake += 1.2
    elif score_i >= 82:
        stake += 0.8
    elif score_i >= 74:
        stake += 0.4

    if ev_f >= 6:
        stake += 0.5
    elif ev_f >= 3:
        stake += 0.2

    if "alto" in risk:
        stake -= 0.8
    elif "medio" in risk:
        stake -= 0.3

    stake = max(0.5, min(stake, 3.5))
    return f"{stake:.1f}%".replace(".0", "")


def pick_status(score, risk, ev=None):
    score_i = safe_int(score, 0)
    ev_f = safe_float(ev, 0)
    risk_l = str(risk or "").lower()

    if score_i < MIN_PUBLIC_SCORE:
        return "REJECTED"
    if "alto" in risk_l and score_i < 82:
        return "CAUTION"
    if ev_f < 0 and score_i < 80:
        return "CAUTION"
    if score_i >= MIN_ELITE_SCORE:
        return "PREMIUM"
    return "PUBLIC"


def build_human_reason(pick):
    home = pick.get("home_team") or pick.get("home") or "local"
    away = pick.get("away_team") or pick.get("away") or "visitante"
    market = pick.get("market") or pick.get("pick") or "mercado seleccionado"
    odds = pick.get("odds") or pick.get("cuota") or "-"
    score = pick.get("shark_score") or pick.get("score") or 0
    ev = pick.get("ev") or pick.get("expected_value") or None
    risk = pick.get("v87_risk") or infer_risk(odds, market, score)

    pieces = [
        f"SHARK AI detecta valor en {market}",
        f"porque el cruce {home} vs {away} encaja con un perfil de cuota interesante",
        f"con score {score}% y riesgo {str(risk).lower()}",
    ]

    if ev not in (None, "", "-"):
        pieces.append(f"El valor esperado estimado es {ev}")

    pieces.append(f"La cuota {odds} exige stake controlado y evitar sobreexposición.")

    return ". ".join(pieces)


def enrich_pick(pick):
    if not isinstance(pick, dict):
        return pick

    enriched = dict(pick)

    score = (
        enriched.get("shark_score")
        or enriched.get("score")
        or enriched.get("confidence")
        or 70
    )
    odds = enriched.get("odds") or enriched.get("cuota") or enriched.get("price") or 2.0
    ev = enriched.get("ev") or enriched.get("expected_value") or None
    market = enriched.get("market") or enriched.get("pick") or "Mercado seleccionado"

    risk = infer_risk(odds, market, score)
    status = pick_status(score, risk, ev)

    enriched.update({
        "v87_score": safe_int(score, 0),
        "v87_confidence": confidence_label(score),
        "v87_quality_label": quality_label(score),
        "v87_risk": risk,
        "v87_stake": recommended_stake(score, risk, ev),
        "v87_status": status,
        "v87_is_public": status != "REJECTED",
        "v87_is_premium": status == "PREMIUM",
        "v87_reason": enriched.get("ai_reason") or enriched.get("reason") or build_human_reason(enriched),
        "v87_generated_at": datetime.utcnow().isoformat(),
    })

    return enriched


def filter_picks(picks, hide_rejected=True):
    if not isinstance(picks, list):
        return []
    out = []
    for p in picks:
        item = enrich_pick(p)
        if hide_rejected and not item.get("v87_is_public"):
            continue
        out.append(item)
    return out


def quality_report(picks):
    enriched = [enrich_pick(p) for p in (picks if isinstance(picks, list) else [])]
    total = len(enriched)
    public = len([p for p in enriched if p.get("v87_is_public")])
    premium = len([p for p in enriched if p.get("v87_is_premium")])
    rejected = total - public
    avg = round(sum([p.get("v87_score", 0) for p in enriched]) / total, 2) if total else 0

    return {
        "total": total,
        "public": public,
        "premium": premium,
        "rejected": rejected,
        "avg_score": avg,
        "status": "QUALITY OK" if total and rejected == 0 else ("QUALITY MIXTA" if total else "SIN PICKS"),
        "picks": enriched,
    }


def demo_picks():
    return [
        {
            "league": "LaLiga",
            "home_team": "Rayo Vallecano",
            "away_team": "Girona",
            "market": "Gana Hándicap: Rayo Vallecano",
            "odds": 3.80,
            "shark_score": 84,
            "ev": "+4.9%",
        },
        {
            "league": "Serie A",
            "home_team": "Cagliari",
            "away_team": "Udinese",
            "market": "Gana Hándicap: Cagliari",
            "odds": 4.55,
            "shark_score": 81,
            "ev": "+2.1%",
        },
        {
            "league": "LaLiga",
            "home_team": "Augsburg",
            "away_team": "Borussia Monchengladbach",
            "market": "Draw gana",
            "odds": 4.00,
            "shark_score": 62,
            "ev": "-1.4%",
        },
    ]


def get_v87_status():
    report = quality_report(demo_picks())
    return {
        "version": "V87",
        "status": "SHARK AI PICK QUALITY ACTIVO",
        "min_public_score": MIN_PUBLIC_SCORE,
        "min_elite_score": MIN_ELITE_SCORE,
        "report": report,
        "modules": [
            "Explicación humana SHARK AI",
            "Risk engine",
            "Stake recomendado",
            "Filtro de picks débiles",
            "Etiquetas de confianza",
            "Quality report admin",
        ],
    }
