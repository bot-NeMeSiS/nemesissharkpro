
"""
NeMeSiS SHARK PRO V79
SHARK AI Real Evolution Engine

Motor ligero, sin dependencias pesadas, preparado para Render.
No es ML pesado todavía: es una base adaptativa real para evolucionar hacia modelos propios.
"""

import math
import sqlite3
from datetime import datetime
from collections import defaultdict


DB_PATH = "nemesis.db"
MODEL_VERSION = "V79_RULE_BASED_EVOLUTION"


def get_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def now_iso():
    return datetime.utcnow().isoformat()


def clamp(value, low=1, high=99):
    return max(low, min(high, round(float(value), 2)))


def odds_value_component(odds):
    try:
        odds = float(odds or 0)
    except Exception:
        odds = 0

    if odds <= 0:
        return 0

    if 1.45 <= odds <= 2.25:
        return 12
    if 2.26 <= odds <= 3.25:
        return 8
    if 1.20 <= odds < 1.45:
        return 3
    if odds > 4.5:
        return -10
    return 0


def risk_from_odds(odds):
    try:
        odds = float(odds or 0)
    except Exception:
        odds = 0

    if odds <= 0:
        return 50
    if odds < 1.35:
        return 25
    if odds <= 2.25:
        return 35
    if odds <= 3.25:
        return 55
    if odds <= 4.5:
        return 72
    return 88


def pattern_key(sport=None, league=None, market=None):
    return f"{sport or 'UNKNOWN'}::{league or 'UNKNOWN'}::{market or 'UNKNOWN'}".upper()


def get_pattern_adjustment(sport=None, league=None, market=None, db_path=DB_PATH):
    conn = get_db(db_path)
    key = pattern_key(sport, league, market)
    row = conn.execute("""
        SELECT score_adjustment, reliability, sample_size
        FROM shark_ai_pattern_memory
        WHERE pattern_key=?
    """, (key,)).fetchone()
    conn.close()

    if not row:
        return {
            "adjustment": 0,
            "reliability": "UNKNOWN",
            "sample_size": 0,
        }

    return {
        "adjustment": float(row["score_adjustment"] or 0),
        "reliability": row["reliability"] or "UNKNOWN",
        "sample_size": int(row["sample_size"] or 0),
    }


def confidence_from_score(score, risk_score, reliability="UNKNOWN"):
    score = float(score or 0)
    risk_score = float(risk_score or 0)

    if reliability == "LOW":
        score -= 6
    elif reliability == "HIGH":
        score += 4
    elif reliability == "ELITE":
        score += 7

    if risk_score >= 80:
        score -= 12
    elif risk_score >= 65:
        score -= 6

    if score >= 88:
        return "ELITE"
    if score >= 76:
        return "ALTA"
    if score >= 62:
        return "MEDIA"
    return "BAJA"


def prediction_probability(score, risk_score):
    """
    Conversión simple a probabilidad interpretativa.
    """
    score = float(score or 0)
    risk_score = float(risk_score or 0)
    raw = score - (risk_score * 0.22)
    probability = 1 / (1 + math.exp(-(raw - 50) / 11))
    return clamp(probability * 100, 1, 96)


def build_ai_reason(payload, adaptive_score, value_score, risk_score, confidence, pattern):
    reasons = []

    if value_score >= 10:
        reasons.append("Value detectado en rango de cuota óptimo")
    elif value_score < 0:
        reasons.append("Cuota con riesgo elevado o rango poco eficiente")

    if pattern["sample_size"] >= 10:
        reasons.append(f"Patrón histórico con fiabilidad {pattern['reliability']}")
    else:
        reasons.append("Patrón aún con muestra limitada")

    if adaptive_score >= 80:
        reasons.append("Score adaptativo fuerte tras ajustes históricos")
    elif adaptive_score < 60:
        reasons.append("Score adaptativo moderado/bajo, se recomienda cautela")

    if risk_score >= 75:
        reasons.append("Volatilidad alta detectada")
    elif risk_score <= 40:
        reasons.append("Riesgo controlado según mercado y cuota")

    reasons.append(f"Confianza final: {confidence}")

    return " · ".join(reasons)


