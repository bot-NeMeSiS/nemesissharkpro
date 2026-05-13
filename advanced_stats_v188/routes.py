
from flask import Blueprint, jsonify, request, render_template_string
import os, sqlite3, json, time, hashlib, math
from pathlib import Path

bp_advanced_stats_v188 = Blueprint("advanced_stats_v188", __name__)

def _db_path():
    return os.environ.get("DATABASE_PATH") or os.environ.get("DB_PATH") or "/data/database.db"

def _connect():
    Path(_db_path()).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(_db_path())

def _init():
    con = _connect()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS advanced_stats_snapshots_v188 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scope TEXT,
            entity_id TEXT,
            stats_json TEXT,
            created_at INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS advanced_stats_events_v188 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT,
            event TEXT,
            detail TEXT,
            created_at INTEGER
        )
    """)
    con.commit()
    con.close()

def _tables():
    con = _connect()
    try:
        return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    except Exception:
        return set()
    finally:
        con.close()

def _rows(table, limit=100):
    if table not in _tables():
        return []
    con = _connect()
    con.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in con.execute(f"SELECT * FROM {table} LIMIT {int(limit)}").fetchall()]
    except Exception:
        return []
    finally:
        con.close()

def _count(table, where="1=1"):
    if table not in _tables():
        return 0
    con = _connect()
    try:
        return con.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}").fetchone()[0]
    except Exception:
        return 0
    finally:
        con.close()

def _pick(row, names):
    lower = {str(k).lower(): k for k in row.keys()}
    for n in names:
        k = lower.get(n)
        if k and row.get(k) not in (None, ""):
            return row.get(k)
    for k in row.keys():
        lk = str(k).lower()
        if any(n in lk for n in names) and row.get(k) not in (None, ""):
            return row.get(k)
    return ""

def _num(v, default=0.0):
    try:
        if v in (None, ""):
            return default
        return float(str(v).replace(",", ".").replace("%",""))
    except Exception:
        return default

def _fixture_rows():
    out = []
    for t in ["fixtures_cache", "fixtures", "real_fixtures", "matches_cache", "matches"]:
        for r in _rows(t, 200):
            r["_source_table"] = t
            out.append(r)
    return out

def _pick_rows():
    out = []
    for t in ["picks", "real_picks", "admin_picks", "closed_picks"]:
        for r in _rows(t, 300):
            r["_source_table"] = t
            out.append(r)
    return out

def _stable(seed, base=50, spread=36):
    h = int(hashlib.md5(str(seed).encode()).hexdigest()[:6], 16)
    return max(0, min(99, base + (h % spread) - spread//2))

def _advanced_fixture_stats():
    fixtures = _fixture_rows()
    total = len(fixtures)
    live = 0
    finished = 0
    scheduled = 0
    leagues = {}
    with_score = 0
    with_odds_like = 0
    for r in fixtures:
        txt = json.dumps(r, ensure_ascii=False, default=str).lower()
        status = str(_pick(r, ["status","state","fixture_status","match_status"])).lower()
        if any(x in txt for x in ["live","in_play","inplay","1h","2h","minute","elapsed"]) or status in ["live","in_play","1h","2h"]:
            live += 1
        elif any(x in status for x in ["finish","ended","final","ft","closed"]):
            finished += 1
        else:
            scheduled += 1
        league = str(_pick(r, ["league","competition","competition_name","sport_title","liga"]) or "Sin liga")
        leagues[league] = leagues.get(league, 0) + 1
        if _pick(r, ["home_score","score_home","goals_home","away_score","score_away","goals_away"]):
            with_score += 1
        if any(x in txt for x in ["odd","odds","price","cuota","bookmaker"]):
            with_odds_like += 1
    top_leagues = sorted([{"league":k, "count":v} for k,v in leagues.items()], key=lambda x:x["count"], reverse=True)[:10]
    coverage = {
        "score_coverage": round((with_score / total) * 100, 2) if total else 0,
        "odds_coverage": round((with_odds_like / total) * 100, 2) if total else 0,
        "live_ratio": round((live / total) * 100, 2) if total else 0,
    }
    return {"total": total, "live": live, "finished": finished, "scheduled": scheduled, "top_leagues": top_leagues, "coverage": coverage}

def _advanced_pick_stats():
    picks = _pick_rows()
    total = len(picks)
    win = loss = void = pending = 0
    profit = 0.0
    stake_total = 0.0
    odds_values = []
    markets = {}
    leagues = {}
    for r in picks:
        txt = json.dumps(r, ensure_ascii=False, default=str).lower()
        result = str(_pick(r, ["result","status","outcome","estado"])).lower()
        if "win" in result or "gan" in result:
            win += 1
        elif "loss" in result or "lost" in result or "perd" in result:
            loss += 1
        elif "void" in result or "push" in result or "nulo" in result:
            void += 1
        else:
            pending += 1
        stake = _num(_pick(r, ["stake","amount","importe"]), 0)
        odds = _num(_pick(r, ["odds","odd","cuota","price"]), 0)
        p = _num(_pick(r, ["profit","benefit","beneficio","pnl"]), 0)
        if not p and stake and odds and (win or loss):
            if "win" in result or "gan" in result:
                p = stake * max(0, odds - 1)
            elif "loss" in result or "perd" in result:
                p = -stake
        profit += p
        stake_total += stake
        if odds:
            odds_values.append(odds)
        market = str(_pick(r, ["market","mercado","pick_type","selection"]) or "Sin mercado")
        markets[market] = markets.get(market, 0) + 1
        league = str(_pick(r, ["league","liga","competition"]) or "Sin liga")
        leagues[league] = leagues.get(league, 0) + 1
    settled = win + loss + void
    winrate = round((win / (win+loss))*100, 2) if (win+loss) else 0
    roi = round((profit / stake_total)*100, 2) if stake_total else 0
    avg_odds = round(sum(odds_values)/len(odds_values), 2) if odds_values else 0
    top_markets = sorted([{"market":k,"count":v} for k,v in markets.items()], key=lambda x:x["count"], reverse=True)[:10]
    top_leagues = sorted([{"league":k,"count":v} for k,v in leagues.items()], key=lambda x:x["count"], reverse=True)[:10]
    return {
        "total": total, "settled": settled, "pending": pending,
        "win": win, "loss": loss, "void": void,
        "winrate": winrate, "roi": roi, "profit": round(profit,2),
        "stake_total": round(stake_total,2), "avg_odds": avg_odds,
        "top_markets": top_markets, "top_leagues": top_leagues
    }

def _advanced_user_stats():
    tables = _tables()
    users_total = sum(_count(t) for t in ["users","clientes","clients","user"])
    favorites = sum(_count(t) for t in ["favorites","user_favorites","favorite_matches"])
    telegram = sum(_count(t) for t in ["telegram_users","telegram_links","telegram_chats","telegram_members"])
    alerts = sum(_count(t) for t in ["push_queue_v182","push_queue_v184","notification_queue_v164","live_alerts"])
    return {
        "users_total": users_total,
        "favorites_total": favorites,
        "telegram_links": telegram,
        "alerts_or_push": alerts,
        "engagement_score": min(99, 20 + favorites*3 + telegram*8 + alerts),
        "tables_detected": sorted(list(tables))[:100]
    }

def _advanced_model_ready():
    fixtures = _advanced_fixture_stats()
    picks = _advanced_pick_stats()
    user = _advanced_user_stats()
    score = 0
    reasons = []
    if fixtures["total"] >= 100:
        score += 25; reasons.append("Hay volumen razonable de fixtures.")
    elif fixtures["total"] > 0:
        score += 10; reasons.append("Hay fixtures, pero aún falta volumen.")
    else:
        reasons.append("No hay fixtures suficientes.")
    if picks["settled"] >= 200:
        score += 35; reasons.append("Hay picks cerrados suficientes para entrenar algo inicial.")
    elif picks["settled"] >= 50:
        score += 18; reasons.append("Hay picks cerrados, pero aún falta muestra.")
    else:
        reasons.append("Faltan picks cerrados WIN/LOSS/VOID para ML real.")
    if picks["avg_odds"] > 0:
        score += 10; reasons.append("Hay cuotas detectadas.")
    if user["engagement_score"] > 35:
        score += 10; reasons.append("Hay señales de engagement.")
    if fixtures["coverage"]["score_coverage"] > 25:
        score += 10; reasons.append("Hay cobertura de marcador.")
    if fixtures["coverage"]["odds_coverage"] > 25:
        score += 10; reasons.append("Hay cobertura de cuotas.")
    return {
        "ml_readiness_score": min(100, score),
        "can_train_now": score >= 65,
        "recommended_next_step": "Recolectar más histórico cerrado y normalizar features" if score < 65 else "Entrenar modelo inicial baseline",
        "reasons": reasons
    }

def _all_stats():
    return {
        "fixtures": _advanced_fixture_stats(),
        "picks": _advanced_pick_stats(),
        "users": _advanced_user_stats(),
        "ml_readiness": _advanced_model_ready(),
        "generated_at": int(time.time()),
        "policy": "No inventa xG, tiros, posesión ni eventos si no existen en datos reales. Calcula métricas sobre tablas disponibles."
    }

def _snapshot():
    _init()
    stats = _all_stats()
    con = _connect()
    con.execute("INSERT INTO advanced_stats_snapshots_v188(scope,entity_id,stats_json,created_at) VALUES(?,?,?,?)",
                ("global","latest",json.dumps(stats, ensure_ascii=False),int(time.time())))
    con.commit()
    con.close()
    return stats

@bp_advanced_stats_v188.route("/advanced-stats-pro")
@bp_advanced_stats_v188.route("/cliente/advanced-stats")
@bp_advanced_stats_v188.route("/admin/advanced-stats")
def page():
    _init()
    stats = _all_stats()
    snapshots = _count("advanced_stats_snapshots_v188")
    return render_template_string("""
