
"""
NeMeSiS SHARK PRO V80
PostgreSQL Migration Readiness

No migra automáticamente. Analiza preparación.
"""

import os
import sqlite3
from pathlib import Path


DB_PATH = "nemesis.db"


def get_sqlite_tables(db_path=DB_PATH):
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table'
        ORDER BY name
        """).fetchall()

        tables = []
        for row in rows:
            table = row["name"]
            count = None
            try:
                count = conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"]
            except Exception:
                pass
            tables.append({"table": table, "rows": count})

        conn.close()
        return tables
    except Exception as exc:
        return [{"table": "ERROR", "rows": str(exc)}]


def get_migration_readiness():
    tables = get_sqlite_tables()
    db_exists = Path(DB_PATH).exists()
    db_size_mb = round(Path(DB_PATH).stat().st_size / (1024 * 1024), 2) if db_exists else 0

    database_url = os.getenv("DATABASE_URL", "")
    postgres_configured = database_url.startswith("postgres://") or database_url.startswith("postgresql://")
    redis_configured = bool(os.getenv("REDIS_URL"))

    blockers = []
    if not db_exists:
        blockers.append("No se detecta nemesis.db todavía")
    if not postgres_configured:
        blockers.append("DATABASE_URL PostgreSQL no configurado")
    if not redis_configured:
        blockers.append("REDIS_URL no configurado")

    score = 82
    if postgres_configured:
        score += 10
    if redis_configured:
        score += 5
    if db_size_mb > 500:
        score -= 10

    score = max(min(score, 100), 0)

    return {
        "status": "POSTGRES READY" if postgres_configured else "SQLITE PRODUCTION SAFE",
        "migration_score": score,
        "sqlite_db_exists": db_exists,
        "sqlite_size_mb": db_size_mb,
        "postgres_configured": postgres_configured,
        "redis_configured": redis_configured,
        "blockers": blockers,
        "tables": tables,
        "recommendation": "Mantener SQLite para beta. Migrar a PostgreSQL cuando haya usuarios reales o pagos.",
    }
