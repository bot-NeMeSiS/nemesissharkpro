
import os
import sqlite3
import hashlib
import requests
from pathlib import Path
from datetime import datetime, timedelta

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
    CREATE TABLE IF NOT EXISTS telegram_alert_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_hash TEXT,
        alert_type TEXT,
        plan TEXT,
        title TEXT,
        message TEXT,
        status TEXT,
        response_preview TEXT,
        created_at TEXT
    )
    """)
    con.commit()
    con.close()

def config_status():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    return {
        "bot_token_configured": bool(token),
        "chat_id_configured": bool(chat_id),
        "ready": bool(token and chat_id),
        "db_path": _db_path(),
    }

def _hash_message(alert_type, title, message):
    raw = f"{alert_type}|{title}|{message}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def is_spam_duplicate(alert_hash, minutes=8):
    ensure_schema()
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT created_at FROM telegram_alert_logs WHERE alert_hash=? ORDER BY id DESC LIMIT 1", (alert_hash,))
    row = cur.fetchone()
    con.close()
    if not row:
        return False
    try:
        created = datetime.fromisoformat(str(row["created_at"]).replace("Z", ""))
        return datetime.utcnow() - created < timedelta(minutes=minutes)
    except Exception:
        return False

def log_alert(alert_hash, alert_type, plan, title, message, status, response_preview=""):
    ensure_schema()
    con = _connect()
    cur = con.cursor()
    cur.execute("""
    INSERT INTO telegram_alert_logs
    (alert_hash, alert_type, plan, title, message, status, response_preview, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        alert_hash, alert_type, plan, title, message, status, response_preview[:500], datetime.utcnow().isoformat() + "Z"
    ))
    con.commit()
    con.close()

def format_premium_alert(title, body, plan="PRO", alert_type="PICK"):
    plan = str(plan or "PRO").upper()
    emoji = "🦈"
    if plan == "ELITE":
        badge = "🏆 ELITE"
    elif plan == "PRO":
        badge = "💎 PRO"
    else:
        badge = "🔹 FREE"

    return (
        f"{emoji} <b>NeMeSiS SHARK PRO</b>\\n"
        f"{badge} · {alert_type}\\n\\n"
        f"<b>{title}</b>\\n"
        f"{body}\\n\\n"
        f"⚠️ Gestión responsable. No es consejo financiero."
    )

def send_telegram_alert(title, body, plan="PRO", alert_type="PICK", force=False):
    ensure_schema()
    cfg = config_status()
    message = format_premium_alert(title, body, plan, alert_type)
    alert_hash = _hash_message(alert_type, title, message)

    if is_spam_duplicate(alert_hash) and not force:
        log_alert(alert_hash, alert_type, plan, title, message, "SKIPPED_DUPLICATE", "Anti-spam activo")
        return {
            "ok": True,
            "sent": False,
            "skipped": True,
            "reason": "Anti-spam: alerta duplicada reciente.",
            "configured": cfg,
        }

    if not cfg["ready"]:
        log_alert(alert_hash, alert_type, plan, title, message, "NOT_CONFIGURED", "Faltan variables Telegram")
        return {
            "ok": False,
            "sent": False,
            "reason": "Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID en Render.",
            "configured": cfg,
        }

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        r = requests.post(url, json=payload, timeout=10)
        status = "SENT" if r.ok else "ERROR"
        log_alert(alert_hash, alert_type, plan, title, message, status, r.text)
        return {
            "ok": r.ok,
            "sent": r.ok,
            "status_code": r.status_code,
            "response_preview": r.text[:500],
            "configured": cfg,
        }
    except Exception as exc:
        log_alert(alert_hash, alert_type, plan, title, message, "EXCEPTION", str(exc))
        return {
            "ok": False,
            "sent": False,
            "reason": str(exc),
            "configured": cfg,
        }

def send_test_alert():
    return send_telegram_alert(
        "Test Telegram V117",
        "✅ Telegram PRO REAL preparado desde el panel admin.\\n📡 Alertas premium listas para picks/live reales.",
        plan="PRO",
        alert_type="TEST",
        force=True
    )

def send_pick_alert(data):
    title = data.get("title") or data.get("match") or "Pick SHARK"
    body = (
        f"🎯 Pick: {data.get('pick', 'Sin pick')}\\n"
        f"💰 Cuota: {data.get('odds', 'N/A')}\\n"
        f"📊 Stake: {data.get('stake', 'N/A')}\\n"
        f"⚠️ Riesgo: {data.get('risk', 'MEDIUM')}\\n"
        f"🧠 Lectura: {data.get('reading', 'Value detectado por el sistema.')}"
    )
    return send_telegram_alert(title, body, data.get("plan", "PRO"), "PICK", bool(data.get("force", False)))

def send_live_alert(data):
    title = data.get("title") or data.get("match") or "Señal live SHARK"
    body = (
        f"📡 Minuto: {data.get('minute', 'LIVE')}\\n"
        f"⚡ Señal: {data.get('signal', 'LIVE_SIGNAL')}\\n"
        f"📊 Momentum: {data.get('momentum', 'N/A')}\\n"
        f"🦈 SHARK Score: {data.get('shark_score', 'N/A')}\\n"
        f"🧠 Lectura: {data.get('reading', 'Señal live detectada con datos reales.')}"
    )
    return send_telegram_alert(title, body, data.get("plan", "PRO"), "LIVE", bool(data.get("force", False)))

def latest_logs(limit=40):
    ensure_schema()
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT * FROM telegram_alert_logs ORDER BY id DESC LIMIT ?", (int(limit),))
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows

def dashboard_payload():
    logs = latest_logs(50)
    sent = len([x for x in logs if x.get("status") == "SENT"])
    errors = len([x for x in logs if x.get("status") in ["ERROR", "EXCEPTION", "NOT_CONFIGURED"]])
    skipped = len([x for x in logs if x.get("status") == "SKIPPED_DUPLICATE"])
    return {
        "version": "V117_TELEGRAM_PRO_REAL",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "config": config_status(),
        "summary": {
            "logs": len(logs),
            "sent": sent,
            "errors": errors,
            "skipped": skipped,
        },
        "logs": logs,
        "policy": {
            "no_fake_alerts": True,
            "manual_admin_send": True,
            "anti_spam": True,
            "premium_format": True,
        }
    }
