
from flask import Blueprint, jsonify, request, render_template_string, Response
import os, sqlite3, json, time, hashlib, csv, io, math
from pathlib import Path

bp_ml_data_foundation_v189 = Blueprint("ml_data_foundation_v189", __name__)

def _db_path():
    return os.environ.get("DATABASE_PATH") or os.environ.get("DB_PATH") or "/data/database.db"

def _connect():
    Path(_db_path()).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(_db_path())

def _init():
    con = _connect()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ml_feature_store_v189 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT,
            entity_id TEXT,
            source_table TEXT,
            feature_key TEXT,
            feature_json TEXT,
            label TEXT,
            outcome_value REAL,
            quality_score INTEGER DEFAULT 0,
            created_at INTEGER,
            updated_at INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ml_training_dataset_v189 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_name TEXT,
            row_hash TEXT UNIQUE,
            entity_id TEXT,
            features_json TEXT,
            label TEXT,
            target REAL,
            split TEXT DEFAULT 'train',
            quality_score INTEGER DEFAULT 0,
            created_at INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ml_model_registry_v189 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT,
            model_type TEXT,
            version TEXT,
            metrics_json TEXT,
            status TEXT DEFAULT 'candidate',
            notes TEXT,
            created_at INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ml_data_quality_v189 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scope TEXT,
            metric TEXT,
            value REAL,
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

def _rows(table, limit=500):
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

def _hash(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str, ensure_ascii=False).encode("utf-8")).hexdigest()

def _fixture_rows():
    out = []
    for t in ["fixtures_cache", "fixtures", "real_fixtures", "matches_cache", "matches"]:
        for r in _rows(t, 1000):
            r["_source_table"] = t
            out.append(r)
    return out

def _pick_rows():
    out = []
    for t in ["picks", "real_picks", "admin_picks", "closed_picks"]:
        for r in _rows(t, 1000):
            r["_source_table"] = t
            out.append(r)
    return out

def _extract_pick_features(row):
    source = row.get("_source_table","")
    entity_id = str(_pick(row, ["id","pick_id","match_id","fixture_id","event_id"]) or _hash(row)[:12])
    league = str(_pick(row, ["league","liga","competition"]) or "")
    market = str(_pick(row, ["market","mercado","pick_type","selection"]) or "")
    sport = str(_pick(row, ["sport","sport_key","sport_title"]) or "")
    odds = _num(_pick(row, ["odds","odd","cuota","price"]), 0)
    stake = _num(_pick(row, ["stake","amount","importe"]), 0)
    confidence = _num(_pick(row, ["confidence","confianza","score","shark_score"]), 0)
    risk_raw = str(_pick(row, ["risk","riesgo","risk_level"]) or "").lower()
    risk = 0.5
    if "alto" in risk_raw or "high" in risk_raw:
        risk = 0.8
    elif "bajo" in risk_raw or "low" in risk_raw:
        risk = 0.25
    elif "medio" in risk_raw or "medium" in risk_raw:
        risk = 0.5
    result = str(_pick(row, ["result","status","outcome","estado"]) or "").lower()
    label = ""
    target = None
    if "win" in result or "gan" in result:
        label = "WIN"; target = 1.0
    elif "loss" in result or "lost" in result or "perd" in result:
        label = "LOSS"; target = 0.0
    elif "void" in result or "push" in result or "nulo" in result:
        label = "VOID"; target = 0.5
    features = {
        "source_table": source,
        "entity_id": entity_id,
        "league": league,
        "market": market,
        "sport": sport,
        "odds": odds,
        "stake": stake,
        "confidence": confidence,
        "risk": risk,
        "has_odds": 1 if odds > 0 else 0,
        "has_stake": 1 if stake > 0 else 0,
        "has_confidence": 1 if confidence > 0 else 0,
        "league_hash": int(hashlib.md5(league.encode()).hexdigest()[:4],16) % 1000 if league else 0,
        "market_hash": int(hashlib.md5(market.encode()).hexdigest()[:4],16) % 1000 if market else 0,
    }
    quality = 10
    quality += 20 if odds > 0 else 0
    quality += 15 if stake > 0 else 0
    quality += 15 if league else 0
    quality += 15 if market else 0
    quality += 25 if label in ("WIN","LOSS","VOID") else 0
    return entity_id, features, label, target, min(100, quality)

