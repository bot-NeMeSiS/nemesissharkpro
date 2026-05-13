from datetime import datetime
from collections import defaultdict

def _num(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default

def _is_win(result):
    return str(result or "").upper() in ["WIN", "WON", "GREEN", "PROFIT", "GANADO"]

def _is_loss(result):
    return str(result or "").upper() in ["LOSS", "LOST", "RED", "LOST_BET", "PERDIDO"]

def _is_void(result):
    return str(result or "").upper() in ["VOID", "PUSH", "CANCELLED", "CANCELED", "NULO"]

def normalize_pick(pick):
    stake = _num(pick.get("stake_units") or pick.get("stake") or 1, 1)
    odds = _num(pick.get("odds") or pick.get("price") or 0, 0)
    result = pick.get("result") or pick.get("status") or "PENDING"

    profit = pick.get("profit_units")
    if profit is None:
        if _is_win(result):
            profit = stake * max(odds - 1, 0)
        elif _is_loss(result):
            profit = -stake
        elif _is_void(result):
            profit = 0
        else:
            profit = 0

    return {
        **pick,
        "stake_units": stake,
        "odds": odds,
        "result": result,
        "profit_units": _num(profit, 0),
        "sport": pick.get("sport") or "unknown",
        "league": pick.get("league") or "unknown",
        "market": pick.get("market") or pick.get("pick") or "unknown",
        "risk": str(pick.get("risk") or "MEDIUM").upper(),
    }

def build_group_stats(items, group_key):
    grouped = defaultdict(list)
    for item in items:
        grouped[item.get(group_key) or "unknown"].append(item)

    rows = []
    for name, picks in grouped.items():
        closed = [p for p in picks if _is_win(p["result"]) or _is_loss(p["result"]) or _is_void(p["result"])]
        wins = sum(1 for p in closed if _is_win(p["result"]))
        losses = sum(1 for p in closed if _is_loss(p["result"]))
        stake = sum(p["stake_units"] for p in closed)
        profit = sum(p["profit_units"] for p in closed)
        roi = (profit / stake * 100) if stake else 0
        winrate = (wins / (wins + losses) * 100) if (wins + losses) else 0

        rows.append({
            group_key: name,
            "total": len(picks),
            "closed": len(closed),
            "wins": wins,
            "losses": losses,
            "stake_units": round(stake, 2),
            "profit_units": round(profit, 2),
            "roi": round(roi, 2),
            "winrate": round(winrate, 2),
        })

    return sorted(rows, key=lambda x: x["profit_units"], reverse=True)

def build_analytics_dashboard(picks):
    normalized = [normalize_pick(p) for p in (picks or [])]

    closed = [p for p in normalized if _is_win(p["result"]) or _is_loss(p["result"]) or _is_void(p["result"])]
    pending = [p for p in normalized if p not in closed]

    wins = sum(1 for p in closed if _is_win(p["result"]))
    losses = sum(1 for p in closed if _is_loss(p["result"]))
    voids = sum(1 for p in closed if _is_void(p["result"]))

    total_stake = sum(p["stake_units"] for p in closed)
    total_profit = sum(p["profit_units"] for p in closed)

    roi = (total_profit / total_stake * 100) if total_stake else 0
    winrate = (wins / (wins + losses) * 100) if (wins + losses) else 0
    avg_odds = (sum(p["odds"] for p in closed if p["odds"]) / len([p for p in closed if p["odds"]])) if closed else 0

    equity_curve = []
    balance = 0
    for idx, pick in enumerate(closed, start=1):
        balance += pick["profit_units"]
        equity_curve.append({
            "n": idx,
            "profit_units": round(balance, 2),
            "pick": pick.get("pick") or pick.get("market") or "pick"
        })

    return {
        "version": "V102_ANALYTICS_PRO",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "summary": {
            "total_picks": len(normalized),
            "closed_picks": len(closed),
            "pending_picks": len(pending),
            "wins": wins,
            "losses": losses,
            "voids": voids,
            "total_stake_units": round(total_stake, 2),
            "profit_units": round(total_profit, 2),
            "roi": round(roi, 2),
            "winrate": round(winrate, 2),
            "avg_odds": round(avg_odds, 2),
        },
        "by_sport": build_group_stats(normalized, "sport"),
        "by_league": build_group_stats(normalized, "league"),
        "by_risk": build_group_stats(normalized, "risk"),
        "by_market": build_group_stats(normalized, "market"),
        "equity_curve": equity_curve,
    }
