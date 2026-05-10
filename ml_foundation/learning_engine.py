
"""
NeMeSiS SHARK PRO V69
SHARK Learning Engine

Este módulo no depende de librerías pesadas para ser seguro en Render.
Calcula patrones históricos, ajustes adaptativos y métricas para SHARK AI.
"""

import sqlite3
from datetime import datetime
from collections import defaultdict


DB_PATH = "nemesis.db"


def get_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def calculate_win_rate(wins, total):
    if not total:
        return 0
    return round((wins / total) * 100, 2)


def calculate_roi(total_profit, total_stake):
    if not total_stake:
        return 0
    return round((total_profit / total_stake) * 100, 2)


def confidence_adjustment_from_pattern(win_rate, roi):
    """
    Ajuste simple y seguro.
    Más adelante puede conectarse a LightGBM/XGBoost sin romper la app.
    """
    adjustment = 0

    if win_rate >= 65:
        adjustment += 6
    elif win_rate >= 58:
        adjustment += 3
    elif win_rate < 45:
        adjustment -= 6

    if roi >= 12:
        adjustment += 5
    elif roi >= 5:
        adjustment += 2
    elif roi < -8:
        adjustment -= 5

    return max(min(adjustment, 15), -15)


def upsert_pattern(conn, pattern_type, pattern_key, rows):
    total = len(rows)
    wins = len([r for r in rows if str(r["result"]).upper() == "WIN"])
    losses = len([r for r in rows if str(r["result"]).upper() == "LOSS"])
    voids = len([r for r in rows if str(r["result"]).upper() == "VOID"])
    profit = sum(float(r["profit_loss"] or 0) for r in rows)
    stake = total
    win_rate = calculate_win_rate(wins, max(total - voids, 0))
    roi = calculate_roi(profit, stake)
    adjustment = confidence_adjustment_from_pattern(win_rate, roi)

    existing = conn.execute(
        """
        SELECT id FROM shark_learning_patterns
        WHERE pattern_type=? AND pattern_key=?
        """,
        (pattern_type, pattern_key),
    ).fetchone()

    payload = (
        total,
        wins,
        losses,
        voids,
        win_rate,
        roi,
        adjustment,
        -adjustment,
        datetime.utcnow().isoformat(),
    )

    if existing:
        conn.execute(
            """
            UPDATE shark_learning_patterns
            SET total_picks=?, wins=?, losses=?, voids=?,
                win_rate=?, roi=?, confidence_adjustment=?,
                risk_adjustment=?, updated_at=?
            WHERE id=?
            """,
            payload + (existing["id"],),
        )
    else:
        conn.execute(
            """
            INSERT INTO shark_learning_patterns (
                pattern_type, pattern_key, total_picks, wins, losses, voids,
                win_rate, roi, confidence_adjustment, risk_adjustment, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (pattern_type, pattern_key) + payload,
        )


def rebuild_learning_patterns(db_path=DB_PATH):
    conn = get_db(db_path)
    rows = conn.execute(
        """
        SELECT * FROM shark_ml_dataset
        WHERE result IS NOT NULL
        """
    ).fetchall()

    grouped = defaultdict(list)

    for row in rows:
        for field in ["sport", "league", "market", "confidence_level", "heat_level"]:
            key = row[field] or "UNKNOWN"
            grouped[(field, key)].append(row)

    for (pattern_type, pattern_key), group_rows in grouped.items():
        upsert_pattern(conn, pattern_type, pattern_key, group_rows)

    conn.commit()
    conn.close()

    return {
        "status": "ok",
        "patterns_rebuilt": len(grouped),
        "dataset_rows": len(rows),
    }


def get_adaptive_score_adjustment(sport=None, league=None, market=None, db_path=DB_PATH):
    conn = get_db(db_path)

    adjustments = []

    for pattern_type, pattern_key in [
        ("sport", sport),
        ("league", league),
        ("market", market),
    ]:
        if not pattern_key:
            continue

        row = conn.execute(
            """
            SELECT confidence_adjustment
            FROM shark_learning_patterns
            WHERE pattern_type=? AND pattern_key=?
            """,
            (pattern_type, pattern_key),
        ).fetchone()

        if row:
            adjustments.append(float(row["confidence_adjustment"] or 0))

    conn.close()

    if not adjustments:
        return 0

    return round(sum(adjustments) / len(adjustments), 2)


def apply_adaptive_shark_score(base_score, sport=None, league=None, market=None, db_path=DB_PATH):
    adjustment = get_adaptive_score_adjustment(sport, league, market, db_path)
    adapted = float(base_score or 0) + adjustment
    return max(min(round(adapted, 2), 99), 1)


def get_ml_center_status(db_path=DB_PATH):
    conn = get_db(db_path)

    dataset_size = conn.execute("SELECT COUNT(*) AS c FROM shark_ml_dataset").fetchone()["c"]
    settled = conn.execute(
        "SELECT COUNT(*) AS c FROM shark_ml_dataset WHERE result IS NOT NULL"
    ).fetchone()["c"]

    wins = conn.execute(
        "SELECT COUNT(*) AS c FROM shark_ml_dataset WHERE UPPER(result)='WIN'"
    ).fetchone()["c"]

    profit = conn.execute(
        "SELECT COALESCE(SUM(profit_loss),0) AS p FROM shark_ml_dataset"
    ).fetchone()["p"]

    best_pattern = conn.execute(
        """
        SELECT pattern_type, pattern_key, roi, win_rate
        FROM shark_learning_patterns
        WHERE total_picks >= 3
        ORDER BY roi DESC
        LIMIT 1
        """
    ).fetchone()

    worst_pattern = conn.execute(
        """
        SELECT pattern_type, pattern_key, roi, win_rate
        FROM shark_learning_patterns
        WHERE total_picks >= 3
        ORDER BY roi ASC
        LIMIT 1
        """
    ).fetchone()

    conn.close()

    accuracy = calculate_win_rate(wins, settled)
    roi = calculate_roi(float(profit or 0), max(dataset_size, 1))

    return {
        "dataset_size": dataset_size,
        "settled_picks": settled,
        "global_accuracy": accuracy,
        "global_roi": roi,
        "best_pattern": dict(best_pattern) if best_pattern else None,
        "worst_pattern": dict(worst_pattern) if worst_pattern else None,
        "engine_status": "APRENDIZAJE ACTIVO" if dataset_size else "ESPERANDO DATOS",
    }
