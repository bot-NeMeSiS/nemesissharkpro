
"""V317 · Telegram chat linking + webhook persistence.
Guarda chat_id reales cuando llega /start o cualquier mensaje al webhook.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = os.getenv("DATABASE_PATH") or os.getenv("DB_PATH") or "/data/database.db"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def ensure_telegram_tables() -> None:
    con = connect()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS telegram_chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT UNIQUE NOT NULL,
            chat_type TEXT,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            title TEXT,
            membership TEXT DEFAULT 'FREE',
            is_active INTEGER DEFAULT 1,
            source TEXT DEFAULT 'webhook',
            last_text TEXT,
            last_update_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS telegram_delivery_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT,
            message TEXT,
            ok INTEGER,
            error TEXT,
            sent_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    con.commit()
    con.close()


def extract_chat(update: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    msg = update.get("message") or update.get("channel_post") or update.get("edited_message") or {}
    chat = msg.get("chat") or {}
    if not chat.get("id"):
        return None
    from_user = msg.get("from") or {}
    text = msg.get("text") or msg.get("caption") or ""
    return {
        "chat_id": str(chat.get("id")),
        "chat_type": str(chat.get("type") or ""),
        "username": str(from_user.get("username") or chat.get("username") or ""),
        "first_name": str(from_user.get("first_name") or ""),
        "last_name": str(from_user.get("last_name") or ""),
        "title": str(chat.get("title") or ""),
        "last_text": str(text or ""),
    }


def save_chat_from_update(update: Dict[str, Any]) -> Dict[str, Any]:
    ensure_telegram_tables()
    item = extract_chat(update)
    if not item:
        return {"ok": False, "error": "No chat_id found in Telegram update"}

    con = connect()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO telegram_chats (
            chat_id, chat_type, username, first_name, last_name, title, last_text, last_update_at, source, is_active
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'webhook', 1)
        ON CONFLICT(chat_id) DO UPDATE SET
            chat_type=excluded.chat_type,
            username=excluded.username,
            first_name=excluded.first_name,
            last_name=excluded.last_name,
            title=excluded.title,
            last_text=excluded.last_text,
            last_update_at=excluded.last_update_at,
            is_active=1
    """, (
        item["chat_id"], item["chat_type"], item["username"], item["first_name"],
        item["last_name"], item["title"], item["last_text"], now_iso()
    ))
    con.commit()
    con.close()
    return {"ok": True, "chat": item}


def list_linked_chats(limit: int = 200) -> List[Dict[str, Any]]:
    ensure_telegram_tables()
    con = connect()
    cur = con.cursor()
    cur.execute("""
        SELECT chat_id, chat_type, username, first_name, last_name, title,
               membership, is_active, source, last_text, last_update_at, created_at
        FROM telegram_chats
        ORDER BY COALESCE(last_update_at, created_at) DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows


def count_linked_chats() -> int:
    ensure_telegram_tables()
    con = connect()
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM telegram_chats WHERE is_active=1")
    n = int(cur.fetchone()[0])
    con.close()
    return n


def build_start_reply() -> str:
    return (
        "🦈 <b>NeMeSiS SHARK PRO conectado</b>\n\n"
        "Tu Telegram ya queda vinculado para recibir avisos automáticos.\n\n"
        "Podrás recibir:\n"
        "• partidos de hoy\n"
        "• alertas live\n"
        "• combis 1X2\n"
        "• avisos SHARK\n\n"
        "REAL ONLY: si faltan datos reales, no inventamos señales."
    )


def should_reply_to_text(text: str) -> bool:
    t = (text or "").strip().lower()
    return t.startswith("/start") or t in ["hola", "ok", "/admin", "/picks", "/grupo"]


def get_admin_chat_id() -> str:
    return (os.getenv("TELEGRAM_ADMIN_CHAT_ID") or os.getenv("ADMIN_TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID") or "").strip()
