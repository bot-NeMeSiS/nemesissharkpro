
import sqlite3
from datetime import datetime, timedelta

DB_PATH = "nemesis.db"

def get_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def now_iso():
    return datetime.utcnow().isoformat()

def add_community_activity(activity_type, user_id, title, message, visibility="PUBLIC", db_path=DB_PATH):
    conn = get_db(db_path)
    conn.execute("""
    INSERT INTO community_activity (activity_type, user_id, title, message, visibility, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (activity_type, str(user_id or "system"), title, message, visibility, now_iso()))
    conn.commit()
    conn.close()

def track_popular_pick(pick_id, sport="", match_name="", market="", action="view", db_path=DB_PATH):
    conn = get_db(db_path)
    row = conn.execute("SELECT id, views, favorites FROM popular_picks WHERE pick_id=?", (str(pick_id),)).fetchone()
    if row:
        views = int(row["views"] or 0) + (1 if action == "view" else 0)
        favs = int(row["favorites"] or 0) + (1 if action == "favorite" else 0)
        heat = views * 1.0 + favs * 3.5
        conn.execute("""
        UPDATE popular_picks SET views=?, favorites=?, heat_score=? WHERE id=?
        """, (views, favs, heat, row["id"]))
    else:
        views = 1 if action == "view" else 0
        favs = 1 if action == "favorite" else 0
        heat = views + favs * 3.5
        conn.execute("""
        INSERT INTO popular_picks (pick_id, sport, match_name, market, views, favorites, heat_score, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (str(pick_id), sport, match_name, market, views, favs, heat, now_iso()))
    conn.commit()
    conn.close()

def rebuild_leaderboard(db_path=DB_PATH):
    conn = get_db(db_path)

    users = []
    try:
        users = conn.execute("SELECT DISTINCT user_id FROM user_retention_profiles").fetchall()
    except Exception:
        users = []

    updated = 0
    for u in users:
        uid = str(u["user_id"])
        profile = None
        try:
            profile = conn.execute("SELECT engagement_score, current_streak FROM user_retention_profiles WHERE user_id=?", (uid,)).fetchone()
        except Exception:
            pass
        engagement = float(profile["engagement_score"] or 0) if profile else 0
        streak = int(profile["current_streak"] or 0) if profile else 0

        roi = round((engagement - 45) * 0.4, 2)
        win_rate = min(round(45 + engagement * 0.35, 2), 88)
        picks_count = max(int(engagement / 3), 1)
        rank_score = round(engagement + max(roi, 0) + streak * 2, 2)

        conn.execute("""
        INSERT INTO user_leaderboard_stats (
            user_id, display_name, roi, win_rate, picks_count, streak, rank_score, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            roi=excluded.roi, win_rate=excluded.win_rate, picks_count=excluded.picks_count,
            streak=excluded.streak, rank_score=excluded.rank_score, updated_at=excluded.updated_at
        """, (uid, f"SHARK User {uid[-4:]}", roi, win_rate, picks_count, streak, rank_score, now_iso()))
        updated += 1

    conn.commit()
    conn.close()
    return {"ok": True, "updated": updated}

def get_community_status(db_path=DB_PATH):
    conn = get_db(db_path)

    total_activity = conn.execute("SELECT COUNT(*) AS c FROM community_activity").fetchone()["c"]
    total_popular = conn.execute("SELECT COUNT(*) AS c FROM popular_picks").fetchone()["c"]
    total_leaderboard = conn.execute("SELECT COUNT(*) AS c FROM user_leaderboard_stats").fetchone()["c"]

    activity = [dict(r) for r in conn.execute("""
        SELECT activity_type, title, message, created_at FROM community_activity
        ORDER BY id DESC LIMIT 12
    """).fetchall()]

    popular = [dict(r) for r in conn.execute("""
        SELECT pick_id, sport, match_name, market, views, favorites, heat_score
        FROM popular_picks ORDER BY heat_score DESC LIMIT 10
    """).fetchall()]

    leaderboard = [dict(r) for r in conn.execute("""
        SELECT display_name, roi, win_rate, picks_count, streak, rank_score
        FROM user_leaderboard_stats ORDER BY rank_score DESC LIMIT 10
    """).fetchall()]

    conn.close()

    score = min(70 + total_activity * 2 + total_popular * 3 + total_leaderboard * 2, 100)

    return {
        "status": "COMUNIDAD ACTIVA" if (total_activity or total_popular or total_leaderboard) else "PREPARADO PARA COMUNIDAD",
        "community_score": score,
        "total_activity": total_activity,
        "total_popular_picks": total_popular,
        "leaderboard_users": total_leaderboard,
        "activity": activity,
        "popular": popular,
        "leaderboard": leaderboard,
    }
