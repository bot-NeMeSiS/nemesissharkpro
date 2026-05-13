
from flask import Blueprint, jsonify, request, render_template_string, Response
import os, sqlite3, json, time, hashlib, csv, io
from pathlib import Path

bp_data_collection_engine_v190 = Blueprint("data_collection_engine_v190", __name__)

def _db_path():
    return os.environ.get("DATABASE_PATH") or os.environ.get("DB_PATH") or "/data/database.db"

def _connect():
    Path(_db_path()).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(_db_path())

def _init():
    con = _connect()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS data_snapshots_v190 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_type TEXT,
            entity_id TEXT,
            source_table TEXT,
            entity_hash TEXT,
            payload_json TEXT,
            quality_score INTEGER DEFAULT 0,
            created_at INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS odds_history_v190 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id TEXT,
            market TEXT,
            selection TEXT,
            bookmaker TEXT,
            odds REAL,
            source_table TEXT,
            raw_json TEXT,
            created_at INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS result_history_v190 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id TEXT,
            home TEXT,
            away TEXT,
            league TEXT,
            status TEXT,
            home_score REAL,
            away_score REAL,
            result_label TEXT,
            source_table TEXT,
            raw_json TEXT,
            created_at INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pick_lifecycle_v190 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pick_id TEXT,
            match_id TEXT,
            market TEXT,
            selection TEXT,
            odds REAL,
            stake REAL,
            status TEXT,
            result_label TEXT,
            profit REAL,
            source_table TEXT,
            raw_json TEXT,
            created_at INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS data_collection_runs_v190 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name TEXT,
            status TEXT,
            collected_snapshots INTEGER DEFAULT 0,
            collected_odds INTEGER DEFAULT 0,
            collected_results INTEGER DEFAULT 0,
            collected_picks INTEGER DEFAULT 0,
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

def _rows(table, limit=1000):
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

def _num(v, default=None):
    try:
        if v in (None, ""):
            return default
        return float(str(v).replace(",", ".").replace("%",""))
    except Exception:
        return default

def _hash(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str, ensure_ascii=False).encode("utf-8")).hexdigest()

def _quality(row, kind):
    txt = json.dumps(row, ensure_ascii=False, default=str).lower()
    q = 10
    if kind == "fixture":
        if _pick(row, ["home_team","home","team_home","home_name","local"]): q += 15
        if _pick(row, ["away_team","away","team_away","away_name","visitor","visitante"]): q += 15
        if _pick(row, ["league","competition","competition_name","sport_title","liga"]): q += 15
        if _pick(row, ["status","state","fixture_status","match_status"]): q += 10
        if _pick(row, ["home_score","score_home","goals_home","away_score","score_away","goals_away"]): q += 20
        if any(x in txt for x in ["odd","odds","price","cuota","bookmaker"]): q += 20
    elif kind == "pick":
        if _pick(row, ["market","mercado","pick_type","selection"]): q += 20
        if _pick(row, ["odds","odd","cuota","price"]): q += 20
        if _pick(row, ["stake","amount","importe"]): q += 15
        if _pick(row, ["result","status","outcome","estado"]): q += 25
        if _pick(row, ["league","liga","competition"]): q += 10
    return min(100, q)

def _fixture_tables():
    return ["fixtures_cache", "fixtures", "real_fixtures", "matches_cache", "matches"]

def _pick_tables():
    return ["picks", "real_picks", "admin_picks", "closed_picks"]

def _collect_snapshots():
    _init()
    con = _connect()
    now = int(time.time())
    total = 0
    for table in _fixture_tables():
        for row in _rows(table, 1500):
            entity_id = str(_pick(row, ["id","fixture_id","match_id","event_id"]) or _hash(row)[:12])
            payload = dict(row)
            h = _hash({"type":"fixture","table":table,"entity":entity_id,"payload":payload})
            con.execute("""
                INSERT INTO data_snapshots_v190(snapshot_type,entity_id,source_table,entity_hash,payload_json,quality_score,created_at)
                VALUES(?,?,?,?,?,?,?)
            """, ("fixture", entity_id, table, h, json.dumps(payload, ensure_ascii=False, default=str), _quality(row, "fixture"), now))
            total += 1
    for table in _pick_tables():
        for row in _rows(table, 1500):
            entity_id = str(_pick(row, ["id","pick_id","match_id","fixture_id","event_id"]) or _hash(row)[:12])
            payload = dict(row)
            h = _hash({"type":"pick","table":table,"entity":entity_id,"payload":payload})
            con.execute("""
                INSERT INTO data_snapshots_v190(snapshot_type,entity_id,source_table,entity_hash,payload_json,quality_score,created_at)
                VALUES(?,?,?,?,?,?,?)
            """, ("pick", entity_id, table, h, json.dumps(payload, ensure_ascii=False, default=str), _quality(row, "pick"), now))
            total += 1
    con.commit()
    con.close()
    return total

