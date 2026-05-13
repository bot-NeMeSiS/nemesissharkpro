
from datetime import datetime

def normalize_result_status(item):
    raw = str(item.get("result") or item.get("status") or "").upper()
    if raw in ["WIN", "WON", "GREEN", "GANADO"]:
        return "WIN"
    if raw in ["LOSS", "LOST", "RED", "PERDIDO"]:
        return "LOSS"
    if raw in ["VOID", "PUSH", "NULO", "CANCELLED", "CANCELED"]:
        return "VOID"
    return "PENDING"

def calculate_pick_result(pick):
    stake = float(pick.get("stake") or pick.get("stake_units") or 1)
    odds = float(pick.get("odds") or pick.get("price") or 0)
    result = normalize_result_status(pick)

    profit = 0
    if result == "WIN":
        profit = stake * max(odds - 1, 0)
    elif result == "LOSS":
        profit = -stake
    elif result == "VOID":
        profit = 0

    return {
        **pick,
        "normalized_result": result,
        "profit_units": round(profit, 2),
        "closed": result in ["WIN", "LOSS", "VOID"]
    }

def build_results_report(picks):
    rows = [calculate_pick_result(p) for p in (picks or [])]
    closed = [r for r in rows if r["closed"]]
    wins = [r for r in closed if r["normalized_result"] == "WIN"]
    losses = [r for r in closed if r["normalized_result"] == "LOSS"]
    stake = sum(float(r.get("stake") or r.get("stake_units") or 1) for r in closed)
    profit = sum(float(r.get("profit_units") or 0) for r in closed)
    roi = (profit / stake * 100) if stake else 0
    winrate = (len(wins) / (len(wins) + len(losses)) * 100) if (len(wins) + len(losses)) else 0

    return {
        "version": "V121_AUTO_PICK_RESULT_ENGINE",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total": len(rows),
        "closed": len(closed),
        "pending": len(rows) - len(closed),
        "wins": len(wins),
        "losses": len(losses),
        "profit_units": round(profit, 2),
        "roi": round(roi, 2),
        "winrate": round(winrate, 2),
        "rows": rows
    }
