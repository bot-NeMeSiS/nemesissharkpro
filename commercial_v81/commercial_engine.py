
"""
NeMeSiS SHARK PRO V81
App Top Comercial Engine
"""

import json
import secrets
import sqlite3
from datetime import datetime


DB_PATH = "nemesis.db"


def get_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def now_iso():
    return datetime.utcnow().isoformat()


def generate_share_code():
    return "NSP-" + secrets.token_urlsafe(8).replace("-", "").replace("_", "")[:10].upper()


def create_or_update_public_profile(
    user_id,
    display_name=None,
    avatar_emoji="🦈",
    bio="Perfil SHARK PRO",
    db_path=DB_PATH
):
    uid = str(user_id or "anonymous")
    conn = get_db(db_path)

    # Intentar traer stats del leaderboard V76 si existen
    stats = None
    try:
        stats = conn.execute("""
            SELECT roi, win_rate, picks_count, streak, rank_score
            FROM user_leaderboard_stats
            WHERE user_id=?
        """, (uid,)).fetchone()
    except Exception:
        stats = None

    roi = float(stats["roi"] or 0) if stats else 0
    win_rate = float(stats["win_rate"] or 0) if stats else 0
    picks = int(stats["picks_count"] or 0) if stats else 0
    streak = int(stats["streak"] or 0) if stats else 0
    reputation = float(stats["rank_score"] or 0) if stats else 50

    display_name = display_name or f"SHARK User {uid[-4:] if len(uid) >= 4 else uid}"

    existing = conn.execute("SELECT user_id FROM public_profiles WHERE user_id=?", (uid,)).fetchone()

    if existing:
        conn.execute("""
        UPDATE public_profiles
        SET display_name=?, avatar_emoji=?, bio=?, public_roi=?, public_win_rate=?,
            public_picks=?, public_streak=?, reputation_score=?, updated_at=?
        WHERE user_id=?
        """, (
            display_name, avatar_emoji, bio, roi, win_rate,
            picks, streak, reputation, now_iso(), uid
        ))
    else:
        conn.execute("""
        INSERT INTO public_profiles (
            user_id, display_name, avatar_emoji, bio, public_roi, public_win_rate,
            public_picks, public_streak, reputation_score, is_public, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
        """, (
            uid, display_name, avatar_emoji, bio, roi, win_rate,
            picks, streak, reputation, now_iso(), now_iso()
        ))

    conn.commit()
    conn.close()

    return get_public_profile(uid, db_path)


def get_public_profile(user_id, db_path=DB_PATH):
    conn = get_db(db_path)
    row = conn.execute("""
        SELECT * FROM public_profiles
        WHERE user_id=? AND is_public=1
    """, (str(user_id),)).fetchone()

    shared = [
        dict(r) for r in conn.execute("""
        SELECT share_code, title, match_name, market, odds, shark_score, confidence, views, created_at
        FROM shared_picks
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 10
        """, (str(user_id),)).fetchall()
    ]

    conn.close()

    if not row:
        return None

    return {
        "profile": dict(row),
        "shared_picks": shared,
    }


