
"""V318 · Telegram webhook setup/diagnostics."""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import Any, Dict


def get_token() -> str:
    return (os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN") or "").strip()


def telegram_api(method: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    token = get_token()
    if not token:
        return {"ok": False, "error": "TELEGRAM_BOT_TOKEN no configurado"}
    url = f"https://api.telegram.org/bot{token}/{method}"
    try:
        if payload is None:
            with urllib.request.urlopen(url, timeout=12) as resp:
                return json.loads(resp.read().decode("utf-8", errors="replace"))
        data = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=12) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def normalize_base_url(base_url: str) -> str:
    base_url = (base_url or "").strip()
    if not base_url:
        return ""
    base_url = base_url.replace("http://", "https://")
    return base_url.rstrip("/")


def build_webhook_url(request_base_url: str = "") -> str:
    env_url = (
        os.getenv("PUBLIC_BASE_URL")
        or os.getenv("APP_BASE_URL")
        or os.getenv("RENDER_EXTERNAL_URL")
        or os.getenv("WEBHOOK_BASE_URL")
        or ""
    )
    base = normalize_base_url(env_url or request_base_url)
    return f"{base}/telegram/webhook" if base else ""


def get_webhook_info() -> Dict[str, Any]:
    return telegram_api("getWebhookInfo")


def delete_webhook() -> Dict[str, Any]:
    return telegram_api("deleteWebhook", {"drop_pending_updates": "false"})


def set_webhook(webhook_url: str) -> Dict[str, Any]:
    if not webhook_url:
        return {"ok": False, "error": "No se pudo construir webhook_url"}
    return telegram_api("setWebhook", {
        "url": webhook_url,
        "allowed_updates": json.dumps(["message", "edited_message", "channel_post"]),
        "drop_pending_updates": "false",
    })


def webhook_setup_status(request_base_url: str = "") -> Dict[str, Any]:
    webhook_url = build_webhook_url(request_base_url)
    info = get_webhook_info()
    return {
        "ok": True,
        "token_present": bool(get_token()),
        "target_webhook_url": webhook_url,
        "current_webhook_info": info,
        "env_base_url_present": bool(os.getenv("PUBLIC_BASE_URL") or os.getenv("APP_BASE_URL") or os.getenv("RENDER_EXTERNAL_URL") or os.getenv("WEBHOOK_BASE_URL")),
    }


def configure_webhook(request_base_url: str = "") -> Dict[str, Any]:
    webhook_url = build_webhook_url(request_base_url)
    before = get_webhook_info()
    deleted = delete_webhook()
    configured = set_webhook(webhook_url)
    after = get_webhook_info()
    return {
        "ok": bool(configured.get("ok")),
        "target_webhook_url": webhook_url,
        "before": before,
        "delete_result": deleted,
        "set_result": configured,
        "after": after,
    }
