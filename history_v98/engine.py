"""V98 Historial Real ROI / Winrate.
Lee SQLite y Real Core sin inventar datos: si no hay picks cerrados, devuelve estado vacío seguro.
"""
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_CANDIDATES = [
    os.getenv("DB_PATH"),
    os.getenv("DATABASE_PATH"),
    os.getenv("SQLITE_DB_PATH"),
    "/data/database.db",
    "instance/nemesis.db",
    "nemesis.db",
    "app.db",
]

WIN_TERMS = {"win", "won", "green", "acierto", "ganado", "void_win"}
LOSS_TERMS = {"loss", "lost", "red", "fallo", "perdido", "void_loss"}
VOID_TERMS = {"void", "push", "cancelled", "cancelado", "nulo", "refund"}


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _db_path():
    for candidate in DB_CANDIDATES:
        if not candidate:
            continue
        p = Path(candidate)
        if p.exists():
            return p
    return None


def _connect():
    path = _db_path()
    if not path:
        return None, None
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    return con, path


def _columns(cur, table):
    try:
        cur.execute(f"PRAGMA table_info({table})")
        return [r[1] for r in cur.fetchall()]
    except Exception:
        return []


def _pick_table(cur):
    for table in ("picks", "bet_picks", "shark_picks"):
        try:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if cur.fetchone():
                return table
        except Exception:
            pass
    return None


def _value(row, *names, default=None):
    for name in names:
        try:
            val = row[name]
            if val is not None and val != "":
                return val
        except Exception:
            continue
    return default


def _float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(str(value).replace(",", "."))
    except Exception:
        return default


def _norm_result(value):
    raw = str(value or "").strip().lower()
    if raw in WIN_TERMS:
        return "WIN"
    if raw in LOSS_TERMS:
        return "LOSS"
    if raw in VOID_TERMS:
        return "VOID"
    if raw in {"pending", "open", "active", "abierto", "pendiente", ""}:
        return "PENDING"
    if "win" in raw or "green" in raw or "acierto" in raw:
        return "WIN"
    if "loss" in raw or "red" in raw or "fall" in raw or "perd" in raw:
        return "LOSS"
    if "void" in raw or "nulo" in raw or "push" in raw:
        return "VOID"
    return "PENDING"


def _profit_units(result, odds, stake):
    stake = _float(stake, 1.0) or 1.0
    odds = _float(odds, 0.0)
    if result == "WIN" and odds > 1:
        return round((odds - 1) * stake, 2)
    if result == "LOSS":
        return round(-stake, 2)
    return 0.0


def _serialize_pick(row):
    result = _norm_result(_value(row, "result", "status", "outcome", "settled_result"))
    odds = _float(_value(row, "odds", "cuota", "price"), 0)
    stake = _float(_value(row, "stake_units", "stake", "units"), 1)
    profit = _value(row, "profit_units", "profit", "pnl", default=None)
    if profit is None:
        profit = _profit_units(result, odds, stake)
    else:
        profit = _float(profit, 0)
    title = _value(row, "title", "match_name", "event", default="Partido real")
    home = _value(row, "home_team", "home", default="")
    away = _value(row, "away_team", "away", default="")
    if (not title or title == "Partido real") and (home or away):
        title = f"{home} vs {away}".strip(" vs ")
    return {
        "id": _value(row, "id", default=""),
        "title": title,
        "pick": _value(row, "pick", "selection", "market", default="Pick"),
        "league": _value(row, "league", "competition", "sport_key", default=""),
        "result": result,
        "odds": odds,
        "stake": stake,
        "profit_units": round(float(profit), 2),
        "shark_score": int(_float(_value(row, "shark_score", "score", "confidence"), 0)),
        "closed_at": _value(row, "closed_at", "settled_at", "updated_at", "created_at", default=""),
        "risk": _value(row, "risk", "riesgo", default=""),
    }


