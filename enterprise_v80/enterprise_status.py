
import os
from .database import get_db_health, get_database_mode
from .cache import cache_stats
from .queue import get_queue_status, init_enterprise_queue
from .migration_readiness import get_migration_readiness


def get_enterprise_scale_status():
    try:
        init_enterprise_queue()
    except Exception:
        pass

    db = get_db_health()
    cache = cache_stats()
    queue = get_queue_status()
    migration = get_migration_readiness()

    modules = [
        {"name": "Database Adapter", "status": "ACTIVO", "description": get_database_mode()},
        {"name": "PostgreSQL Ready Layer", "status": "PREPARADO", "description": "Punto central de migración creado"},
        {"name": "Redis Ready Cache", "status": "PREPARADO", "description": cache["mode"]},
        {"name": "Enterprise Jobs Queue", "status": "ACTIVO", "description": "Cola central SQLite fallback"},
        {"name": "Worker Entrypoint", "status": "PREPARADO", "description": "Background worker opcional"},
        {"name": "SQLite WAL/Optimize", "status": "ACTIVO" if db.get("ok") else "REVISAR", "description": db.get("journal_mode", "UNKNOWN")},
        {"name": "Migration Readiness", "status": migration["status"], "description": migration["recommendation"]},
    ]

    score = 88
    if db.get("ok"):
        score += 5
    if migration.get("postgres_configured"):
        score += 4
    if migration.get("redis_configured"):
        score += 3
    if queue["statuses"].get("failed", 0) > 0:
        score -= 8

    score = max(min(score, 100), 0)

    return {
        "status": "ENTERPRISE SCALE READY" if score >= 90 else "ENTERPRISE FOUNDATION READY",
        "enterprise_score": score,
        "database": db,
        "cache": cache,
        "queue": queue,
        "migration": migration,
        "modules": modules,
        "next_step": "Cuando haya usuarios reales: PostgreSQL + Redis + Background Worker separado.",
    }
