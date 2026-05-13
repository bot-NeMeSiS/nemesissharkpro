
"""
NeMeSiS SHARK PRO V72
Launch Readiness + Beta Engine
"""

import os
import secrets
import sqlite3
from datetime import datetime


DB_PATH = "nemesis.db"


def get_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_setting(key, default=None, db_path=DB_PATH):
    conn = get_db(db_path)
    row = conn.execute("SELECT value FROM launch_settings WHERE key=?", (key,)).fetchone()
    conn.close()
    if not row:
        return os.getenv(key, default)
    return row["value"]


def set_setting(key, value, db_path=DB_PATH):
    conn = get_db(db_path)
    conn.execute("""
    INSERT INTO launch_settings (key, value, updated_at)
    VALUES (?, ?, ?)
    ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
    """, (key, str(value), datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def create_beta_invite(email, plan_granted="PRO", notes="", db_path=DB_PATH):
    invite_code = "NSP-" + secrets.token_urlsafe(8).replace("-", "").replace("_", "")[:10].upper()
    conn = get_db(db_path)
    conn.execute("""
    INSERT OR REPLACE INTO beta_invites (
        email, invite_code, plan_granted, status, created_at, notes
    ) VALUES (?, ?, ?, 'PENDING', ?, ?)
    """, (email.lower().strip(), invite_code, plan_granted, datetime.utcnow().isoformat(), notes))
    conn.commit()
    conn.close()
    return invite_code


def validate_beta_invite(invite_code, db_path=DB_PATH):
    conn = get_db(db_path)
    row = conn.execute("""
    SELECT * FROM beta_invites
    WHERE invite_code=? AND status='PENDING'
    """, (invite_code.strip(),)).fetchone()
    conn.close()
    return dict(row) if row else None


def mark_invite_used(invite_code, user_id, db_path=DB_PATH):
    conn = get_db(db_path)
    conn.execute("""
    UPDATE beta_invites
    SET status='USED', used_by_user_id=?, used_at=?
    WHERE invite_code=?
    """, (str(user_id), datetime.utcnow().isoformat(), invite_code.strip()))
    conn.commit()
    conn.close()


def add_launch_event(event_type, status, message, db_path=DB_PATH):
    conn = get_db(db_path)
    conn.execute("""
    INSERT INTO launch_events (event_type, status, message, created_at)
    VALUES (?, ?, ?, ?)
    """, (event_type, status, message, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def get_launch_status(db_path=DB_PATH):
    conn = get_db(db_path)

    settings = {
        row["key"]: row["value"]
        for row in conn.execute("SELECT key, value FROM launch_settings").fetchall()
    }

    invite_counts = {
        "total": conn.execute("SELECT COUNT(*) AS c FROM beta_invites").fetchone()["c"],
        "pending": conn.execute("SELECT COUNT(*) AS c FROM beta_invites WHERE status='PENDING'").fetchone()["c"],
        "used": conn.execute("SELECT COUNT(*) AS c FROM beta_invites WHERE status='USED'").fetchone()["c"],
    }

    recent_events = [
        dict(row) for row in conn.execute("""
        SELECT event_type, status, message, created_at
        FROM launch_events
        ORDER BY id DESC
        LIMIT 10
        """).fetchall()
    ]

    conn.close()

    checklist = [
        {
            "area": "Beta Mode",
            "status": "ACTIVO" if settings.get("BETA_MODE") == "true" else "OFF",
            "description": "Control de beta cerrada antes de abrir pagos."
        },
        {
            "area": "Registro público",
            "status": "CERRADO" if settings.get("PUBLIC_REGISTRATION") == "false" else "ABIERTO",
            "description": "Recomendado cerrado hasta QA final."
        },
        {
            "area": "Mantenimiento",
            "status": "OFF" if settings.get("MAINTENANCE_MODE") == "false" else "ACTIVO",
            "description": "Permite pausar acceso si hay incidencia."
        },
        {
            "area": "Invitaciones beta",
            "status": "OK" if invite_counts["total"] >= 0 else "REVISAR",
            "description": f"{invite_counts['pending']} pendientes / {invite_counts['used']} usadas."
        },
        {
            "area": "Stripe",
            "status": "PENDIENTE",
            "description": "Stripe sigue bloqueado intencionadamente hasta rendimiento máximo."
        },
    ]

    readiness_score = 92
    if settings.get("PUBLIC_REGISTRATION") == "true":
        readiness_score -= 8
    if settings.get("MAINTENANCE_MODE") == "true":
        readiness_score -= 12

    return {
        "launch_stage": settings.get("LAUNCH_STAGE", "PRIVATE_BETA"),
        "readiness_score": readiness_score,
        "settings": settings,
        "invite_counts": invite_counts,
        "recent_events": recent_events,
        "checklist": checklist,
        "status": "BETA READY" if readiness_score >= 85 else "REVISAR",
    }