def _extract_fixture_features(row):
    source = row.get("_source_table","")
    entity_id = str(_pick(row, ["id","fixture_id","match_id","event_id"]) or _hash(row)[:12])
    league = str(_pick(row, ["league","competition","competition_name","sport_title","liga"]) or "")
    home = str(_pick(row, ["home_team","home","team_home","home_name","local"]) or "")
    away = str(_pick(row, ["away_team","away","team_away","away_name","visitor","visitante"]) or "")
    status = str(_pick(row, ["status","state","fixture_status","match_status"]) or "").lower()
    score_home = _num(_pick(row, ["home_score","score_home","goals_home","home_goals"]), -1)
    score_away = _num(_pick(row, ["away_score","score_away","goals_away","away_goals"]), -1)
    txt = json.dumps(row, ensure_ascii=False, default=str).lower()
    has_odds = 1 if any(x in txt for x in ["odd","odds","price","cuota","bookmaker"]) else 0
    is_live = 1 if any(x in txt for x in ["live","in_play","inplay","1h","2h","minute","elapsed"]) else 0
    is_finished = 1 if any(x in status for x in ["finish","ended","final","ft","closed"]) else 0
    label = ""
    target = None
    if is_finished and score_home >= 0 and score_away >= 0:
        if score_home > score_away:
            label = "HOME_WIN"; target = 1.0
        elif score_home < score_away:
            label = "AWAY_WIN"; target = 2.0
        else:
            label = "DRAW"; target = 0.0
    features = {
        "source_table": source,
        "entity_id": entity_id,
        "league": league,
        "home": home,
        "away": away,
        "status": status,
        "is_live": is_live,
        "is_finished": is_finished,
        "has_odds": has_odds,
        "has_score": 1 if score_home >= 0 and score_away >= 0 else 0,
        "score_home": max(score_home, 0),
        "score_away": max(score_away, 0),
        "league_hash": int(hashlib.md5(league.encode()).hexdigest()[:4],16) % 1000 if league else 0,
        "home_hash": int(hashlib.md5(home.encode()).hexdigest()[:4],16) % 1000 if home else 0,
        "away_hash": int(hashlib.md5(away.encode()).hexdigest()[:4],16) % 1000 if away else 0,
    }
    quality = 10
    quality += 15 if league else 0
    quality += 15 if home and away else 0
    quality += 15 if has_odds else 0
    quality += 20 if features["has_score"] else 0
    quality += 25 if label else 0
    return entity_id, features, label, target, min(100, quality)

def _build_feature_store():
    _init()
    now = int(time.time())
    created = 0
    con = _connect()
    for r in _pick_rows():
        entity_id, features, label, target, quality = _extract_pick_features(r)
        key = _hash({"type":"pick","entity_id":entity_id,"features":features})
        con.execute("""
            INSERT INTO ml_feature_store_v189(entity_type,entity_id,source_table,feature_key,feature_json,label,outcome_value,quality_score,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?)
        """, ("pick", entity_id, r.get("_source_table",""), key, json.dumps(features, ensure_ascii=False), label, target, quality, now, now))
        created += 1
    for r in _fixture_rows():
        entity_id, features, label, target, quality = _extract_fixture_features(r)
        key = _hash({"type":"fixture","entity_id":entity_id,"features":features})
        con.execute("""
            INSERT INTO ml_feature_store_v189(entity_type,entity_id,source_table,feature_key,feature_json,label,outcome_value,quality_score,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?)
        """, ("fixture", entity_id, r.get("_source_table",""), key, json.dumps(features, ensure_ascii=False), label, target, quality, now, now))
        created += 1
    con.commit()
    con.close()
    _quality_snapshot()
    return created

def _build_training_dataset(name="baseline_v189"):
    _init()
    con = _connect()
    con.row_factory = sqlite3.Row
    rows = con.execute("""
        SELECT entity_type,entity_id,feature_json,label,outcome_value,quality_score
        FROM ml_feature_store_v189
        WHERE label IS NOT NULL AND label != '' AND quality_score >= 50
        ORDER BY id DESC
        LIMIT 5000
    """).fetchall()
    added = 0
    for idx, r in enumerate(rows):
        features = json.loads(r["feature_json"])
        row_payload = {
            "entity_type": r["entity_type"],
            "entity_id": r["entity_id"],
            "features": features,
            "label": r["label"],
            "target": r["outcome_value"]
        }
        row_hash = _hash(row_payload)
        split = "test" if idx % 5 == 0 else "train"
        try:
            con.execute("""
                INSERT OR IGNORE INTO ml_training_dataset_v189(dataset_name,row_hash,entity_id,features_json,label,target,split,quality_score,created_at)
                VALUES(?,?,?,?,?,?,?,?,?)
            """, (name, row_hash, r["entity_id"], json.dumps(features, ensure_ascii=False), r["label"], r["outcome_value"], split, r["quality_score"], int(time.time())))
            added += con.total_changes
        except Exception:
            pass
    con.commit()
    con.close()
    return len(rows)

