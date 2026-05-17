
"""V315 · Telegram Delivery Recovery.
Envía mensajes reales vía Telegram Bot API si TELEGRAM_BOT_TOKEN y chat_id están configurados.
No inventa partidos ni picks: solo envía lo que se le pasa.
"""

from __future__ import annotations

import json
import os
import sqlite3
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


DB_PATH = os.getenv("DATABASE_PATH") or os.getenv("DB_PATH") or "/data/database.db"


def get_token() -> str:
    return (os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN") or "").strip()


def api_url(method: str) -> str:
    token = get_token()
    return f"https://api.telegram.org/bot{token}/{method}"


def telegram_config_status() -> Dict[str, Any]:
    token = get_token()
    admin_chat = (os.getenv("TELEGRAM_ADMIN_CHAT_ID") or os.getenv("ADMIN_TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID") or "").strip()
    webhook_secret = (os.getenv("TELEGRAM_WEBHOOK_SECRET") or "").strip()
    return {
        "token_present": bool(token),
        "token_preview": (token[:8] + "..." + token[-4:]) if len(token) > 14 else ("SET" if token else ""),
        "admin_chat_id_present": bool(admin_chat),
        "admin_chat_id": admin_chat,
        "webhook_secret_present": bool(webhook_secret),
        "db_path": DB_PATH,
    }


def telegram_request(method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    token = get_token()
    if not token:
        return {"ok": False, "error": "TELEGRAM_BOT_TOKEN no configurado en Render."}
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(api_url(method), data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def send_message(chat_id: str, text: str, parse_mode: str = "HTML") -> Dict[str, Any]:
    if not chat_id:
        return {"ok": False, "error": "chat_id vacío. El usuario debe abrir el bot con /start o estar vinculado."}
    if not text:
        return {"ok": False, "error": "mensaje vacío"}
    return telegram_request("sendMessage", {
        "chat_id": str(chat_id),
        "text": text[:3900],
        "parse_mode": parse_mode,
        "disable_web_page_preview": "true",
    })


def send_admin_test(text: Optional[str] = None) -> Dict[str, Any]:
    admin_chat = (os.getenv("TELEGRAM_ADMIN_CHAT_ID") or os.getenv("ADMIN_TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID") or "").strip()
    msg = text or "🦈 <b>NeMeSiS SHARK PRO</b>\n\nTest Telegram OK.\nEl bot puede enviar mensajes reales si este mensaje llega."
    return send_message(admin_chat, msg)


def try_db_connection() -> Dict[str, Any]:
    path = Path(DB_PATH)
    if not path.exists():
        return {"ok": False, "error": f"No existe DB en {DB_PATH}"}
    try:
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r["name"] for r in cur.fetchall()]
        con.close()
        return {"ok": True, "tables": tables}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def discover_telegram_chats(limit: int = 200) -> List[Dict[str, Any]]:
    """Intenta descubrir usuarios/chat_id en tablas comunes sin romper si no existen."""
    db = try_db_connection()
    if not db.get("ok"):
        return []
    candidates = []
    possible_tables = ["users", "user", "clientes", "clients", "telegram_users", "members"]
    possible_cols = ["telegram_chat_id", "telegram_id", "chat_id", "tg_chat_id", "telegram"]
    try:
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        for table in possible_tables:
            if table not in db.get("tables", []):
                continue
            cur.execute(f"PRAGMA table_info({table})")
            cols = [r["name"] for r in cur.fetchall()]
            chat_cols = [c for c in possible_cols if c in cols]
            if not chat_cols:
                continue
            name_cols = [c for c in ["name", "username", "email", "nombre"] if c in cols]
            tier_cols = [c for c in ["membership", "tier", "plan", "role"] if c in cols]
            select_cols = chat_cols + name_cols[:1] + tier_cols[:1]
            cur.execute(f"SELECT {', '.join(select_cols)} FROM {table} LIMIT ?", (limit,))
            for row in cur.fetchall():
                for cc in chat_cols:
                    chat_id = row[cc]
                    if chat_id:
                        candidates.append({
                            "table": table,
                            "chat_id": str(chat_id),
                            "name": str(row[name_cols[0]]) if name_cols else "",
                            "tier": str(row[tier_cols[0]]) if tier_cols else "",
                        })
        con.close()
    except Exception:
        return candidates
    # dedupe
    seen = set()
    out = []
    for item in candidates:
        if item["chat_id"] not in seen:
            seen.add(item["chat_id"])
            out.append(item)
    return out


def broadcast_to_known_chats(text: str, max_count: int = 50) -> Dict[str, Any]:
    chats = discover_telegram_chats(limit=max_count)
    results = []
    for item in chats[:max_count]:
        res = send_message(item["chat_id"], text)
        results.append({"chat_id": item["chat_id"], "ok": bool(res.get("ok")), "response": res})
    return {"ok": True, "count": len(results), "results": results}


def build_daily_client_message() -> str:
    return (
        "🦈 <b>NeMeSiS SHARK PRO</b>\n\n"
        "Centro Telegram activo.\n"
        "Revisa la app para partidos de hoy, Live, combis 1X2 y SHARK AI.\n\n"
        "Sistema REAL ONLY: si faltan datos reales, no se inventan señales."
    )
