
"""
NeMeSiS SHARK PRO V73
Observability engine ligero para Render/SQLite.
"""

import os
import sqlite3
import traceback as tb
from datetime import datetime, timedelta


DB_PATH = "nemesis.db"


def get_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def env_bool(name, default=True):
    value = os.getenv(name)
    if value is None:
        return default
    return str(value).lower() in ("1", "true", "yes", "on")


def log_error_event(error_type, endpoint="", method="", status_code=500, message="", traceback="", user_id="", ip="", user_agent="", db_path=DB_PATH):
    if not env_bool("V73_ERROR_TRACKING_ENABLED", True):
        return

    try:
        conn = get_db(db_path)
        conn.execute("""
        INSERT INTO app_error_events (
            error_type, endpoint, method, status_code, message, traceback,
            user_id, ip, user_agent, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            error_type,
            endpoint,
            method,
            status_code,
            str(message)[:2000],
            str(traceback)[:6000],
            str(user_id or ""),
            str(ip or ""),
            str(user_agent or "")[:800],
            datetime.utcnow().isoformat()
        ))
        conn.commit()
        conn.close()
    except Exception:
        pass


def log_exception(exc, request=None, status_code=500):
    trace = tb.format_exc()
    endpoint = getattr(request, "path", "") if request else ""
    method = getattr(request, "method", "") if request else ""
    ip = getattr(request, "remote_addr", "") if request else ""
    user_agent = ""
    try:
        user_agent = request.headers.get("User-Agent", "") if request else ""
    except Exception:
        user_agent = ""

    log_error_event(
        error_type=exc.__class__.__name__,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        message=str(exc),
        traceback=trace,
        ip=ip,
        user_agent=user_agent,
    )


def log_health_event(event_type, status, message, response_time_ms=0, db_path=DB_PATH):
    try:
        conn = get_db(db_path)
        conn.execute("""
        INSERT INTO app_health_events (
            event_type, status, message, response_time_ms, created_at
        ) VALUES (?, ?, ?, ?, ?)
        """, (
            event_type,
            status,
            str(message)[:1000],
            float(response_time_ms or 0),
            datetime.utcnow().isoformat(),
        ))
        conn.commit()
        conn.close()
    except Exception:
        pass


def check_db_status(db_path=DB_PATH):
    try:
        conn = get_db(db_path)
        row = conn.execute("PRAGMA integrity_check").fetchone()
        conn.close()
        result = row[0] if row else "unknown"
        return "OK" if result == "ok" else f"REVISAR: {result}"
    except Exception as exc:
        return f"ERROR: {exc}"


def get_table_count(table, db_path=DB_PATH):
    try:
        conn = get_db(db_path)
        row = conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()
        conn.close()
        return int(row["c"])
    except Exception:
        return 0


def create_performance_snapshot(db_path=DB_PATH):
    conn = get_db(db_path)

    since = (datetime.utcnow() - timedelta(hours=24)).isoformat()

    total_errors = conn.execute("""
        SELECT COUNT(*) AS c FROM app_error_events
        WHERE created_at >= ?
    """, (since,)).fetchone()["c"]

    health_rows = conn.execute("""
        SELECT response_time_ms FROM app_health_events
        WHERE created_at >= ?
    """, (since,)).fetchall()

    avg_response = 0
    if health_rows:
        avg_response = round(sum(float(r["response_time_ms"] or 0) for r in health_rows) / len(health_rows), 2)

    telegram_pending = 0
    push_pending = 0

    try:
        telegram_pending = conn.execute("""
            SELECT COUNT(*) AS c FROM telegram_queue
            WHERE status IN ('PENDING','RETRYING','PROCESSING')
        """).fetchone()["c"]
    except Exception:
        telegram_pending = 0

    try:
        push_pending = conn.execute("""
            SELECT COUNT(*) AS c FROM push_queue
            WHERE status IN ('PENDING','RETRYING','PROCESSING')
        """).fetchone()["c"]
    except Exception:
        push_pending = 0

    db_status = check_db_status(db_path)

    # request total aproximado: health events + errors
    total_requests = len(health_rows) + total_errors
    error_rate = round((total_errors / total_requests) * 100, 2) if total_requests else 0

    conn.execute("""
    INSERT INTO app_performance_snapshots (
        total_requests, total_errors, error_rate, avg_response_time_ms,
        telegram_pending, push_pending, db_status, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        total_requests,
        total_errors,
        error_rate,
        avg_response,
        telegram_pending,
        push_pending,
        db_status,
        datetime.utcnow().isoformat(),
    ))

    conn.commit()
    conn.close()

    return {
        "total_requests": total_requests,
        "total_errors": total_errors,
        "error_rate": error_rate,
        "avg_response_time_ms": avg_response,
        "telegram_pending": telegram_pending,
        "push_pending": push_pending,
        "db_status": db_status,
    }


def get_observability_status(db_path=DB_PATH):
    conn = get_db(db_path)
    since_24h = (datetime.utcnow() - timedelta(hours=24)).isoformat()

    total_errors_24h = conn.execute("""
        SELECT COUNT(*) AS c FROM app_error_events
        WHERE created_at >= ?
    """, (since_24h,)).fetchone()["c"]

    recent_errors = [
        dict(row) for row in conn.execute("""
        SELECT error_type, endpoint, status_code, message, created_at
        FROM app_error_events
        ORDER BY id DESC
        LIMIT 12
        """).fetchall()
    ]

    latest_snapshot = conn.execute("""
        SELECT * FROM app_performance_snapshots
        ORDER BY id DESC
        LIMIT 1
    """).fetchone()

    conn.close()

    snapshot = dict(latest_snapshot) if latest_snapshot else create_performance_snapshot(db_path)

    score = 100
    if total_errors_24h > 0:
        score -= min(total_errors_24h * 3, 40)
    if snapshot.get("db_status") != "OK":
        score -= 25
    if float(snapshot.get("error_rate", 0) or 0) > 5:
        score -= 15

    if score >= 90:
        status = "OBSERVABILIDAD ÓPTIMA"
    elif score >= 75:
        status = "ESTABLE CON AVISOS"
    else:
        status = "REVISAR INCIDENCIAS"

    return {
        "status": status,
        "observability_score": max(score, 0),
        "errors_24h": total_errors_24h,
        "snapshot": snapshot,
        "recent_errors": recent_errors,
        "checks": [
            {
                "area": "Base de datos",
                "status": "OK" if snapshot.get("db_status") == "OK" else "REVISAR",
                "description": snapshot.get("db_status", "unknown"),
            },
            {
                "area": "Errores 24h",
                "status": "OK" if total_errors_24h == 0 else "REVISAR",
                "description": f"{total_errors_24h} errores registrados en las últimas 24h.",
            },
            {
                "area": "Telegram Queue",
                "status": "OK" if int(snapshot.get("telegram_pending", 0) or 0) < 10 else "REVISAR",
                "description": f"{snapshot.get('telegram_pending', 0)} pendientes.",
            },
            {
                "area": "Push Queue",
                "status": "OK" if int(snapshot.get("push_pending", 0) or 0) < 10 else "REVISAR",
                "description": f"{snapshot.get('push_pending', 0)} pendientes.",
            },
            {
                "area": "Tiempo medio",
                "status": "OK" if float(snapshot.get("avg_response_time_ms", 0) or 0) < 1200 else "REVISAR",
                "description": f"{snapshot.get('avg_response_time_ms', 0)} ms.",
            },
        ],
    }
