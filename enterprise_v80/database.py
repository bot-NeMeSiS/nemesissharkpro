
"""
NeMeSiS SHARK PRO V80
Enterprise Database Adapter

Objetivo:
- Mantener SQLite funcionando.
- Preparar PostgreSQL sin obligarte a migrar hoy.
- Centralizar conexión DB para futuras migraciones.
"""

import os
import sqlite3
from contextlib import contextmanager


SQLITE_PATH = os.getenv("SQLITE_DB_PATH", "nemesis.db")
DATABASE_URL = os.getenv("DATABASE_URL", "")


def using_postgres():
    return DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://")


def get_database_mode():
    if using_postgres():
        return "POSTGRES_READY"
    return "SQLITE_ACTIVE"


def get_sqlite_connection(db_path=None):
    conn = sqlite3.connect(db_path or SQLITE_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    return conn


def get_connection():
    """
    Actualmente mantiene SQLite como runtime por compatibilidad.
    Si activas PostgreSQL, este archivo ya deja el punto central preparado.
    Para PostgreSQL real se recomienda añadir psycopg/SQLAlchemy en la siguiente migración controlada.
    """
    return get_sqlite_connection()


@contextmanager
def db_session():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_enterprise_db_settings():
    with db_session() as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA busy_timeout=8000")
        conn.execute("PRAGMA optimize")


def get_db_health():
    try:
        conn = get_sqlite_connection()
        row = conn.execute("PRAGMA integrity_check").fetchone()
        wal = conn.execute("PRAGMA journal_mode").fetchone()[0]
        conn.close()
        return {
            "ok": row[0] == "ok",
            "integrity": row[0],
            "journal_mode": wal,
            "mode": get_database_mode(),
        }
    except Exception as exc:
        return {
            "ok": False,
            "integrity": str(exc),
            "journal_mode": "UNKNOWN",
            "mode": get_database_mode(),
        }
