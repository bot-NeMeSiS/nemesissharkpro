
"""
NeMeSiS SHARK PRO V80
Worker entrypoint preparado.

En Render puedes crear un Background Worker separado más adelante:
python -m enterprise_v80.worker

Por seguridad, no ejecuta loop infinito salvo que V80_WORKER_LOOP=true.
"""

import os
import time
from .queue import init_enterprise_queue, process_enterprise_jobs


def run_once():
    init_enterprise_queue()
    return process_enterprise_jobs(limit=int(os.getenv("V80_WORKER_BATCH_SIZE", "5")))


def run_loop():
    init_enterprise_queue()
    interval = int(os.getenv("V80_WORKER_INTERVAL_SECONDS", "30"))

    while os.getenv("V80_WORKER_LOOP", "false").lower() == "true":
        result = run_once()
        print("[V80 Worker]", result)
        time.sleep(interval)


if __name__ == "__main__":
    if os.getenv("V80_WORKER_LOOP", "false").lower() == "true":
        run_loop()
    else:
        print(run_once())
