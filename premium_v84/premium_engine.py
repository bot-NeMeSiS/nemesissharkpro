
"""
NeMeSiS SHARK PRO V84
Premium Engagement Experience Engine
"""

import json
import sqlite3
from datetime import datetime, timedelta


DB_PATH = "nemesis.db"


def get_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def now_iso():
    return datetime.utcnow().isoformat()


def level_from_xp(xp):
    xp = int(xp or 0)
    if xp >= 1500:
        return 10
    if xp >= 1000:
        return 8
    if xp >= 650:
        return 6
    if xp >= 350:
        return 4
    if xp >= 150:
        return 3
    if xp >= 50:
        return 2
    return 1


def ensure_xp_profile(user_id, db_path=DB_PATH):
    uid = str(user_id or "anonymous")
    conn = get_db(db_path)
    row = conn.execute("SELECT user_id FROM user_xp_profiles WHERE user_id=?", (uid,)).fetchone()
    if not row:
        conn.execute("""
        INSERT INTO user_xp_profiles (
            user_id, xp, level, streak_days, last_activity_at, badge_count, updated_at
        ) VALUES (?, 0, 1, 0, ?, 0, ?)
        """, (uid, now_iso(), now_iso()))
        conn.commit()
    conn.close()


def log_premium_event(event_type, user_id="anonymous", title="", metadata=None, db_path=DB_PATH):
    conn = get_db(db_path)
    conn.execute("""
    INSERT INTO premium_experience_events (
        event_type, user_id, title, metadata, created_at
    ) VALUES (?, ?, ?, ?, ?)
    """, (
        event_type,
        str(user_id or "anonymous"),
        title or event_type,
        json.dumps(metadata or {}, ensure_ascii=False),
        now_iso()
    ))
    conn.commit()
    conn.close()


def add_xp(user_id, amount=10, reason="Actividad SHARK", db_path=DB_PATH):
    uid = str(user_id or "anonymous")
    ensure_xp_profile(uid, db_path)

    conn = get_db(db_path)
    row = conn.execute("SELECT * FROM user_xp_profiles WHERE user_id=?", (uid,)).fetchone()
    current_xp = int(row["xp"] or 0)
    old_level = int(row["level"] or 1)

    new_xp = current_xp + int(amount or 0)
    new_level = level_from_xp(new_xp)

    last_activity = row["last_activity_at"]
    streak = int(row["streak_days"] or 0)

    try:
        last_dt = datetime.fromisoformat(last_activity)
        if datetime.utcnow().date() > last_dt.date():
            if (datetime.utcnow().date() - last_dt.date()).days == 1:
                streak += 1
            else:
                streak = 1
    except Exception:
        streak = 1

    conn.execute("""
    UPDATE user_xp_profiles
    SET xp=?, level=?, streak_days=?, last_activity_at=?, updated_at=?
    WHERE user_id=?
    """, (new_xp, new_level, streak, now_iso(), now_iso(), uid))

    conn.commit()
    conn.close()

    if new_level > old_level:
        grant_badge(uid, f"LEVEL_{new_level}", f"Nivel {new_level}", "Has subido de nivel en NeMeSiS SHARK PRO.", db_path)
        log_premium_event("LEVEL_UP", uid, f"Subida a nivel {new_level}", {"xp": new_xp}, db_path)

    log_premium_event("XP_ADDED", uid, reason, {"amount": amount, "xp": new_xp}, db_path)
    return get_user_premium_payload(uid, db_path)


def grant_badge(user_id, badge_key, title, description, db_path=DB_PATH):
    uid = str(user_id or "anonymous")
    conn = get_db(db_path)

    exists = conn.execute("""
    SELECT id FROM user_badges WHERE user_id=? AND badge_key=?
    """, (uid, badge_key)).fetchone()

    if not exists:
        conn.execute("""
        INSERT INTO user_badges (
            user_id, badge_key, badge_title, badge_description, created_at
        ) VALUES (?, ?, ?, ?, ?)
        """, (uid, badge_key, title, description, now_iso()))

        count = conn.execute("SELECT COUNT(*) AS c FROM user_badges WHERE user_id=?", (uid,)).fetchone()["c"]
        conn.execute("""
        UPDATE user_xp_profiles SET badge_count=?, updated_at=? WHERE user_id=?
        """, (count, now_iso(), uid))

    conn.commit()
    conn.close()


def ensure_default_missions(user_id, db_path=DB_PATH):
    uid = str(user_id or "anonymous")
    conn = get_db(db_path)

    missions = [
        ("open_live_center", "Explora el Live Center", "Abre el centro live y revisa partidos activos.", 20),
        ("view_shark_ai", "Consulta SHARK AI", "Revisa una explicación premium de SHARK AI.", 25),
        ("save_favorite", "Guarda un favorito", "Añade un partido o pick a favoritos.", 15),
        ("activate_alerts", "Activa alertas", "Activa Telegram o Push para picks premium.", 30),
        ("share_pick", "Comparte un pick", "Comparte un pick SHARK con tu comunidad.", 25),
    ]

    for key, title, desc, xp in missions:
        exists = conn.execute("""
        SELECT id FROM ux_missions WHERE user_id=? AND mission_key=?
        """, (uid, key)).fetchone()
        if not exists:
            conn.execute("""
            INSERT INTO ux_missions (
                user_id, mission_key, title, description, xp_reward, status, created_at
            ) VALUES (?, ?, ?, ?, ?, 'PENDING', ?)
            """, (uid, key, title, desc, xp, now_iso()))

    conn.commit()
    conn.close()


