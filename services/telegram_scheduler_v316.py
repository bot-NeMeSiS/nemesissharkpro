
"""V316 · Telegram Auto Broadcast Scheduler.
Scheduler interno seguro para Render.
IMPORTANTE: funciona mientras el proceso web esté vivo. Para producción fuerte, se puede complementar con Render Cron.
"""

from __future__ import annotations

import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict

try:
    from services.telegram_delivery_v315 import (
        telegram_config_status,
        broadcast_to_known_chats,
        build_daily_client_message,
        send_admin_test,
    )
except Exception:  # fallback si import path varía
    telegram_config_status = None
    broadcast_to_known_chats = None
    build_daily_client_message = None
    send_admin_test = None


_STATE: Dict[str, Any] = {
    "started": False,
    "enabled": False,
    "last_run_at": None,
    "last_result": None,
    "last_error": None,
    "runs": 0,
    "thread_alive": False,
}

_LOCK = threading.Lock()


def scheduler_enabled() -> bool:
    return (os.getenv("TELEGRAM_AUTO_BROADCAST_ENABLED", "true").lower() in ["1", "true", "yes", "on"])


def interval_seconds() -> int:
    raw = os.getenv("TELEGRAM_AUTO_BROADCAST_INTERVAL_SECONDS") or os.getenv("TELEGRAM_BROADCAST_INTERVAL_SECONDS") or "3600"
    try:
        value = int(raw)
    except Exception:
        value = 3600
    return max(300, value)  # mínimo 5 minutos anti-spam


def max_chats() -> int:
    raw = os.getenv("TELEGRAM_AUTO_BROADCAST_MAX_CHATS", "50")
    try:
        return max(1, min(int(raw), 250))
    except Exception:
        return 50


def build_auto_message() -> str:
    if build_daily_client_message:
        base = build_daily_client_message()
    else:
        base = "🦈 <b>NeMeSiS SHARK PRO</b>\n\nTelegram automático activo."
    return (
        base
        + "\n\n"
        + "⏱️ Aviso automático del sistema.\n"
        + "Abre la app para revisar partidos de hoy, Live, 1X2 y SHARK AI."
    )


def run_once(reason: str = "manual") -> Dict[str, Any]:
    with _LOCK:
        _STATE["last_error"] = None

    if not scheduler_enabled() and reason != "manual":
        result = {"ok": False, "skipped": True, "reason": "scheduler disabled"}
    else:
        try:
            msg = build_auto_message()
            if broadcast_to_known_chats:
                result = broadcast_to_known_chats(msg, max_count=max_chats())
            else:
                result = {"ok": False, "error": "broadcast service unavailable"}
        except Exception as exc:
            result = {"ok": False, "error": str(exc)}

    with _LOCK:
        _STATE["last_run_at"] = datetime.now(timezone.utc).isoformat()
        _STATE["last_result"] = result
        _STATE["runs"] = int(_STATE.get("runs") or 0) + 1
        if not result.get("ok"):
            _STATE["last_error"] = result.get("error") or result.get("reason") or "unknown"
    return result


def _loop() -> None:
    while True:
        with _LOCK:
            _STATE["thread_alive"] = True
            _STATE["enabled"] = scheduler_enabled()
        try:
            if scheduler_enabled():
                run_once(reason="auto")
        except Exception as exc:
            with _LOCK:
                _STATE["last_error"] = str(exc)
        time.sleep(interval_seconds())


def start_scheduler_once() -> Dict[str, Any]:
    with _LOCK:
        if _STATE.get("started"):
            _STATE["thread_alive"] = True
            return status()
        _STATE["started"] = True
        _STATE["enabled"] = scheduler_enabled()

    t = threading.Thread(target=_loop, name="telegram-auto-broadcast-v316", daemon=True)
    t.start()
    with _LOCK:
        _STATE["thread_alive"] = True
    return status()


def status() -> Dict[str, Any]:
    cfg = telegram_config_status() if telegram_config_status else {}
    with _LOCK:
        state = dict(_STATE)
    return {
        "ok": True,
        "version": "V316",
        "scheduler": state,
        "enabled_env": scheduler_enabled(),
        "interval_seconds": interval_seconds(),
        "max_chats": max_chats(),
        "telegram_config": cfg,
        "note": "El envío automático funciona mientras el proceso Render esté vivo. Para máxima fiabilidad se recomienda añadir Render Cron apuntando a /api/telegram/auto-run-v316.",
    }