def _load_picks(limit=250):
    con, path = _connect()
    if not con:
        return [], {"db_found": False, "db_path": "No detectada en este entorno"}
    try:
        cur = con.cursor()
        table = _pick_table(cur)
        if not table:
            con.close()
            return [], {"db_found": True, "db_path": str(path), "table": None, "message": "No existe tabla de picks"}
        cols = _columns(cur, table)
        order_col = "closed_at" if "closed_at" in cols else "settled_at" if "settled_at" in cols else "updated_at" if "updated_at" in cols else "created_at" if "created_at" in cols else "id"
        sql = f"SELECT * FROM {table} ORDER BY {order_col} DESC LIMIT ?"
        cur.execute(sql, (int(limit),))
        rows = cur.fetchall()
        con.close()
        return [_serialize_pick(r) for r in rows], {"db_found": True, "db_path": str(path), "table": table, "rows_loaded": len(rows)}
    except Exception as exc:
        try:
            con.close()
        except Exception:
            pass
        return [], {"db_found": True, "db_path": str(path), "error": str(exc)}


def _aggregate(picks):
    closed = [p for p in picks if p["result"] in {"WIN", "LOSS", "VOID"}]
    graded = [p for p in closed if p["result"] in {"WIN", "LOSS"}]
    wins = len([p for p in graded if p["result"] == "WIN"])
    losses = len([p for p in graded if p["result"] == "LOSS"])
    voids = len([p for p in closed if p["result"] == "VOID"])
    stake_total = round(sum(float(p.get("stake") or 0) for p in graded), 2)
    profit = round(sum(float(p.get("profit_units") or 0) for p in graded), 2)
    roi = round((profit / stake_total * 100), 2) if stake_total else 0.0
    winrate = round((wins / len(graded) * 100), 2) if graded else 0.0
    avg_odds = round(sum(float(p.get("odds") or 0) for p in graded) / len(graded), 2) if graded else 0.0
    pending = len([p for p in picks if p["result"] == "PENDING"])
    return {
        "total_loaded": len(picks),
        "closed": len(closed),
        "graded": len(graded),
        "wins": wins,
        "losses": losses,
        "voids": voids,
        "pending": pending,
        "profit_units": profit,
        "stake_units": stake_total,
        "roi": roi,
        "winrate": winrate,
        "avg_odds": avg_odds,
    }


def _by_league(picks):
    data = {}
    for p in picks:
        if p["result"] not in {"WIN", "LOSS"}:
            continue
        key = p.get("league") or "General"
        item = data.setdefault(key, {"league": key, "picks": 0, "wins": 0, "profit_units": 0.0, "stake_units": 0.0})
        item["picks"] += 1
        item["wins"] += 1 if p["result"] == "WIN" else 0
        item["profit_units"] += float(p.get("profit_units") or 0)
        item["stake_units"] += float(p.get("stake") or 0)
    out = []
    for item in data.values():
        item["profit_units"] = round(item["profit_units"], 2)
        item["roi"] = round(item["profit_units"] / item["stake_units"] * 100, 2) if item["stake_units"] else 0
        item["winrate"] = round(item["wins"] / item["picks"] * 100, 2) if item["picks"] else 0
        out.append(item)
    return sorted(out, key=lambda x: x["profit_units"], reverse=True)[:12]


def build_history_center(limit=250):
    picks, db = _load_picks(limit=limit)
    stats = _aggregate(picks)
    closed_recent = [p for p in picks if p["result"] in {"WIN", "LOSS", "VOID"}][:40]
    pending_recent = [p for p in picks if p["result"] == "PENDING"][:20]
    return {
        "ok": True,
        "version": "V98",
        "title": "Historial Real ROI / Winrate",
        "generated_at": _now_iso(),
        "db": db,
        "stats": stats,
        "recent_closed": closed_recent,
        "pending": pending_recent,
        "by_league": _by_league(picks),
        "empty_state": stats["closed"] == 0,
        "message": "Historial calculado con picks cerrados reales" if stats["closed"] else "Aún no hay picks cerrados reales para calcular ROI/winrate. No se muestran demos.",
        "next_step": "V99 Membresías SaaS + roles premium + protección de rutas",
    }
