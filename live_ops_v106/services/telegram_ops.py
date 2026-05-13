
import os
import requests
from datetime import datetime

def telegram_config_status():
    return {
        "bot_token": bool(os.environ.get("TELEGRAM_BOT_TOKEN")),
        "chat_id": bool(os.environ.get("TELEGRAM_CHAT_ID")),
        "ready": bool(os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID")),
    }

def send_telegram_message(text):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        return {
            "ok": False,
            "sent": False,
            "reason": "Telegram no configurado. Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID.",
            "configured": telegram_config_status(),
        }

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        r = requests.post(url, json=payload, timeout=8)
        return {
            "ok": r.ok,
            "sent": r.ok,
            "status_code": r.status_code,
            "response_preview": r.text[:300],
            "configured": telegram_config_status(),
        }
    except Exception as exc:
        return {
            "ok": False,
            "sent": False,
            "reason": str(exc),
            "configured": telegram_config_status(),
        }

def send_test_alert():
    now = datetime.utcnow().isoformat() + "Z"
    text = (
        "🦈 <b>NeMeSiS SHARK PRO</b>\\n"
        "✅ Test Telegram V106 correcto\\n"
        f"🕒 {now}\\n"
        "Panel Live Ops preparado."
    )
    return send_telegram_message(text)
