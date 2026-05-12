
import sqlite3
import os
from pathlib import Path
from datetime import datetime

def _db_path():
    for value in [os.environ.get("DATABASE_PATH"), os.environ.get("DB_PATH"), "/data/app.db", "/data/database.db", "app.db", "database.db"]:
        if value:
            return value
    return "app.db"

def _connect():
    path = _db_path()
    Path(path).parent.mkdir(parents=True, exist_ok=True) if "/" in path else None
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con

def ensure_picks_manager_schema():
    con = _connect()
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS managed_picks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        match_name TEXT,
        league TEXT,
        sport TEXT DEFAULT 'football',
        pick TEXT NOT NULL,
        odds REAL,
        stake REAL DEFAULT 1,
        risk TEXT DEFAULT 'MEDIUM',
        plan TEXT DEFAULT 'PRO',
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

def create_pick(data):
    ensure_picks_manager_schema()
    now = datetime.utcnow().isoformat() + "Z"
    con = _connect()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO managed_picks
        (title, match_name, league, sport, pick, odds, stake, risk, plan, status, result, profit, shark_score, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("title") or data.get("pick") or "Pick SHARK",
        data.get("match_name") or data.get("match") or "",
        data.get("league") or "",
        data.get("sport") or "football",
        data.get("pick") or "Sin pick",
        float(data.get("odds") or 0),
        float(data.get("stake") or 1),
        str(data.get("risk") or "MEDIUM").upper(),
        str(data.get("plan") or "PRO").upper(),
        "PENDING",
        "PENDING",
        0,
        float(data.get("shark_score") or data.get("score") or 0),
        data.get("notes") or "",
        now,
        now,
    ))
    con.commit()
    pick_id = cur.lastrowid
    con.close()
    return {"ok": True, "id": pick_id}

def list_picks(limit=100):
    ensure_picks_manager_schema()
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT * FROM managed_picks ORDER BY id DESC LIMIT ?", (int(limit),))
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows

def close_pick(pick_id, result):
    ensure_picks_manager_schema()
    result = str(result or "VOID").upper()
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT * FROM managed_picks WHERE id=?", (pick_id,))
    row = cur.fetchone()
    if not row:
        con.close()
        return {"ok": False, "error": "Pick no encontrado"}

    stake = float(row["stake"] or 0)
    odds = float(row["odds"] or 0)
    profit = 0
    if result in ["WIN", "WON", "GREEN", "GANADO"]:
        profit = stake * max(odds - 1, 0)
        status = "CLOSED"
    elif result in ["LOSS", "LOST", "RED", "PERDIDO"]:
        profit = -stake
        status = "CLOSED"
    elif result in ["VOID", "PUSH", "NULO"]:
        profit = 0
        status = "CLOSED"
    else:
        status = "PENDING"
        result = "PENDING"

    now = datetime.utcnow().isoformat() + "Z"
    cur.execute("""
        UPDATE managed_picks
        SET status=?, result=?, profit=?, updated_at=?, closed_at=?
        WHERE id=?
    """, (status, result, profit, now, now if status == "CLOSED" else None, pick_id))
    con.commit()
    con.close()
    return {"ok": True, "id": pick_id, "result": result, "profit": round(profit, 2)}

def analytics():
    rows = list_picks(10000)
    closed = [r for r in rows if str(r.get("status")).upper() == "CLOSED"]
    wins = [r for r in closed if str(r.get("result")).upper() in ["WIN", "WON", "GREEN", "GANADO"]]
    losses = [r for r in closed if str(r.get("result")).upper() in ["LOSS", "LOST", "RED", "PERDIDO"]]
    stake = sum(float(r.get("stake") or 0) for r in closed)
    profit = sum(float(r.get("profit") or 0) for r in closed)
    roi = (profit / stake * 100) if stake else 0
    winrate = (len(wins) / (len(wins) + len(losses)) * 100) if (len(wins) + len(losses)) else 0
    return {
        "total": len(rows),
        "closed": len(closed),
        "pending": len(rows) - len(closed),
        "wins": len(wins),
        "losses": len(losses),
        "stake": round(stake, 2),
        "profit": round(profit, 2),
        "roi": round(roi, 2),
        "winrate": round(winrate, 2),
    }
