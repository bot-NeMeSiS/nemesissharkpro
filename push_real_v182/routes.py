
from flask import Blueprint, jsonify, request, render_template_string
import os, sqlite3, json, time
from pathlib import Path

bp_push_real_v182 = Blueprint("push_real_v182", __name__)

def _db_path():
    return os.environ.get("DATABASE_PATH") or os.environ.get("DB_PATH") or "/data/database.db"

def _connect():
    path = _db_path()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(path)

def _init():
    con = _connect()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS push_subscriptions_v182 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            endpoint TEXT UNIQUE,
            p256dh TEXT,
            auth TEXT,
            user_agent TEXT,
            plan TEXT DEFAULT 'FREE',
            enabled INTEGER DEFAULT 1,
            created_at INTEGER,
            updated_at INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS push_queue_v182 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target TEXT,
            plan TEXT,
            title TEXT,
            body TEXT,
            url TEXT,
            payload TEXT,
            status TEXT DEFAULT 'pending',
            error TEXT,
            created_at INTEGER,
            sent_at INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS push_logs_v182 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT,
            event TEXT,
            detail TEXT,
            created_at INTEGER
        )
    """)
    con.commit()
    con.close()

def _log(level, event, detail=""):
    try:
        _init()
        con = _connect()
        con.execute("INSERT INTO push_logs_v182(level,event,detail,created_at) VALUES(?,?,?,?)",
                    (level, event, detail[:1000], int(time.time())))
        con.commit()
        con.close()
    except Exception:
        pass

def _vapid_status():
    public_key = os.environ.get("VAPID_PUBLIC_KEY", "")
    private_key = os.environ.get("VAPID_PRIVATE_KEY", "")
    subject = os.environ.get("VAPID_SUBJECT", "")
    return {
        "configured": bool(public_key and private_key and subject),
        "public_key_present": bool(public_key),
        "private_key_present": bool(private_key),
        "subject_present": bool(subject),
        "public_key": public_key,
        "subject": subject,
        "note": "Para envío push real necesitas VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY y VAPID_SUBJECT en Render."
    }

def _counts():
    _init()
    con = _connect()
    cur = con.cursor()
    def one(sql, params=()):
        try:
            return cur.execute(sql, params).fetchone()[0]
        except Exception:
            return 0
    data = {
        "subscriptions_total": one("SELECT COUNT(*) FROM push_subscriptions_v182"),
        "subscriptions_enabled": one("SELECT COUNT(*) FROM push_subscriptions_v182 WHERE enabled=1"),
        "queue_pending": one("SELECT COUNT(*) FROM push_queue_v182 WHERE status='pending'"),
        "queue_sent": one("SELECT COUNT(*) FROM push_queue_v182 WHERE status='sent'"),
        "queue_failed": one("SELECT COUNT(*) FROM push_queue_v182 WHERE status='failed'"),
    }
    rows = []
    try:
        for r in cur.execute("SELECT id, level, event, detail, created_at FROM push_logs_v182 ORDER BY id DESC LIMIT 10"):
            rows.append({"id": r[0], "level": r[1], "event": r[2], "detail": r[3], "created_at": r[4]})
    except Exception:
        pass
    data["recent_logs"] = rows
    con.close()
    return data

@bp_push_real_v182.route("/admin/push-real")
@bp_push_real_v182.route("/admin/push-vapid")
@bp_push_real_v182.route("/admin/push-notifications-full")
def admin_push_real():
    _init()
    st = _vapid_status()
    counts = _counts()
    return render_template_string("""
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Push Real V182 · NeMeSiS SHARK PRO</title>
<link rel="manifest" href="/manifest.json">
<style>
:root{--bg:#06111f;--panel:#0b1c31;--line:#183759;--txt:#eaf7ff;--mut:#8fb2c9;--cyan:#23e6ff;--gold:#ffd166;--red:#ff5b7a;--green:#35f0a1}
body{margin:0;background:radial-gradient(circle at top,#12345a,#06111f 50%,#02060b);font-family:Inter,system-ui,Arial;color:var(--txt)}
.wrap{max-width:1180px;margin:auto;padding:26px}
.hero{border:1px solid var(--line);background:linear-gradient(135deg,rgba(35,230,255,.14),rgba(255,209,102,.08));border-radius:28px;padding:26px;box-shadow:0 25px 90px rgba(0,0,0,.35)}
.badge{display:inline-flex;gap:8px;align-items:center;padding:8px 12px;border-radius:99px;background:rgba(35,230,255,.12);border:1px solid rgba(35,230,255,.35);color:#bff8ff;font-weight:800;font-size:12px}
.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:18px}
.card{border:1px solid var(--line);background:rgba(11,28,49,.86);border-radius:22px;padding:18px}
.k{font-size:34px;font-weight:900;margin-top:6px}
.mut{color:var(--mut)}
.ok{color:var(--green)}.bad{color:var(--red)}.gold{color:var(--gold)}
.btn{display:inline-block;border:0;border-radius:14px;padding:12px 16px;margin:6px 8px 6px 0;background:linear-gradient(135deg,#22d3ee,#2dd4bf);color:#021018;font-weight:900;text-decoration:none;cursor:pointer}
.btn2{background:#102a45;color:#dff8ff;border:1px solid #245078}
pre{white-space:pre-wrap;background:#05101d;border:1px solid #183759;border-radius:16px;padding:14px;color:#dff8ff}
@media(max-width:820px){.grid{grid-template-columns:1fr}.wrap{padding:16px}.k{font-size:28px}}
</style>
</head>
<body>
<div class="wrap">
 <div class="hero">
  <div class="badge">🦈 V182 PUSH REAL VAPID FOUNDATION</div>
  <h1>Centro Push Real · NeMeSiS SHARK PRO</h1>
  <p class="mut">Suscripciones PWA, cola de notificaciones, diagnóstico VAPID y pruebas reales. No inventa alertas: si no hay datos, deja estado pendiente/premium.</p>
  <button class="btn" onclick="subscribePush()">Activar notificaciones en este dispositivo</button>
  <button class="btn btn2" onclick="queueTest()">Crear prueba push</button>
  <button class="btn btn2" onclick="runDry()">Procesar cola modo seguro</button>
  <a class="btn btn2" href="/admin/intelligence">Admin Intelligence</a>
 </div>

 <div class="grid">
  <div class="card"><div class="mut">VAPID</div><div class="k {{ 'ok' if st.configured else 'bad' }}">{{ 'OK' if st.configured else 'FALTA' }}</div><p class="mut">Public/private key + subject.</p></div>
  <div class="card"><div class="mut">Suscripciones activas</div><div class="k">{{ counts.subscriptions_enabled }}</div><p class="mut">Dispositivos PWA registrados.</p></div>
  <div class="card"><div class="mut">Cola pendiente</div><div class="k gold">{{ counts.queue_pending }}</div><p class="mut">Alertas listas para enviar.</p></div>
 </div>

 <div class="grid">
  <div class="card"><h3>Configuración</h3><pre>{{ st | tojson(indent=2) }}</pre></div>
  <div class="card"><h3>Estado</h3><pre>{{ counts | tojson(indent=2) }}</pre></div>
  <div class="card"><h3>Resultado acción</h3><pre id="out">Sin acciones todavía.</pre></div>
 </div>
</div>
<script>
async function subscribePush(){
 const out=document.getElementById('out');
 try{
   if(!('serviceWorker' in navigator)){out.textContent='Service Worker no soportado.';return}
   if(!('PushManager' in window)){out.textContent='PushManager no soportado en este navegador.';return}
   const cfg=await fetch('/api/v182/push/public-key').then(r=>r.json());
   if(!cfg.public_key){out.textContent='Falta VAPID_PUBLIC_KEY en Render.';return}
   const reg=await navigator.serviceWorker.register('/service-worker.js');
   const perm=await Notification.requestPermission();
   if(perm!=='granted'){out.textContent='Permiso no concedido: '+perm;return}
   const key=urlBase64ToUint8Array(cfg.public_key);
   const sub=await reg.pushManager.subscribe({userVisibleOnly:true, applicationServerKey:key});
   const res=await fetch('/api/v182/push/subscribe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({subscription:sub, plan:'ELITE'})}).then(r=>r.json());
   out.textContent=JSON.stringify(res,null,2);
 }catch(e){out.textContent='Error: '+e}
}
function urlBase64ToUint8Array(base64String){
 const padding='='.repeat((4-base64String.length%4)%4);
 const base64=(base64String+padding).replace(/-/g,'+').replace(/_/g,'/');
 const raw=window.atob(base64);
 const output=new Uint8Array(raw.length);
 for(let i=0;i<raw.length;++i){output[i]=raw.charCodeAt(i)}
 return output;
}
async function queueTest(){
 const res=await fetch('/api/v182/push/queue-test',{method:'POST'}).then(r=>r.json());
 document.getElementById('out').textContent=JSON.stringify(res,null,2);
}
async function runDry(){
 const res=await fetch('/api/v182/push/process?dry=1',{method:'POST'}).then(r=>r.json());
 document.getElementById('out').textContent=JSON.stringify(res,null,2);
}
</script>
</body>
</html>
    """, st=st, counts=counts)

@bp_push_real_v182.route("/api/v182/push/status")
def api_push_status():
    return jsonify({"ok": True, "vapid": _vapid_status(), "counts": _counts()})

@bp_push_real_v182.route("/api/v182/push/public-key")
def api_public_key():
    return jsonify({"ok": True, "public_key": os.environ.get("VAPID_PUBLIC_KEY", "")})

@bp_push_real_v182.route("/api/v182/push/subscribe", methods=["POST"])
def api_subscribe():
    _init()
    data = request.get_json(silent=True) or {}
    sub = data.get("subscription") or data
    endpoint = sub.get("endpoint")
    keys = sub.get("keys") or {}
    if not endpoint:
        return jsonify({"ok": False, "error": "No endpoint recibido"}), 400
    plan = (data.get("plan") or "FREE").upper()
    con = _connect()
    con.execute("""
        INSERT INTO push_subscriptions_v182(user_id,endpoint,p256dh,auth,user_agent,plan,enabled,created_at,updated_at)
        VALUES(?,?,?,?,?,?,1,?,?)
        ON CONFLICT(endpoint) DO UPDATE SET p256dh=excluded.p256dh, auth=excluded.auth, user_agent=excluded.user_agent, plan=excluded.plan, enabled=1, updated_at=excluded.updated_at
    """, (str(data.get("user_id") or ""), endpoint, keys.get("p256dh",""), keys.get("auth",""), request.headers.get("User-Agent",""), plan, int(time.time()), int(time.time())))
    con.commit()
    con.close()
    _log("info", "push_subscribed", endpoint[:120])
    return jsonify({"ok": True, "message": "Dispositivo suscrito a push", "plan": plan})

@bp_push_real_v182.route("/api/v182/push/queue-test", methods=["POST"])
def api_queue_test():
    _init()
    payload = {
        "title": "🦈 NeMeSiS SHARK PRO",
        "body": "Prueba push real preparada. Si VAPID está configurado, podrá enviarse a dispositivos suscritos.",
        "url": "/cliente/pro",
        "type": "test"
    }
    con = _connect()
    con.execute("INSERT INTO push_queue_v182(target,plan,title,body,url,payload,status,created_at) VALUES(?,?,?,?,?,?,?,?)",
                ("all", "ELITE", payload["title"], payload["body"], payload["url"], json.dumps(payload, ensure_ascii=False), "pending", int(time.time())))
    con.commit()
    con.close()
    _log("info", "push_test_queued", payload["body"])
    return jsonify({"ok": True, "queued": payload})

@bp_push_real_v182.route("/api/v182/push/process", methods=["POST"])
def api_process():
    _init()
    dry = request.args.get("dry", "1") != "0"
    st = _vapid_status()
    con = _connect()
    cur = con.cursor()
    rows = cur.execute("SELECT id,title,body,url,payload FROM push_queue_v182 WHERE status='pending' ORDER BY id ASC LIMIT 25").fetchall()
    processed = []
    # Foundation: mark dry-run, do not attempt external send without pywebpush configured.
    for r in rows:
        qid = r[0]
        if dry or not st["configured"]:
            cur.execute("UPDATE push_queue_v182 SET status=?, error=?, sent_at=? WHERE id=?",
                        ("failed" if not st["configured"] else "sent", "VAPID no configurado" if not st["configured"] else "dry-run ok", int(time.time()), qid))
            processed.append({"id": qid, "status": "dry-run" if st["configured"] else "missing-vapid"})
        else:
            # Real send hook prepared. Install pywebpush and enable sending in production if required.
            cur.execute("UPDATE push_queue_v182 SET status=?, error=?, sent_at=? WHERE id=?",
                        ("failed", "Motor real pendiente de pywebpush/worker externo", int(time.time()), qid))
            processed.append({"id": qid, "status": "send-hook-prepared"})
    con.commit()
    con.close()
    _log("info", "push_queue_processed", json.dumps(processed, ensure_ascii=False))
    return jsonify({"ok": True, "dry": dry, "vapid_configured": st["configured"], "processed": processed})