def predict_pick(payload, db_path=DB_PATH, save=True):
    """
    payload esperado:
    {
      pick_id, sport, league, match_name, market, selection,
      odds, shark_score/base_score
    }
    """
    base_score = float(payload.get("shark_score") or payload.get("base_score") or 65)
    odds = float(payload.get("odds") or 0)

    sport = payload.get("sport") or "General"
    league = payload.get("league") or "General"
    market = payload.get("market") or "General"

    value_score = odds_value_component(odds)
    risk_score = risk_from_odds(odds)
    pattern = get_pattern_adjustment(sport, league, market, db_path)

    adaptive_score = clamp(base_score + value_score + pattern["adjustment"] - (risk_score * 0.08))
    confidence = confidence_from_score(adaptive_score, risk_score, pattern["reliability"])
    probability = prediction_probability(adaptive_score, risk_score)

    if confidence in ("ELITE", "ALTA") and probability >= 62:
        label = "APROBADO"
    elif confidence == "MEDIA" and probability >= 54:
        label = "OBSERVAR"
    else:
        label = "RECHAZADO"

    ai_reason = build_ai_reason(payload, adaptive_score, value_score, risk_score, confidence, pattern)

    result = {
        "pick_id": payload.get("pick_id"),
        "sport": sport,
        "league": league,
        "match_name": payload.get("match_name") or "",
        "market": market,
        "selection": payload.get("selection") or "",
        "odds": odds,
        "base_score": base_score,
        "adaptive_score": adaptive_score,
        "value_score": value_score,
        "risk_score": risk_score,
        "confidence_level": confidence,
        "prediction_label": label,
        "prediction_probability": probability,
        "ai_reason": ai_reason,
        "pattern": pattern,
        "model_version": MODEL_VERSION,
    }

    if save:
        conn = get_db(db_path)
        conn.execute("""
        INSERT INTO shark_ai_predictions (
            pick_id, sport, league, match_name, market, selection,
            odds, base_score, adaptive_score, value_score, risk_score,
            confidence_level, prediction_label, prediction_probability,
            ai_reason, model_version, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result["pick_id"], sport, league, result["match_name"], market, result["selection"],
            odds, base_score, adaptive_score, value_score, risk_score,
            confidence, label, probability, ai_reason, MODEL_VERSION, now_iso()
        ))
        conn.commit()
        conn.close()

        if label == "RECHAZADO":
            remember_rejected_signal(sport, league, market, ai_reason, risk_score, db_path)

    return result


def remember_rejected_signal(sport, league, market, reason, risk_score, db_path=DB_PATH):
    conn = get_db(db_path)
    conn.execute("""
    INSERT INTO shark_ai_rejected_signals (
        signal_type, sport, league, market, reason, risk_score, created_at
    ) VALUES ('PICK_REJECTED', ?, ?, ?, ?, ?, ?)
    """, (sport, league, market, reason, risk_score, now_iso()))
    conn.commit()
    conn.close()


def rebuild_pattern_memory(db_path=DB_PATH):
    """
    Reconstruye patrones desde shark_ai_predictions y, si existe, shark_ml_dataset.
    """
    conn = get_db(db_path)

    rows = conn.execute("""
        SELECT sport, league, market, odds, adaptive_score, result, profit_loss
        FROM shark_ai_predictions
        WHERE result IS NOT NULL
    """).fetchall()

    try:
        ml_rows = conn.execute("""
            SELECT sport, league, market, odds, shark_score AS adaptive_score, result, profit_loss
            FROM shark_ml_dataset
            WHERE result IS NOT NULL
        """).fetchall()
        rows = list(rows) + list(ml_rows)
    except Exception:
        pass

    grouped = defaultdict(list)
    for row in rows:
        grouped[pattern_key(row["sport"], row["league"], row["market"])].append(row)

    updated = 0

    for key, group in grouped.items():
        sample = len(group)
        wins = len([r for r in group if str(r["result"]).upper() == "WIN"])
        losses = len([r for r in group if str(r["result"]).upper() == "LOSS"])
        voids = len([r for r in group if str(r["result"]).upper() == "VOID"])

        valid = max(sample - voids, 1)
        win_rate = round((wins / valid) * 100, 2)
        profit = sum(float(r["profit_loss"] or 0) for r in group)
        roi = round((profit / max(sample, 1)) * 100, 2)
        avg_odds = round(sum(float(r["odds"] or 0) for r in group) / max(sample, 1), 2)
        avg_score = round(sum(float(r["adaptive_score"] or 0) for r in group) / max(sample, 1), 2)

        if sample >= 30 and win_rate >= 62 and roi >= 8:
            reliability = "ELITE"
            adjustment = 10
        elif sample >= 12 and win_rate >= 56 and roi >= 3:
            reliability = "HIGH"
            adjustment = 6
        elif sample >= 8 and (win_rate < 45 or roi < -8):
            reliability = "LOW"
            adjustment = -9
        elif sample >= 5:
            reliability = "MEDIUM"
            adjustment = 2 if roi > 0 else -2
        else:
            reliability = "UNKNOWN"
            adjustment = 0

        conn.execute("""
        INSERT INTO shark_ai_pattern_memory (
            pattern_key, pattern_type, sample_size, wins, losses, voids,
            avg_odds, avg_score, win_rate, roi, reliability, score_adjustment, updated_at
        ) VALUES (?, 'SPORT_LEAGUE_MARKET', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(pattern_key) DO UPDATE SET
            sample_size=excluded.sample_size,
            wins=excluded.wins,
            losses=excluded.losses,
            voids=excluded.voids,
            avg_odds=excluded.avg_odds,
            avg_score=excluded.avg_score,
            win_rate=excluded.win_rate,
            roi=excluded.roi,
            reliability=excluded.reliability,
            score_adjustment=excluded.score_adjustment,
            updated_at=excluded.updated_at
        """, (
            key, sample, wins, losses, voids, avg_odds, avg_score,
            win_rate, roi, reliability, adjustment, now_iso()
        ))
        updated += 1

    conn.commit()
    conn.close()

    return {
        "ok": True,
        "patterns_updated": updated,
        "source_rows": len(rows),
    }


def create_model_snapshot(db_path=DB_PATH):
    conn = get_db(db_path)

    total = conn.execute("SELECT COUNT(*) AS c FROM shark_ai_predictions").fetchone()["c"]
    settled = conn.execute("SELECT COUNT(*) AS c FROM shark_ai_predictions WHERE result IS NOT NULL").fetchone()["c"]
    wins = conn.execute("SELECT COUNT(*) AS c FROM shark_ai_predictions WHERE UPPER(result)='WIN'").fetchone()["c"]
    profit = conn.execute("SELECT COALESCE(SUM(profit_loss),0) AS p FROM shark_ai_predictions").fetchone()["p"]

    accuracy = round((wins / max(settled, 1)) * 100, 2)
    roi = round((float(profit or 0) / max(settled, 1)) * 100, 2)

    best = conn.execute("""
        SELECT pattern_key, roi FROM shark_ai_pattern_memory
        ORDER BY roi DESC LIMIT 1
    """).fetchone()

    worst = conn.execute("""
        SELECT pattern_key, roi FROM shark_ai_pattern_memory
        ORDER BY roi ASC LIMIT 1
    """).fetchone()

    pattern_count = conn.execute("SELECT COUNT(*) AS c FROM shark_ai_pattern_memory").fetchone()["c"]
    reliability_score = min(round(50 + pattern_count * 2 + accuracy * 0.35 + max(roi, 0), 2), 100)

    best_pattern = f"{best['pattern_key']} ({best['roi']}%)" if best else None
    worst_pattern = f"{worst['pattern_key']} ({worst['roi']}%)" if worst else None

    conn.execute("""
    INSERT INTO shark_ai_model_snapshots (
        model_version, dataset_size, prediction_count, accuracy, roi,
        reliability_score, best_pattern, worst_pattern, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        MODEL_VERSION, settled, total, accuracy, roi, reliability_score,
        best_pattern, worst_pattern, now_iso()
    ))

    conn.commit()
    conn.close()

    return {
        "model_version": MODEL_VERSION,
        "dataset_size": settled,
        "prediction_count": total,
        "accuracy": accuracy,
        "roi": roi,
        "reliability_score": reliability_score,
        "best_pattern": best_pattern,
        "worst_pattern": worst_pattern,
    }


def get_shark_ai_v79_status(db_path=DB_PATH):
    conn = get_db(db_path)

    predictions = conn.execute("SELECT COUNT(*) AS c FROM shark_ai_predictions").fetchone()["c"]
    approved = conn.execute("SELECT COUNT(*) AS c FROM shark_ai_predictions WHERE prediction_label='APROBADO'").fetchone()["c"]
    rejected = conn.execute("SELECT COUNT(*) AS c FROM shark_ai_predictions WHERE prediction_label='RECHAZADO'").fetchone()["c"]
    patterns = conn.execute("SELECT COUNT(*) AS c FROM shark_ai_pattern_memory").fetchone()["c"]
    rejected_signals = conn.execute("SELECT COUNT(*) AS c FROM shark_ai_rejected_signals").fetchone()["c"]

    latest_snapshot = conn.execute("""
        SELECT * FROM shark_ai_model_snapshots
        ORDER BY id DESC LIMIT 1
    """).fetchone()

    top_patterns = [
        dict(r) for r in conn.execute("""
        SELECT pattern_key, sample_size, win_rate, roi, reliability, score_adjustment
        FROM shark_ai_pattern_memory
        ORDER BY roi DESC
        LIMIT 8
        """).fetchall()
    ]

    recent_predictions = [
        dict(r) for r in conn.execute("""
        SELECT match_name, market, odds, adaptive_score, confidence_level,
               prediction_label, prediction_probability, created_at
        FROM shark_ai_predictions
        ORDER BY id DESC
        LIMIT 10
        """).fetchall()
    ]

    conn.close()

    snapshot = dict(latest_snapshot) if latest_snapshot else create_model_snapshot(db_path)

    ai_score = min(round(
        72
        + min(predictions, 100) * 0.08
        + min(patterns, 40) * 0.35
        + float(snapshot.get("reliability_score", 0)) * 0.18,
        2
    ), 99)

    return {
        "status": "SHARK AI EVOLUCIONANDO",
        "ai_evolution_score": ai_score,
        "model_version": MODEL_VERSION,
        "predictions": predictions,
        "approved": approved,
        "rejected": rejected,
        "patterns": patterns,
        "rejected_signals": rejected_signals,
        "snapshot": snapshot,
        "top_patterns": top_patterns,
        "recent_predictions": recent_predictions,
        "modules": [
            {"name": "Score adaptativo V79", "status": "ACTIVO"},
            {"name": "Memoria de patrones", "status": "ACTIVO"},
            {"name": "Value Score", "status": "ACTIVO"},
            {"name": "Risk Score", "status": "ACTIVO"},
            {"name": "Explicaciones IA premium", "status": "ACTIVO"},
            {"name": "Rechazo inteligente de señales", "status": "ACTIVO"},
            {"name": "Snapshots de modelo", "status": "ACTIVO"},
        ],
    }