def _quality_snapshot():
    con = _connect()
    cur = con.cursor()
    def one(sql):
        try:
            return cur.execute(sql).fetchone()[0]
        except Exception:
            return 0
    metrics = {
        "feature_rows": one("SELECT COUNT(*) FROM ml_feature_store_v189"),
        "labeled_rows": one("SELECT COUNT(*) FROM ml_feature_store_v189 WHERE label IS NOT NULL AND label != ''"),
        "high_quality_rows": one("SELECT COUNT(*) FROM ml_feature_store_v189 WHERE quality_score >= 70"),
        "avg_quality": one("SELECT COALESCE(AVG(quality_score),0) FROM ml_feature_store_v189"),
        "training_rows": one("SELECT COUNT(*) FROM ml_training_dataset_v189"),
    }
    now = int(time.time())
    for k, v in metrics.items():
        con.execute("INSERT INTO ml_data_quality_v189(scope,metric,value,detail,created_at) VALUES(?,?,?,?,?)",
                    ("global", k, float(v or 0), "", now))
    con.commit()
    con.close()
    return metrics

def _baseline_metrics():
    _init()
    con = _connect()
    con.row_factory = sqlite3.Row
    rows = con.execute("SELECT label,target,split FROM ml_training_dataset_v189").fetchall()
    con.close()
    total = len(rows)
    if not total:
        return {
            "trained": False,
            "message": "No hay dataset etiquetado suficiente.",
            "accuracy_baseline": 0,
            "samples": 0
        }
    labels = {}
    for r in rows:
        labels[r["label"]] = labels.get(r["label"], 0) + 1
    majority = max(labels, key=labels.get)
    acc = round((labels[majority] / total) * 100, 2)
    metrics = {
        "trained": True,
        "model_type": "majority_baseline_no_prediction_claim",
        "majority_label": majority,
        "accuracy_baseline": acc,
        "samples": total,
        "labels": labels,
        "note": "Baseline estadístico: NO es modelo predictivo comercial todavía; sirve para medir dataset y punto de partida."
    }
    con = _connect()
    con.execute("INSERT INTO ml_model_registry_v189(model_name,model_type,version,metrics_json,status,notes,created_at) VALUES(?,?,?,?,?,?,?)",
                ("NemesisBaseline", "majority_baseline", "v189", json.dumps(metrics, ensure_ascii=False), "baseline", metrics["note"], int(time.time())))
    con.commit()
    con.close()
    return metrics

def _status():
    _init()
    tables = _tables()
    data = {
        "source": {
            "fixtures_rows": len(_fixture_rows()),
            "picks_rows": len(_pick_rows()),
            "available_tables": sorted(list(tables))[:120]
        },
        "feature_store": {
            "rows": _count("ml_feature_store_v189"),
            "picks": _count("ml_feature_store_v189", "entity_type='pick'"),
            "fixtures": _count("ml_feature_store_v189", "entity_type='fixture'"),
            "labeled": _count("ml_feature_store_v189", "label IS NOT NULL AND label != ''"),
            "high_quality": _count("ml_feature_store_v189", "quality_score >= 70")
        },
        "training_dataset": {
            "rows": _count("ml_training_dataset_v189"),
            "train": _count("ml_training_dataset_v189", "split='train'"),
            "test": _count("ml_training_dataset_v189", "split='test'")
        },
        "model_registry": {
            "models": _count("ml_model_registry_v189")
        }
    }
    labeled = data["feature_store"]["labeled"]
    highq = data["feature_store"]["high_quality"]
    score = 0
    if data["source"]["fixtures_rows"] > 0: score += 15
    if data["source"]["picks_rows"] > 0: score += 15
    if labeled >= 50: score += 20
    if labeled >= 200: score += 20
    if highq >= 50: score += 15
    if data["training_dataset"]["rows"] >= 50: score += 15
    data["readiness"] = {
        "score": min(100, score),
        "level": "alto" if score >= 75 else ("medio" if score >= 45 else "bajo"),
        "can_train_real_model": score >= 75,
        "missing": []
    }
    if labeled < 200:
        data["readiness"]["missing"].append("Más picks/partidos cerrados con resultado real.")
    if highq < 50:
        data["readiness"]["missing"].append("Más filas de calidad con cuota, mercado, liga y resultado.")
    if data["source"]["fixtures_rows"] < 100:
        data["readiness"]["missing"].append("Más histórico de fixtures.")
    data["policy"] = "Guarda y normaliza datos reales; no promete predicciones rentables sin histórico suficiente."
    return data

