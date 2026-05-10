
"""
NeMeSiS SHARK PRO V74
User Experience Automation + Retention Engine
"""

import sqlite3
from datetime import datetime, timedelta


DB_PATH = "nemesis.db"


def get_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def now_iso():
    return datetime.utcnow().isoformat()


def track_engagement_event(user_id, event_type, event_value="", page="", source="APP", db_path=DB_PATH):
    conn = get_db(db_path)
    conn.execute("""
    INSERT INTO user_engagement_events (
        user_id, event_type, event_value, page, source, created_at
    ) VALUES (?, ?, ?, ?, ?, ?)
    """, (str(user_id or "anonymous"), event_type, event_value, page, source, now_iso()))
    conn.commit()
    conn.close()


def ensure_retention_profile(user_id, db_path=DB_PATH):
    conn = get_db(db_path)
    existing = conn.execute("""
    SELECT user_id FROM user_retention_profiles WHERE user_id=?
    """, (str(user_id),)).fetchone()

    if not existing:
        conn.execute("""
        INSERT INTO user_retention_profiles (
            user_id, engagement_score, retention_risk, current_streak,
            last_seen_at, onboarding_completed, updated_at
        ) VALUES (?, 0, 'UNKNOWN', 0, ?, 0, ?)
        """, (str(user_id), now_iso(), now_iso()))
        conn.commit()

    conn.close()


def calculate_user_engagement(user_id, db_path=DB_PATH):
    ensure_retention_profile(user_id, db_path)
    conn = get_db(db_path)

    since_7d = (datetime.utcnow() - timedelta(days=7)).isoformat()
    since_24h = (datetime.utcnow() - timedelta(hours=24)).isoformat()

    events_7d = conn.execute("""
    SELECT COUNT(*) AS c FROM user_engagement_events
    WHERE user_id=? AND created_at >= ?
    """, (str(user_id), since_7d)).fetchone()["c"]

    events_24h = conn.execute("""
    SELECT COUNT(*) AS c FROM user_engagement_events
    WHERE user_id=? AND created_at >= ?
    """, (str(user_id), since_24h)).fetchone()["c"]

    pick_views = conn.execute("""
    SELECT COUNT(*) AS c FROM user_engagement_events
    WHERE user_id=? AND event_type IN ('PICK_VIEW','LIVE_CENTER_VIEW','SHARK_AI_VIEW')
    AND created_at >= ?
    """, (str(user_id), since_7d)).fetchone()["c"]

    score = min(round(events_7d * 3 + events_24h * 5 + pick_views * 4, 2), 100)

    if score >= 70:
        risk = "BAJO"
    elif score >= 35:
        risk = "MEDIO"
    else:
        risk = "ALTO"

    conn.execute("""
    UPDATE user_retention_profiles
    SET engagement_score=?, retention_risk=?, last_seen_at=?, updated_at=?
    WHERE user_id=?
    """, (score, risk, now_iso(), now_iso(), str(user_id)))

    conn.commit()
    conn.close()

    return {
        "user_id": str(user_id),
        "engagement_score": score,
        "retention_risk": risk,
        "events_7d": events_7d,
        "events_24h": events_24h,
        "pick_views_7d": pick_views,
    }


def create_retention_action(user_id, action_type, title, message, priority="NORMAL", channel="IN_APP", db_path=DB_PATH):
    conn = get_db(db_path)
    conn.execute("""
    INSERT INTO retention_actions (
        user_id, action_type, status, priority, title, message, channel, created_at
    ) VALUES (?, ?, 'PENDING', ?, ?, ?, ?, ?)
    """, (str(user_id), action_type, priority, title, message, channel, now_iso()))
    conn.commit()
    conn.close()


def run_retention_rules(db_path=DB_PATH):
    conn = get_db(db_path)
    profiles = conn.execute("""
    SELECT * FROM user_retention_profiles
    """).fetchall()

    created = 0

    for profile in profiles:
        user_id = profile["user_id"]
        score = float(profile["engagement_score"] or 0)
        risk = profile["retention_risk"] or "UNKNOWN"

        pending_existing = conn.execute("""
        SELECT id FROM retention_actions
        WHERE user_id=? AND status='PENDING'
        LIMIT 1
        """, (user_id,)).fetchone()

        if pending_existing:
            continue

        if risk == "ALTO":
            conn.execute("""
            INSERT INTO retention_actions (
                user_id, action_type, status, priority, title, message, channel, created_at
            ) VALUES (?, 'REACTIVATION', 'PENDING', 'HIGH', ?, ?, 'IN_APP', ?)
            """, (
                user_id,
                "Vuelve al radar SHARK",
                "Hay nuevas oportunidades live y picks premium esperándote.",
                now_iso(),
            ))
            created += 1

        elif score >= 70:
            conn.execute("""
            INSERT INTO retention_actions (
                user_id, action_type, status, priority, title, message, channel, created_at
            ) VALUES (?, 'POWER_USER', 'PENDING', 'NORMAL', ?, ?, 'IN_APP', ?)
            """, (
                user_id,
                "Estás en modo SHARK",
                "Tu actividad es alta. Revisa el Live Center para oportunidades avanzadas.",
                now_iso(),
            ))
            created += 1

    conn.commit()
    conn.close()

    return {
        "ok": True,
        "actions_created": created,
        "profiles_checked": len(profiles),
    }


