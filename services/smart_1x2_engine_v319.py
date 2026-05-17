
import os, sqlite3
from pathlib import Path

DB_PATH = os.getenv("DATABASE_PATH") or os.getenv("DB_PATH") or "/data/database.db"

def discover_real_1x2_matches(limit=20):
    try:
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r["name"] for r in cur.fetchall()]
        out = []
        for table in tables:
            if not any(k in table.lower() for k in ["match","fixture","event","odds","partido"]):
                continue
            cur.execute(f"PRAGMA table_info({table})")
            cols = [r["name"] for r in cur.fetchall()]
            home = next((c for c in ["home_team","home","local_team","team_home","home_name"] if c in cols), None)
            away = next((c for c in ["away_team","away","visitor_team","team_away","away_name"] if c in cols), None)
            if not home or not away:
                continue
            league = next((c for c in ["league","competition","sport_key","liga"] if c in cols), None)
            odd1 = next((c for c in ["odd_1","home_odd","cuota_1","odds_home"] if c in cols), None)
            oddx = next((c for c in ["odd_x","draw_odd","cuota_x","odds_draw"] if c in cols), None)
            odd2 = next((c for c in ["odd_2","away_odd","cuota_2","odds_away"] if c in cols), None)
            select = [home, away] + [c for c in [league, odd1, oddx, odd2] if c]
            cur.execute(f"SELECT {', '.join(select)} FROM {table} LIMIT ?", (limit,))
            for r in cur.fetchall():
                item = {
                    "home": str(r[home] or ""),
                    "away": str(r[away] or ""),
                    "league": str(r[league] or "") if league else "",
                    "odd_1": r[odd1] if odd1 else None,
                    "odd_x": r[oddx] if oddx else None,
                    "odd_2": r[odd2] if odd2 else None,
                    "source_table": table,
                }
                item["recommendation"] = recommend(item)
                out.append(item)
                if len(out) >= limit:
                    break
            if len(out) >= limit:
                break
        con.close()
        return {"ok": True, "count": len(out), "matches": out, "low_data": len(out)==0, "real_only": True}
    except Exception as e:
        return {"ok": False, "error": str(e), "matches": [], "low_data": True, "real_only": True}

def f(v):
    try:
        return float(v)
    except Exception:
        return None

def recommend(item):
    odds = [("1", f(item.get("odd_1"))), ("X", f(item.get("odd_x"))), ("2", f(item.get("odd_2")))]
    if any(o is None for _, o in odds):
        return {"pick":"LOW DATA","risk":"Esperar","reason":"Faltan cuotas 1X2 reales.","score":None}
    pick, odd = min(odds, key=lambda x: x[1])
    return {"pick":pick,"odd":odd,"risk":"Bajo" if odd <= 1.65 else "Medio" if odd <= 2.25 else "Alto","reason":"Cuota 1X2 real más baja disponible.","score":max(45,min(92,int(100-(odd*18))))}

def build_combi_summary(matches, max_legs=3):
    legs, total = [], 1.0
    for m in matches:
        rec = m.get("recommendation") or {}
        if rec.get("pick") in ["1","X","2"] and rec.get("odd"):
            legs.append({"home":m.get("home"),"away":m.get("away"),"pick":rec.get("pick"),"odd":rec.get("odd"),"risk":rec.get("risk")})
            total *= float(rec.get("odd"))
        if len(legs) >= max_legs:
            break
    return {"ok": bool(legs), "legs": legs, "total_odd": round(total,2) if legs else None, "message": "Combi calculada con cuotas reales." if legs else "LOW DATA: no hay cuotas 1X2 reales suficientes."}