def _collect_odds():
    _init()
    con = _connect()
    now = int(time.time())
    total = 0
    for table in _fixture_tables() + _pick_tables():
        for row in _rows(table, 1500):
            raw = json.dumps(row, ensure_ascii=False, default=str)
            odds = _num(_pick(row, ["odds","odd","cuota","price"]), None)
            if odds is None and not any(x in raw.lower() for x in ["odds","odd","cuota","price"]):
                continue
            match_id = str(_pick(row, ["match_id","fixture_id","event_id","id"]) or _hash(row)[:12])
            market = str(_pick(row, ["market","mercado","pick_type"]) or "unknown")
            selection = str(_pick(row, ["selection","pick","pronostico","bet"]) or "")
            bookmaker = str(_pick(row, ["bookmaker","book","casa"]) or "")
            con.execute("""
                INSERT INTO odds_history_v190(match_id,market,selection,bookmaker,odds,source_table,raw_json,created_at)
                VALUES(?,?,?,?,?,?,?,?)
            """, (match_id, market, selection, bookmaker, odds or 0, table, raw, now))
            total += 1
    con.commit()
    con.close()
    return total

def _collect_results():
    _init()
    con = _connect()
    now = int(time.time())
    total = 0
    for table in _fixture_tables():
        for row in _rows(table, 1500):
            home = str(_pick(row, ["home_team","home","team_home","home_name","local"]) or "")
            away = str(_pick(row, ["away_team","away","team_away","away_name","visitor","visitante"]) or "")
            league = str(_pick(row, ["league","competition","competition_name","sport_title","liga"]) or "")
            status = str(_pick(row, ["status","state","fixture_status","match_status"]) or "")
            hs = _num(_pick(row, ["home_score","score_home","goals_home","home_goals"]), None)
            as_ = _num(_pick(row, ["away_score","score_away","goals_away","away_goals"]), None)
            if hs is None or as_ is None:
                continue
            label = "DRAW"
            if hs > as_: label = "HOME_WIN"
            elif hs < as_: label = "AWAY_WIN"
            match_id = str(_pick(row, ["id","fixture_id","match_id","event_id"]) or _hash(row)[:12])
            con.execute("""
                INSERT INTO result_history_v190(match_id,home,away,league,status,home_score,away_score,result_label,source_table,raw_json,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """, (match_id, home, away, league, status, hs, as_, label, table, json.dumps(row, ensure_ascii=False, default=str), now))
            total += 1
    con.commit()
    con.close()
    return total

def _collect_pick_lifecycle():
    _init()
    con = _connect()
    now = int(time.time())
    total = 0
    for table in _pick_tables():
        for row in _rows(table, 1500):
            pick_id = str(_pick(row, ["id","pick_id"]) or _hash(row)[:12])
            match_id = str(_pick(row, ["match_id","fixture_id","event_id"]) or "")
            market = str(_pick(row, ["market","mercado","pick_type"]) or "")
            selection = str(_pick(row, ["selection","pick","pronostico","bet"]) or "")
            odds = _num(_pick(row, ["odds","odd","cuota","price"]), 0)
            stake = _num(_pick(row, ["stake","amount","importe"]), 0)
            status = str(_pick(row, ["status","estado"]) or "")
            result_raw = str(_pick(row, ["result","outcome","estado","status"]) or "").lower()
            label = ""
            if "win" in result_raw or "gan" in result_raw: label = "WIN"
            elif "loss" in result_raw or "perd" in result_raw or "lost" in result_raw: label = "LOSS"
            elif "void" in result_raw or "nulo" in result_raw or "push" in result_raw: label = "VOID"
            profit = _num(_pick(row, ["profit","benefit","beneficio","pnl"]), None)
            if profit is None:
                if label == "WIN" and stake and odds: profit = stake * max(0, odds-1)
                elif label == "LOSS" and stake: profit = -stake
                elif label == "VOID": profit = 0
                else: profit = 0
            con.execute("""
                INSERT INTO pick_lifecycle_v190(pick_id,match_id,market,selection,odds,stake,status,result_label,profit,source_table,raw_json,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """, (pick_id, match_id, market, selection, odds, stake, status, label, profit, table, json.dumps(row, ensure_ascii=False, default=str), now))
            total += 1
    con.commit()
    con.close()
    return total

