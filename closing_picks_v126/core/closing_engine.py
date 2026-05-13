
import os
import sqlite3
from pathlib import Path
from datetime import datetime

def _db_path():
    for value in [os.environ.get("DATABASE_PATH"), os.environ.get("DB_PATH"), "/data/app.db", "/data/database.db", "app.db", "database.db"]:
        if value:
            return value
    return "app.db"

def _connect():
    path = _db_path()
    if "/" in path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con

def ensure_schema():
    con = _connect()
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS closing_picks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        external_id TEXT,
        user_id TEXT,
        title TEXT NOT NULL,
        match_name TEXT,
        league TEXT,
        sport TEXT DEFAULT 'football',
        pick TEXT NOT NULL,
        odds REAL DEFAULT 0,
        stake REAL DEFAULT 1,
        plan TEXT DEFAULT 'PRO',
        risk TEXT DEFAULT 'MEDIUM',
        status TEXT DEFAULT 'PENDING',
        result TEXT DEFAULT 'PENDING',
        profit REAL DEFAULT 0,
        shark_score REAL DEFAULT 0,
        notes TEXT,
        created_at TEXT,
        updated_at TEXT,
        closed_at TEXT
    )
    """)
    con.commit()
    con.close()

def normalize_result(result):
    r = str(result or "PENDING").upper()
    if r in ["WIN", "WON", "GREEN", "GANADO"]:
        return "WIN"
    if r in ["LOSS", "LOST", "RED", "PERDIDO"]:
        return "LOSS"
    if r in ["VOID", "PUSH", "NULO", "CANCELLED", "CANCELED"]:
        return "VOID"
    return "PENDING"

def profit_for(result, stake, odds):
    result = normalize_result(result)
    stake = float(stake or 0)
    odds = float(odds or 0)
    if result == "WIN":
        return round(stake * max(odds - 1, 0), 2)
    if result == "LOSS":
        return round(-stake, 2)
    return 0

def create_pick(data):
    ensure_schema()
    now = datetime.utcnow().isoformat() + "Z"
    con = _connect()
    cur = con.cursor()
    cur.execute("""
    INSERT INTO closing_picks
    (external_id, user_id, title, match_name, league, sport, pick, odds, stake, plan, risk, status, result, profit, shark_score, notes, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("external_id"),
        data.get("user_id"),
        data.get("title") or data.get("match") or "Pick SHARK",
        data.get("match_name") or data.get("match") or "",
        data.get("league") or "",
        data.get("sport") or "football",
        data.get("pick") or "Sin pick",
        float(data.get("odds") or 0),
        float(data.get("stake") or 1),
        str(data.get("plan") or "PRO").upper(),
        str(data.get("risk") or "MEDIUM").upper(),
        "PENDING",
        "PENDING",
        0,
        float(data.get("shark_score") or data.get("score") or 0),
        data.get("notes") or "",
        now,
        now
    ))
    con.commit()
    pick_id = cur.lastrowid
    con.close()
    return {"ok": True, "id": pick_id}

def list_picks(status=None, limit=200):
    ensure_schema()
    con = _connect()
    cur = con.cursor()
    if status:
        cur.execute("SELECT * FROM closing_picks WHERE status=? ORDER BY id DESC LIMIT ?", (status.upper(), int(limit)))
    else:
        cur.execute("SELECT * FROM closing_picks ORDER BY id DESC LIMIT ?", (int(limit),))
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows

def close_pick(pick_id, result):
    ensure_schema()
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT * FROM closing_picks WHERE id=?", (int(pick_id),))
    row = cur.fetchone()
    if not row:
        con.close()
        return {"ok": False, "error": "Pick no encontrado"}

    result = normalize_result(result)
    profit = profit_for(result, row["stake"], row["odds"])
    status = "CLOSED" if result in ["WIN", "LOSS", "VOID"] else "PENDING"
    now = datetime.utcnow().isoformat() + "Z"

    cur.execute("""
    UPDATE closing_picks
    SET status=?, result=?, profit=?, updated_at=?, closed_at=?
    WHERE id=?
    """, (status, result, profit, now, now if status == "CLOSED" else None, int(pick_id)))
    con.commit()
    con.close()
    return {"ok": True, "id": int(pick_id), "status": status, "result": result, "profit": profit}

def bulk_close(items):
    results = []
    for item in items or []:
        pick_id = item.get("id") or item.get("pick_id")
        result = item.get("result")
        if pick_id:
            results.append(close_pick(pick_id, result))
    return {"ok": True, "closed": results}

def performance(user_id=None):
    rows = list_picks(limit=10000)
    if user_id:
        rows = [r for r in rows if str(r.get("user_id") or "") == str(user_id)]

    closed = [r for r in rows if str(r.get("status")).upper() == "CLOSED"]
    pending = [r for r in rows if str(r.get("status")).upper() != "CLOSED"]
    wins = [r for r in closed if str(r.get("result")).upper() == "WIN"]
    losses = [r for r in closed if str(r.get("result")).upper() == "LOSS"]
    voids = [r for r in closed if str(r.get("result")).upper() == "VOID"]

    stake = sum(float(r.get("stake") or 0) for r in closed)
    profit = sum(float(r.get("profit") or 0) for r in closed)
    roi = (profit / stake * 100) if stake else 0
    winrate = (len(wins) / (len(wins) + len(losses)) * 100) if (len(wins) + len(losses)) else 0

    by_plan = {}
    by_league = {}
    for r in closed:
        for bucket, key in [(by_plan, r.get("plan") or "UNKNOWN"), (by_league, r.get("league") or "UNKNOWN")]:
            bucket.setdefault(key, {"count": 0, "profit": 0, "stake": 0})
            bucket[key]["count"] += 1
            bucket[key]["profit"] += float(r.get("profit") or 0)
            bucket[key]["stake"] += float(r.get("stake") or 0)

    def finalize(bucket):
        out = []
        for k, v in bucket.items():
            stake = v["stake"]
            out.append({
                "name": k,
                "count": v["count"],
                "profit": round(v["profit"], 2),
                "stake": round(stake, 2),
                "roi": round((v["profit"] / stake * 100) if stake else 0, 2)
            })
        return sorted(out, key=lambda x: x["profit"], reverse=True)

    return {
        "version": "V126_CLOSING_PICKS_PRO",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total": len(rows),
        "closed": len(closed),
        "pending": len(pending),
        "wins": len(wins),
        "losses": len(losses),
        "voids": len(voids),
        "stake": round(stake, 2),
        "profit": round(profit, 2),
        "roi": round(roi, 2),
        "winrate": round(winrate, 2),
        "by_plan": finalize(by_plan),
        "by_league": finalize(by_league),
        "recent": rows[:25],
    }