<!doctype html>
<html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Advanced Stats V188 · NeMeSiS SHARK PRO</title>
<style>
:root{--bg:#06111f;--panel:#0b1c31;--line:#1b4169;--txt:#eafbff;--mut:#91b4c9;--cyan:#22d3ee;--green:#35f0a1;--gold:#ffd166;--red:#ff5b7a}
body{margin:0;background:radial-gradient(circle at top,#163f69,#06111f 52%,#02060b);font-family:Inter,system-ui,Arial;color:var(--txt)}
.wrap{max-width:1240px;margin:auto;padding:24px}.hero,.card{border:1px solid var(--line);background:rgba(11,28,49,.88);border-radius:26px;padding:22px;box-shadow:0 20px 80px rgba(0,0,0,.28)}
.badge{display:inline-flex;padding:8px 12px;border-radius:99px;background:rgba(34,211,238,.14);border:1px solid rgba(34,211,238,.35);color:#c9f9ff;font-weight:900;font-size:12px}
.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;margin-top:16px}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px}
.k{font-size:34px;font-weight:950;margin-top:6px}.mut{color:var(--mut)}.ok{color:var(--green)}.gold{color:var(--gold)}.red{color:var(--red)}
.bar{height:12px;border-radius:99px;background:#071526;border:1px solid #193b60;overflow:hidden}.fill{height:100%;background:linear-gradient(90deg,#22d3ee,#35f0a1);width:var(--w)}
.btn{display:inline-block;margin:8px 8px 0 0;padding:12px 16px;border-radius:14px;text-decoration:none;background:linear-gradient(135deg,#22d3ee,#2dd4bf);color:#021018;font-weight:950;border:0;cursor:pointer}
.btn2{background:#102a45;color:#dff8ff;border:1px solid #245078}
pre{white-space:pre-wrap;background:#05101d;border:1px solid #183759;border-radius:16px;padding:14px;color:#e6fbff;overflow:auto;max-height:420px}
li{margin:7px 0}
@media(max-width:950px){.grid,.grid2{grid-template-columns:1fr}.wrap{padding:16px}}
</style></head>
<body><div class="wrap">
 <div class="hero">
  <div class="badge">📈 V188 ADVANCED STATS PRO</div>
  <h1>Estadísticas avanzadas reales</h1>
  <p class="mut">ROI, winrate, cobertura de datos, ligas/mercados fuertes, readiness para ML y snapshots. No inventa xG/eventos si la API no los trae.</p>
  <button class="btn" onclick="snapshot()">Crear snapshot stats</button>
  <a class="btn btn2" href="/live-depth-pro">Live Depth</a>
  <a class="btn btn2" href="/data-visual-richness-pro">Data Visual</a>
  <a class="btn btn2" href="/admin/business-analytics">Business Analytics</a>
 </div>

 <div class="grid">
  <div class="card"><div class="mut">Fixtures</div><div class="k ok">{{ stats.fixtures.total }}</div></div>
  <div class="card"><div class="mut">Picks</div><div class="k gold">{{ stats.picks.total }}</div></div>
  <div class="card"><div class="mut">ROI</div><div class="k {{ 'ok' if stats.picks.roi >= 0 else 'red' }}">{{ stats.picks.roi }}%</div></div>
  <div class="card"><div class="mut">Winrate</div><div class="k">{{ stats.picks.winrate }}%</div></div>
 </div>

 <div class="grid">
  <div class="card"><div class="mut">Score coverage</div><div class="k">{{ stats.fixtures.coverage.score_coverage }}%</div><div class="bar"><div class="fill" style="--w:{{ stats.fixtures.coverage.score_coverage }}%"></div></div></div>
  <div class="card"><div class="mut">Odds coverage</div><div class="k">{{ stats.fixtures.coverage.odds_coverage }}%</div><div class="bar"><div class="fill" style="--w:{{ stats.fixtures.coverage.odds_coverage }}%"></div></div></div>
  <div class="card"><div class="mut">ML readiness</div><div class="k gold">{{ stats.ml_readiness.ml_readiness_score }}%</div><div class="bar"><div class="fill" style="--w:{{ stats.ml_readiness.ml_readiness_score }}%"></div></div></div>
  <div class="card"><div class="mut">Snapshots</div><div class="k">{{ snapshots }}</div></div>
 </div>

 <div class="grid2">
  <div class="card"><h2>Ligas detectadas</h2><pre>{{ stats.fixtures.top_leagues | tojson(indent=2) }}</pre></div>
  <div class="card"><h2>Mercados detectados</h2><pre>{{ stats.picks.top_markets | tojson(indent=2) }}</pre></div>
 </div>

 <div class="grid2">
  <div class="card">
   <h2>Machine Learning readiness</h2>
   <p class="mut">{{ stats.ml_readiness.recommended_next_step }}</p>
   <ul>{% for r in stats.ml_readiness.reasons %}<li>{{ r }}</li>{% endfor %}</ul>
  </div>
  <div class="card"><h2>JSON completo</h2><pre id="out">{{ stats | tojson(indent=2) }}</pre></div>
 </div>
</div>
<script>
async function snapshot(){
 const r=await fetch('/api/v188/advanced-stats/snapshot',{method:'POST'}).then(r=>r.json());
 document.getElementById('out').textContent=JSON.stringify(r,null,2);
}
</script>
</body></html>
    """, stats=stats, snapshots=snapshots)

@bp_advanced_stats_v188.route("/api/v188/advanced-stats")
def api_stats():
    return jsonify({"ok": True, "stats": _all_stats()})

@bp_advanced_stats_v188.route("/api/v188/advanced-stats/snapshot", methods=["POST"])
def api_snapshot():
    return jsonify({"ok": True, "snapshot": _snapshot()})

@bp_advanced_stats_v188.route("/api/v188/ml-readiness")
def api_ml_readiness():
    return jsonify({"ok": True, "ml_readiness": _advanced_model_ready()})