def share_pick(
    pick_id,
    user_id,
    title="Pick SHARK PRO",
    match_name="Partido destacado",
    market="Mercado premium",
    odds=1.85,
    shark_score=78,
    confidence="ALTA",
    db_path=DB_PATH
):
    conn = get_db(db_path)
    share_code = generate_share_code()

    share_text = (
        f"🦈 NeMeSiS SHARK PRO\n"
        f"{match_name}\n"
        f"Mercado: {market}\n"
        f"Cuota: {odds}\n"
        f"SHARK Score: {shark_score}%\n"
        f"Confianza: {confidence}"
    )

    conn.execute("""
    INSERT INTO shared_picks (
        share_code, pick_id, user_id, title, match_name, market, odds,
        shark_score, confidence, share_text, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        share_code, str(pick_id), str(user_id), title, match_name, market,
        float(odds), float(shark_score), confidence, share_text, now_iso()
    ))

    conn.commit()
    conn.close()

    log_commercial_event("PICK_SHARED", "APP", title, {"share_code": share_code})
    return get_shared_pick(share_code, db_path)


def get_shared_pick(share_code, db_path=DB_PATH, increment_view=False):
    conn = get_db(db_path)

    if increment_view:
        conn.execute("""
        UPDATE shared_picks
        SET views = views + 1
        WHERE share_code=?
        """, (share_code,))
        conn.commit()

    row = conn.execute("""
        SELECT * FROM shared_picks WHERE share_code=?
    """, (share_code,)).fetchone()

    conn.close()

    return dict(row) if row else None


def log_commercial_event(event_type, source, title, metadata=None, db_path=DB_PATH):
    conn = get_db(db_path)
    conn.execute("""
    INSERT INTO commercial_events (event_type, source, title, metadata, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (
        event_type,
        source,
        title,
        json.dumps(metadata or {}, ensure_ascii=False),
        now_iso()
    ))
    conn.commit()
    conn.close()


def get_commercial_status(db_path=DB_PATH):
    conn = get_db(db_path)

    profiles = conn.execute("SELECT COUNT(*) AS c FROM public_profiles").fetchone()["c"]
    shares = conn.execute("SELECT COUNT(*) AS c FROM shared_picks").fetchone()["c"]
    events = conn.execute("SELECT COUNT(*) AS c FROM commercial_events").fetchone()["c"]
    total_views = conn.execute("SELECT COALESCE(SUM(views),0) AS v FROM shared_picks").fetchone()["v"]

    top_profiles = [
        dict(r) for r in conn.execute("""
        SELECT display_name, avatar_emoji, public_roi, public_win_rate,
               public_picks, public_streak, reputation_score
        FROM public_profiles
        WHERE is_public=1
        ORDER BY reputation_score DESC
        LIMIT 10
        """).fetchall()
    ]

    recent_shared = [
        dict(r) for r in conn.execute("""
        SELECT share_code, title, match_name, market, odds, shark_score, confidence, views, created_at
        FROM shared_picks
        ORDER BY id DESC
        LIMIT 10
        """).fetchall()
    ]

    recent_events = [
        dict(r) for r in conn.execute("""
        SELECT event_type, source, title, created_at
        FROM commercial_events
        ORDER BY id DESC
        LIMIT 12
        """).fetchall()
    ]

    conn.close()

    score = min(84 + profiles * 2 + shares * 2 + min(int(total_views or 0), 20), 99)

    return {
        "status": "APP COMERCIAL READY",
        "commercial_score": score,
        "public_profiles": profiles,
        "shared_picks": shares,
        "commercial_events": events,
        "total_shared_views": int(total_views or 0),
        "top_profiles": top_profiles,
        "recent_shared": recent_shared,
        "recent_events": recent_events,
        "modules": [
            {"name": "Landing premium", "status": "ACTIVO"},
            {"name": "Onboarding comercial", "status": "ACTIVO"},
            {"name": "Perfiles públicos", "status": "ACTIVO"},
            {"name": "Compartir picks", "status": "ACTIVO"},
            {"name": "Social proof", "status": "ACTIVO"},
            {"name": "Beta comercial", "status": "ACTIVO"},
            {"name": "Mobile app feel", "status": "ACTIVO"},
        ],
    }


def get_landing_metrics():
    return {
        "headline": "La plataforma IA para detectar value en apuestas deportivas",
        "subheadline": "SHARK AI analiza picks, momentum live, riesgo, patrones y oportunidades en tiempo real.",
        "kpis": [
            {"label": "SHARK AI", "value": "V79+"},
            {"label": "Live Intelligence", "value": "Activo"},
            {"label": "Telegram", "value": "Integrado"},
            {"label": "Beta privada", "value": "Ready"},
        ],
        "features": [
            "Picks reales con score IA",
            "Live Center con momentum",
            "Alertas Telegram y Push",
            "Dashboard PRO/ELITE",
            "Analytics y ROI",
            "Aprendizaje SHARK AI",
            "Comunidad y perfiles públicos",
        ],
    }
