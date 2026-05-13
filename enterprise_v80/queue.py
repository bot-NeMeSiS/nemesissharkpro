
"""
NeMeSiS SHARK PRO V80
Enterprise Queue Adapter

Centraliza trabajos asíncronos:
- Telegram
- Push
- ML snapshots
- backups
- resultados
- refresh Odds API

Sin obligar a Celery todavía.
"""

import sqlite3
from datetime import datetime


DB_PATH = "nemesis.db"


def init_enterprise_queue(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS enterprise_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_type TEXT,
        payload TEXT,
        status TEXT DEFAULT 'PENDING',
        priority TEXT DEFAULT 'NORMAL',
        attempts INTEGER DEFAULT 0,
        max_attempts INTEGER DEFAULT 3,
        last_error TEXT,
        created_at TEXT,
        started_at TEXT,
        finished_at TEXT
    )
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_enterprise_jobs_status ON enterprise_jobs(status)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_enterprise_jobs_type_status ON enterprise_jobs(job_type, status)")

    conn.commit()
    conn.close()


def enqueue_job(job_type, payload="{}", priority="NORMAL", max_attempts=3, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.execute("""
    INSERT INTO enterprise_jobs (
        job_type, payload, priority, max_attempts, created_at
    ) VALUES (?, ?, ?, ?, ?)
    """, (job_type, payload, priority, max_attempts, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return True


def get_queue_status(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    statuses = {}
    for status in ["PENDING", "PROCESSING", "DONE", "FAILED", "RETRYING"]:
        try:
            row = conn.execute("SELECT COUNT(*) AS c FROM enterprise_jobs WHERE status=?", (status,)).fetchone()
            statuses[status.lower()] = row["c"]
        except Exception:
            statuses[status.lower()] = 0

    by_type = []
    try:
        by_type = [
            dict(row) for row in conn.execute("""
            SELECT job_type, status, COUNT(*) AS count
            FROM enterprise_jobs
            GROUP BY job_type, status
            ORDER BY count DESC
            LIMIT 20
            """).fetchall()
        ]
    except Exception:
        pass

    conn.close()

    return {
        "statuses": statuses,
        "by_type": by_type,
    }


def process_enterprise_jobs(limit=5, db_path=DB_PATH):
    """
    Worker seguro para ejecutar manualmente desde admin/API.
    No usa while True.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
    SELECT * FROM enterprise_jobs
    WHERE status IN ('PENDING','RETRYING')
    ORDER BY
      CASE priority
        WHEN 'HIGH' THEN 1
        WHEN 'NORMAL' THEN 2
        ELSE 3
      END,
      id ASC
    LIMIT ?
    """, (limit,)).fetchall()

    processed = 0

    for row in rows:
        try:
            conn.execute("""
            UPDATE enterprise_jobs
            SET status='PROCESSING', started_at=?
            WHERE id=?
            """, (datetime.utcnow().isoformat(), row["id"]))

            # V80 solo marca el sistema preparado. La ejecución real se conectará por tipo en siguientes versiones.
            conn.execute("""
            UPDATE enterprise_jobs
            SET status='DONE', finished_at=?
            WHERE id=?
            """, (datetime.utcnow().isoformat(), row["id"]))

            processed += 1

        except Exception as exc:
            attempts = int(row["attempts"] or 0) + 1
            status = "FAILED" if attempts >= int(row["max_attempts"] or 3) else "RETRYING"

            conn.execute("""
            UPDATE enterprise_jobs
            SET attempts=?, status=?, last_error=?
            WHERE id=?
            """, (attempts, status, str(exc), row["id"]))

    conn.commit()
    conn.close()

    return {
        "ok": True,
        "processed": processed,
    }