def complete_mission(user_id, mission_key, db_path=DB_PATH):
    uid = str(user_id or "anonymous")
    ensure_default_missions(uid, db_path)

    conn = get_db(db_path)
    mission = conn.execute("""
    SELECT * FROM ux_missions
    WHERE user_id=? AND mission_key=? AND status='PENDING'
    """, (uid, mission_key)).fetchone()

    if not mission:
        conn.close()
        return get_user_premium_payload(uid, db_path)

    conn.execute("""
    UPDATE ux_missions
    SET status='COMPLETED', completed_at=?
    WHERE id=?
    """, (now_iso(), mission["id"]))

    conn.commit()
    conn.close()

    payload = add_xp(uid, int(mission["xp_reward"] or 10), f"Misión completada: {mission['title']}", db_path)
    grant_badge(uid, f"MISSION_{mission_key}", mission["title"], mission["description"], db_path)
    log_premium_event("MISSION_COMPLETED", uid, mission["title"], {"mission_key": mission_key}, db_path)
    return payload


def get_user_premium_payload(user_id, db_path=DB_PATH):
    uid = str(user_id or "anonymous")
    ensure_xp_profile(uid, db_path)
    ensure_default_missions(uid, db_path)

    conn = get_db(db_path)
    profile = conn.execute("SELECT * FROM user_xp_profiles WHERE user_id=?", (uid,)).fetchone()

    badges = [
        dict(row) for row in conn.execute("""
        SELECT badge_key, badge_title, badge_description, created_at
        FROM user_badges
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 12
        """, (uid,)).fetchall()
    ]

    missions = [
        dict(row) for row in conn.execute("""
        SELECT mission_key, title, description, xp_reward, status, completed_at
        FROM ux_missions
        WHERE user_id=?
        ORDER BY id ASC
        """, (uid,)).fetchall()
    ]

    conn.close()

    xp = int(profile["xp"] or 0)
    level = int(profile["level"] or 1)
    next_level_xp = {1: 50, 2: 150, 3: 350, 4: 650, 5: 650, 6: 1000, 7: 1000, 8: 1500, 9: 1500}.get(level, 2000)
    progress = min(round((xp / max(next_level_xp, 1)) * 100, 2), 100)

    return {
        "user_id": uid,
        "profile": dict(profile),
        "badges": badges,
        "missions": missions,
        "next_level_xp": next_level_xp,
        "level_progress": progress,
        "status": "PREMIUM EXPERIENCE ACTIVA",
    }


def get_v84_admin_status(db_path=DB_PATH):
    conn = get_db(db_path)

    profiles = conn.execute("SELECT COUNT(*) AS c FROM user_xp_profiles").fetchone()["c"]
    badges = conn.execute("SELECT COUNT(*) AS c FROM user_badges").fetchone()["c"]
    missions = conn.execute("SELECT COUNT(*) AS c FROM ux_missions").fetchone()["c"]
    completed = conn.execute("SELECT COUNT(*) AS c FROM ux_missions WHERE status='COMPLETED'").fetchone()["c"]
    events = conn.execute("SELECT COUNT(*) AS c FROM premium_experience_events").fetchone()["c"]

    top_users = [
        dict(row) for row in conn.execute("""
        SELECT user_id, xp, level, streak_days, badge_count
        FROM user_xp_profiles
        ORDER BY xp DESC
        LIMIT 10
        """).fetchall()
    ]

    recent_events = [
        dict(row) for row in conn.execute("""
        SELECT event_type, user_id, title, created_at
        FROM premium_experience_events
        ORDER BY id DESC
        LIMIT 12
        """).fetchall()
    ]

    conn.close()

    score = min(88 + profiles * 2 + completed * 1 + badges * 0.5, 99)

    return {
        "status": "PREMIUM ENGAGEMENT READY",
        "experience_score": round(score, 2),
        "profiles": profiles,
        "badges": badges,
        "missions": missions,
        "completed_missions": completed,
        "events": events,
        "top_users": top_users,
        "recent_events": recent_events,
        "modules": [
            {"name": "Microanimaciones premium", "status": "ACTIVO"},
            {"name": "XP / niveles", "status": "ACTIVO"},
            {"name": "Misiones UX", "status": "ACTIVO"},
            {"name": "Badges suaves", "status": "ACTIVO"},
            {"name": "Realtime feeling UI", "status": "ACTIVO"},
            {"name": "Onboarding inteligente", "status": "ACTIVO"},
            {"name": "Engagement events", "status": "ACTIVO"},
        ],
    }