@bp_ml_data_foundation_v189.route("/ml-data-foundation-pro")
@bp_ml_data_foundation_v189.route("/admin/ml-data")
@bp_ml_data_foundation_v189.route("/admin/machine-learning")
def page():
    data = _status()
    return render_template_string("""
<!doctype html>
<html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ML Data Foundation V189 · NeMeSiS SHARK PRO</title>
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
li{margin:7px 0}@media(max-width:950px){.grid,.grid2{grid-template-columns:1fr}.wrap{padding:16px}}
</style></head>
<body><div class="wrap">
 <div class="hero">
  <div class="badge">🧠 V189 MACHINE LEARNING DATA FOUNDATION PRO</div>
  <h1>Motor de datos para ML real</h1>
  <p class="mut">Feature store, dataset de entrenamiento, calidad de datos, baseline y export CSV. Esto guarda valor real para futuro sin inventar predicciones.</p>
  <button class="btn" onclick="buildFeatures()">Construir feature store</button>
  <button class="btn btn2" onclick="buildDataset()">Crear dataset</button>
  <button class="btn btn2" onclick="baseline()">Baseline</button>
  <a class="btn btn2" href="/api/v189/ml/export.csv">Export CSV</a>
  <a class="btn btn2" href="/advanced-stats-pro">Advanced Stats</a>
 </div>

 <div class="grid">
  <div class="card"><div class="mut">Readiness ML</div><div class="k {{ 'ok' if data.readiness.score >= 75 else 'gold' }}">{{ data.readiness.score }}%</div><div class="bar"><div class="fill" style="--w:{{ data.readiness.score }}%"></div></div></div>
  <div class="card"><div class="mut">Feature rows</div><div class="k">{{ data.feature_store.rows }}</div></div>
  <div class="card"><div class="mut">Labeled</div><div class="k gold">{{ data.feature_store.labeled }}</div></div>
  <div class="card"><div class="mut">Training rows</div><div class="k ok">{{ data.training_dataset.rows }}</div></div>
 </div>

 <div class="grid2">
  <div class="card">
   <h2>Qué falta para ML real</h2>
   {% if data.readiness.missing %}
    <ul>{% for m in data.readiness.missing %}<li>{{ m }}</li>{% endfor %}</ul>
   {% else %}
    <p class="ok">Dataset preparado para baseline serio.</p>
   {% endif %}
   <p class="mut">Nivel: {{ data.readiness.level }}</p>
  </div>
  <div class="card"><h2>Resultado</h2><pre id="out">{{ data | tojson(indent=2) }}</pre></div>
 </div>
</div>
<script>
async function buildFeatures(){ const r=await fetch('/api/v189/ml/build-feature-store',{method:'POST'}).then(r=>r.json()); out.textContent=JSON.stringify(r,null,2); }
async function buildDataset(){ const r=await fetch('/api/v189/ml/build-dataset',{method:'POST'}).then(r=>r.json()); out.textContent=JSON.stringify(r,null,2); }
async function baseline(){ const r=await fetch('/api/v189/ml/baseline',{method:'POST'}).then(r=>r.json()); out.textContent=JSON.stringify(r,null,2); }
</script>
</body></html>
    """, data=data)

@bp_ml_data_foundation_v189.route("/api/v189/ml/status")
def api_status():
    return jsonify({"ok": True, "ml": _status()})

@bp_ml_data_foundation_v189.route("/api/v189/ml/build-feature-store", methods=["POST", "GET"])
def api_build_feature_store():
    created = _build_feature_store()
    return jsonify({"ok": True, "created_feature_rows": created, "status": _status()})

@bp_ml_data_foundation_v189.route("/api/v189/ml/build-dataset", methods=["POST", "GET"])
def api_build_dataset():
    rows = _build_training_dataset()
    return jsonify({"ok": True, "candidate_rows": rows, "status": _status()})

@bp_ml_data_foundation_v189.route("/api/v189/ml/baseline", methods=["POST", "GET"])
def api_baseline():
    metrics = _baseline_metrics()
    return jsonify({"ok": True, "baseline": metrics, "status": _status()})

@bp_ml_data_foundation_v189.route("/api/v189/ml/export.csv")
def api_export_csv():
    _init()
    con = _connect()
    con.row_factory = sqlite3.Row
    rows = con.execute("SELECT dataset_name,entity_id,features_json,label,target,split,quality_score,created_at FROM ml_training_dataset_v189 ORDER BY id DESC LIMIT 10000").fetchall()
    con.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["dataset_name","entity_id","features_json","label","target","split","quality_score","created_at"])
    for r in rows:
        writer.writerow([r["dataset_name"], r["entity_id"], r["features_json"], r["label"], r["target"], r["split"], r["quality_score"], r["created_at"]])
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition":"attachment; filename=nemesis_ml_dataset_v189.csv"})
