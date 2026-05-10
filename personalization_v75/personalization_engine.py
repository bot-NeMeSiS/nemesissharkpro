
import sqlite3
from datetime import datetime, timedelta
from collections import Counter

DB_PATH = "nemesis.db"

def get_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def now_iso():
    return datetime.utcnow().isoformat()

def infer_user_profile(user_id, db_path=DB_PATH):
    conn = get_db(db_path)
    uid = str(user_id or "anonymous")

    events = conn.execute("""
        SELECT event_type, event_value, page, created_at
        FROM user_engagement_events
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 300
    """, (uid,)).fetchall()

    sports = []
    markets = []
    leagues = []

    for e in events:
        value = (e["event_value"] or "").lower()
        page = (e["page"] or "").lower()
        text = value + " " + page

        for sport in ["fútbol", "football", "soccer", "basket", "tenis", "nba", "mlb", "nhl"]:
            if sport in text:
                sports.append("Fútbol" if sport in ["fútbol", "football", "soccer"] else sport.upper())

        for market in ["over", "under", "1x2", "moneyline", "handicap", "ambos marcan"]:
            if market in text:
                markets.append(market.upper())

        for league in ["premier", "laliga", "champions", "nba", "serie a", "bundesliga"]:
            if league in text:
                leagues.append(league.title())

    favorite_sport = Counter(sports).most_common(1)[0][0] if sports else "Fútbol"
    favorite_market = Counter(markets).most_common(1)[0][0] if markets else "1X2"
    favorite_league = Counter(leagues).most_common(1)[0][0] if leagues else "General"

    engagement = 0
    try:
        row = conn.execute("""
            SELECT engagement_score FROM user_retention_profiles WHERE user_id=?
        """, (uid,)).fetchone()
        engagement = float(row["engagement_score"] or 0) if row else 0
    except Exception:
        engagement = len(events)

    risk_preference = "ALTO" if engagement >= 75 else "MEDIO" if engagement >= 35 else "BAJO"
    recommended_plan = "ELITE" if engagement >= 75 else "PRO"

    personalization_score = min(round(35 + len(events) * 1.5 + engagement * 0.5, 2), 100)

    conn.execute("""
    INSERT INTO user_personalization_profiles (
        user_id, favorite_sport, favorite_league, favorite_market,
        risk_preference, recommended_plan, personalization_score, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(user_id) DO UPDATE SET
        favorite_sport=excluded.favorite_sport,
        favorite_league=excluded.favorite_league,
        favorite_market=excluded.favorite_market,
        risk_preference=excluded.risk_preference,
        recommended_plan=excluded.recommended_plan,
        personalization_score=excluded.personalization_score,
        updated_at=excluded.updated_at
    """, (
        uid, favorite_sport, favorite_league, favorite_market,
        risk_preference, recommended_plan, personalization_score, now_iso()
    ))

    conn.commit()
    conn.close()

    return get_personalization_payload(uid, db_path)

def create_recommendation(user_id, rec_type, title, message, priority="NORMAL", db_path=DB_PATH):
    conn = get_db(db_path)
    conn.execute("""
    INSERT INTO user_recommendations (
        user_id, recommendation_type, title, message, priority, status, created_at
    ) VALUES (?, ?, ?, ?, ?, 'ACTIVE', ?)
    """, (str(user_id), rec_type, title, message, priority, now_iso()))
    conn.commit()
    conn.close()

def refresh_recommendations(user_id, db_path=DB_PATH):
    payload = infer_user_profile(user_id, db_path)
    profile = payload["profile"]
    conn = get_db(db_path)

    existing = conn.execute("""
        SELECT COUNT(*) AS c FROM user_recommendations
        WHERE user_id=? AND status='ACTIVE'
    """, (str(user_id),)).fetchone()["c"]

    if existing < 3:
        create_recommendation(
            user_id,
            "SPORT_FOCUS",
            f"Zona recomendada: {profile['favorite_sport']}",
            f"Tu actividad encaja mejor con picks de {profile['favorite_sport']} y mercado {profile['favorite_market']}.",
            "HIGH" if profile["personalization_score"] >= 70 else "NORMAL",
            db_path,
        )
        create_recommendation(
            user_id,
            "SMART_ALERT",
            "Activa alertas inteligentes",
            f"Te avisaremos cuando haya picks de {profile['favorite_league']} con score alto.",
            "NORMAL",
            db_path,
        )
        create_recommendation(
            user_id,
            "PLAN_HINT",
            f"Plan sugerido: {profile['recommended_plan']}",
            "Según tu uso, este plan encaja mejor con tu perfil.",
            "LOW",
            db_path,
        )

    conn.close()
    return get_personalization_payload(user_id, db_path)

def get_personalization_payload(user_id, db_path=DB_PATH):
    conn = get_db(db_path)
    uid = str(user_id or "anonymous")
    row = conn.execute("""
        SELECT * FROM user_personalization_profiles WHERE user_id=?
    """, (uid,)).fetchone()

    if not row:
        profile = {
            "user_id": uid,
            "favorite_sport": "Fútbol",
            "favorite_league": "General",
            "favorite_market": "1X2",
            "risk_preference": "MEDIO",
            "recommended_plan": "PRO",
            "personalization_score": 0,
        }
    else:
        profile = dict(row)

    recommendations = [
        dict(r) for r in conn.execute("""
        SELECT recommendation_type, title, message, priority, created_at
        FROM user_recommendations
        WHERE user_id=? AND status='ACTIVE'
        ORDER BY id DESC
        LIMIT 8
        """, (uid,)).fetchall()
    ]

    conn.close()
    return {
        "user_id": uid,
        "profile": profile,
        "recommendations": recommendations,
        "status": "PERSONALIZACIÓN ACTIVA" if profile.get("personalization_score", 0) else "APRENDIENDO PERFIL",
    }

def get_personalization_admin_status(db_path=DB_PATH):
    conn = get_db(db_path)

    total_profiles = conn.execute("SELECT COUNT(*) AS c FROM user_personalization_profiles").fetchone()["c"]
    total_recommendations = conn.execute("SELECT COUNT(*) AS c FROM user_recommendations WHERE status='ACTIVE'").fetchone()["c"]
    avg_score = conn.execute("SELECT COALESCE(AVG(personalization_score),0) AS v FROM user_personalization_profiles").fetchone()["v"]

    top_profiles = [
        dict(r) for r in conn.execute("""
        SELECT user_id, favorite_sport, favorite_league, favorite_market,
               risk_preference, recommended_plan, personalization_score
        FROM user_personalization_profiles
        ORDER BY personalization_score DESC
        LIMIT 10
        """).fetchall()
    ]

    conn.close()

    score = min(round(70 + float(avg_score or 0) * 0.3, 2), 100)

    return {
        "status": "PERSONALIZATION READY",
        "personalization_score": score,
        "total_profiles": total_profiles,
        "active_recommendations": total_recommendations,
        "avg_profile_score": round(float(avg_score or 0), 2),
        "top_profiles": top_profiles,
        "modules": [
            {"name": "Perfil automático", "status": "ACTIVO"},
            {"name": "Recomendaciones inteligentes", "status": "ACTIVO"},
            {"name": "Alertas por comportamiento", "status": "ACTIVO"},
            {"name": "Plan sugerido", "status": "ACTIVO"},
        ],
    }