def _run_collection(job_name="manual"):
    start = time.time()
    try:
        snapshots = _collect_snapshots()
        odds = _collect_odds()
        results = _collect_results()
        picks = _collect_pick_lifecycle()
        status = "ok"
        detail = f"Collection completed in {int((time.time()-start)*1000)}ms"
    except Exception as e:
        snapshots = odds = results = picks = 0
        status = "error"
        detail = str(e)
    con = _connect()
    con.execute("""
        INSERT INTO data_collection_runs_v190(job_name,status,collected_snapshots,collected_odds,collected_results,collected_picks,detail,created_at)
        VALUES(?,?,?,?,?,?,?,?)
    """, (job_name, status, snapshots, odds, results, picks, detail, int(time.time())))
    con.commit()
    con.close()
    return {"status": status, "snapshots": snapshots, "odds": odds, "results": results, "picks": picks, "detail": detail}

def _status():
    _init()
    con = _connect()
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    def one(sql):
        try:
            return cur.execute(sql).fetchone()[0]
        except Exception:
            return 0
    recent = []
    try:
        for r in cur.execute("SELECT job_name,status,collected_snapshots,collected_odds,collected_results,collected_picks,detail,created_at FROM data_collection_runs_v190 ORDER BY id DESC LIMIT 12"):
            recent.append(dict(r))
    except Exception:
        pass
    data = {
        "source_tables": {
            "fixtures_rows": sum(len(_rows(t, 2000)) for t in _fixture_tables()),
            "picks_rows": sum(len(_rows(t, 2000)) for t in _pick_tables()),
            "tables_detected": sorted(list(_tables()))[:120]
        },
        "warehouse": {
            "snapshots": one("SELECT COUNT(*) FROM data_snapshots_v190"),
            "fixture_snapshots": one("SELECT COUNT(*) FROM data_snapshots_v190 WHERE snapshot_type='fixture'"),
            "pick_snapshots": one("SELECT COUNT(*) FROM data_snapshots_v190 WHERE snapshot_type='pick'"),
            "odds_history": one("SELECT COUNT(*) FROM odds_history_v190"),
            "result_history": one("SELECT COUNT(*) FROM result_history_v190"),
            "pick_lifecycle": one("SELECT COUNT(*) FROM pick_lifecycle_v190"),
            "avg_quality": round(one("SELECT COALESCE(AVG(quality_score),0) FROM data_snapshots_v190"), 2)
        },
        "runs": recent,
        "ml_value": {
            "ready_for_ml_pipeline": one("SELECT COUNT(*) FROM result_history_v190") > 50 or one("SELECT COUNT(*) FROM pick_lifecycle_v190 WHERE result_label IN ('WIN','LOSS','VOID')") > 50,
            "value_note": "Cuanto más histórico cerrado y cuotas guardes, más valor tendrá el dataset."
        },
        "policy": "Guarda histórico real y snapshots. No inventa datos deportivos."
    }
    con.close()
    return data