def get_retention_status(db_path=DB_PATH):
    conn = get_db(db_path)

    total_profiles = conn.execute("SELECT COUNT(*) AS c FROM user_retention_profiles").fetchone()["c"]
    high_risk = conn.execute("""
    SELECT COUNT(*) AS c FROM user_retention_profiles WHERE retention_risk='ALTO'
    """).fetchone()["c"]
    medium_risk = conn.execute("""
    SELECT COUNT(*) AS c FROM user_retention_profiles WHERE retention_risk='MEDIO'
    """).fetchone()["c"]
    low_risk = conn.execute("""
    SELECT COUNT(*) AS c FROM user_retention_profiles WHERE retention_risk='BAJO'
    """).fetchone()["c"]

    pending_actions = conn.execute("""
    SELECT COUNT(*) AS c FROM retention_actions WHERE status='PENDING'
    """).fetchone()["c"]

    events_24h = conn.execute("""
    SELECT COUNT(*) AS c FROM user_engagement_events
    WHERE created_at >= ?
    """, ((datetime.utcnow() - timedelta(hours=24)).isoformat(),)).fetchone()["c"]

    recent_actions = [
        dict(row) for row in conn.execute("""
        SELECT user_id, action_type, priority, title, message, channel, created_at
        FROM retention_actions
        ORDER BY id DESC
        LIMIT 12
        """).fetchall()
    ]

    conn.close()

    score = 85
    if total_profiles == 0:
        score = 70
    if high_risk > 0:
        score -= min(high_risk * 4, 25)
    if events_24h > 10:
        score += 5

    score = max(min(score, 100), 0)

    return {
        "status": "RETENCIÓN ACTIVA" if total_profiles else "ESPERANDO USUARIOS",
        "retention_score": score,
        "total_profiles": total_profiles,
        "risk": {
            "alto": high_risk,
            "medio": medium_risk,
            "bajo": low_risk,
        },
        "pending_actions": pending_actions,
        "events_24h": events_24h,
        "recent_actions": recent_actions,
        "modules": [
            {"name": "Onboarding dinámico", "status": "ACTIVO"},
            {"name": "Engagement Score", "status": "ACTIVO"},
            {"name": "Retention Risk", "status": "ACTIVO"},
            {"name": "In-App Actions", "status": "ACTIVO"},
            {"name": "Reactivación inteligente", "status": "ACTIVO"},
        ],
    }


def get_user_experience_payload(user_id, db_path=DB_PATH):
    ensure_retention_profile(user_id, db_path)
    engagement = calculate_user_engagement(user_id, db_path)

    conn = get_db(db_path)
    actions = [
        dict(row) for row in conn.execute("""
        SELECT id, action_type, priority, title, message, channel, created_at
        FROM retention_actions
        WHERE user_id=? AND status='PENDING'
        ORDER BY id DESC
        LIMIT 5
        """, (str(user_id),)).fetchall()
    ]

    onboarding_done = conn.execute("""
    SELECT onboarding_completed FROM user_retention_profiles
    WHERE user_id=?
    """, (str(user_id),)).fetchone()

    conn.close()

    steps = [
        {"key": "ver_live_center", "title": "Explora el Live Center", "done": False},
        {"key": "ver_pick", "title": "Revisa tu primer pick SHARK", "done": False},
        {"key": "activar_alertas", "title": "Activa alertas premium", "done": False},
        {"key": "abrir_shark_ai", "title": "Consulta SHARK AI", "done": False},
    ]

    return {
        "user_id": str(user_id),
        "engagement": engagement,
        "actions": actions,
        "onboarding_completed": bool(onboarding_done and onboarding_done["onboarding_completed"]),
        "onboarding_steps": steps,
    }