@bp_data_collection_engine_v190.route("/data-collection-engine-pro")
@bp_data_collection_engine_v190.route("/admin/data-collection")
@bp_data_collection_engine_v190.route("/admin/data-engine")
def page():
    data = _status()
    score = min(100, int((data["warehouse"]["snapshots"] / 50) + (data["warehouse"]["odds_history"] / 20) + (data["warehouse"]["result_history"] / 10) + (data["warehouse"]["pick_lifecycle"] / 10)))
    return render_template_string("""
<!doctype html>
<html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Data Collection Engine V190 · NeMeSiS SHARK PRO</title>
<style>
:root{--bg:#06111f;--panel:#0b1c31;--line:#1b4169;--txt:#eafbff;--mut:#91b4c9;--cyan:#22d3ee;--green:#35f0a1;--gold:#ffd166;--red:#ff5b7a}
body{margin:0;background:radial-gradient(circle at top,#153d68,#06111f 52%,#02060b);font-family:Inter,system-ui,Arial;color:var(--txt)}
.wrap{max-width:1240px;margin:auto;padding:24px}.hero,.card{border:1px solid var(--line);background:rgba(11,28,49,.88);border-radius:26px;padding:22px;box-shadow:0 20px 80px rgba(0,0,0,.28)}
.badge{display:inline-flex;padding:8px 12px;border-radius:99px;background:rgba(34,211,238,.14);border:1px solid rgba(34,211,238,.35);color:#c9f9ff;font-weight:900;font-size:12px}
.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;margin-top:16px}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px}
.k{font-size:34px;font-weight:950;margin-top:6px}.mut{color:var(--mut)}.ok{color:var(--green)}.gold{color:var(--gold)}.red{color:var(--red)}
.bar{height:12px;border-radius:99px;background:#071526;border:1px solid #193b60;overflow:hidden}.fill{height:100%;background:linear-gradient(90deg,#22d3ee,#35f0a1);width:var(--w)}
.btn{display:inline-block;margin:8px 8px 0 0;padding:12px 16px;border-radius:14px;text-decoration:none;background:linear-gradient(135deg,#22d3ee,#2dd4bf);color:#021018;font-weight:950;border:0;cursor:pointer}
.btn2{background:#102a45;color:#dff8ff;border:1px solid #245078}
pre{white-space:pre-wrap;background:#05101d;border:1px solid #183759;border-radius:16px;padding:14px;color:#e6fbff;overflow:auto;max-height:420px}
@media(max-width:950px){.grid,.grid2{grid-template-columns:1fr}.wrap{padding:16px}}
</style></head>
<body><div class="wrap">
 <div class="hero">
  <div class="badge">💾 V190 DATA COLLECTION ENGINE PRO</div>
  <h1>Motor de recolección histórica</h1>
  <p class="mut">Snapshots, historial de cuotas, resultados, ciclo de vida de picks y exportaciones. Esto convierte la app en un almacén de datos valioso para ML futuro.</p>
  <button class="btn" onclick="runCollection()">Recolectar ahora</button>
  <a class="btn btn2" href="/api/v190/data/export/snapshots.csv">Export snapshots CSV</a>
  <a class="btn btn2" href="/api/v190/data/export/picks.csv">Export picks CSV</a>
  <a class="btn btn2" href="/ml-data-foundation-pro">ML Data</a>
 </div>

 <div class="grid">
  <div class="card"><div class="mut">Valor dataset</div><div class="k {{ 'ok' if score >= 60 else 'gold' }}">{{ score }}%</div><div class="bar"><div class="fill" style="--w:{{ score }}%"></div></div></div>
  <div class="card"><div class="mut">Snapshots</div><div class="k">{{ data.warehouse.snapshots }}</div></div>
  <div class="card"><div class="mut">Odds history</div><div class="k gold">{{ data.warehouse.odds_history }}</div></div>
  <div class="card"><div class="mut">Pick lifecycle</div><div class="k ok">{{ data.warehouse.pick_lifecycle }}</div></div>
 </div>

 <div class="grid">
  <div class="card"><div class="mut">Resultados</div><div class="k">{{ data.warehouse.result_history }}</div></div>
  <div class="card"><div class="mut">Fixtures source</div><div class="k">{{ data.source_tables.fixtures_rows }}</div></div>
  <div class="card"><div class="mut">Picks source</div><div class="k">{{ data.source_tables.picks_rows }}</div></div>
  <div class="card"><div class="mut">Calidad media</div><div class="k">{{ data.warehouse.avg_quality }}</div></div>
 </div>

 <div class="grid2">
  <div class="card"><h2>Últimas ejecuciones</h2><pre>{{ data.runs | tojson(indent=2) }}</pre></div>
  <div class="card"><h2>Estado completo</h2><pre id="out">{{ data | tojson(indent=2) }}</pre></div>
 </div>
</div>
<script>
async function runCollection(){
 const r=await fetch('/api/v190/data-collection/run',{method:'POST'}).then(r=>r.json());
 document.getElementById('out').textContent=JSON.stringify(r,null,2);
}
</script>
</body></html>
    """, data=data, score=score)

@bp_data_collection_engine_v190.route("/api/v190/data-collection/status")
def api_status():
    return jsonify({"ok": True, "data_collection": _status()})

@bp_data_collection_engine_v190.route("/api/v190/data-collection/run", methods=["POST","GET"])
def api_run():
    job = request.args.get("job","manual")
    result = _run_collection(job)
    return jsonify({"ok": result["status"] == "ok", "result": result, "status": _status()})

@bp_data_collection_engine_v190.route("/api/v190/data/export/snapshots.csv")
def export_snapshots():
    _init()
    con = _connect()
    con.row_factory = sqlite3.Row
    rows = con.execute("SELECT snapshot_type,entity_id,source_table,quality_score,created_at FROM data_snapshots_v190 ORDER BY id DESC LIMIT 20000").fetchall()
    con.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["snapshot_type","entity_id","source_table","quality_score","created_at"])
    for r in rows:
        writer.writerow([r["snapshot_type"], r["entity_id"], r["source_table"], r["quality_score"], r["created_at"]])
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition":"attachment; filename=nemesis_data_snapshots_v190.csv"})

@bp_data_collection_engine_v190.route("/api/v190/data/export/picks.csv")
def export_picks():
    _init()
    con = _connect()
    con.row_factory = sqlite3.Row
    rows = con.execute("SELECT pick_id,match_id,market,selection,odds,stake,status,result_label,profit,source_table,created_at FROM pick_lifecycle_v190 ORDER BY id DESC LIMIT 20000").fetchall()
    con.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["pick_id","match_id","market","selection","odds","stake","status","result_label","profit","source_table","created_at"])
    for r in rows:
        writer.writerow([r["pick_id"], r["match_id"], r["market"], r["selection"], r["odds"], r["stake"], r["status"], r["result_label"], r["profit"], r["source_table"], r["created_at"]])
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition":"attachment; filename=nemesis_pick_lifecycle_v190.csv"})
