
"""
NeMeSiS SHARK PRO V80
Enterprise Cache Adapter

Preparado para Redis, con fallback en memoria para Render/free tier.
"""

import os
import time
import json


_MEMORY_CACHE = {}


def redis_enabled():
    return bool(os.getenv("REDIS_URL")) and os.getenv("V80_REDIS_ENABLED", "false").lower() == "true"


def get_cache_mode():
    return "REDIS_READY" if redis_enabled() else "MEMORY_FALLBACK"


def cache_set(key, value, ttl=300):
    payload = {
        "value": value,
        "expires": time.time() + ttl,
    }

    # Fallback estable sin dependencia externa
    _MEMORY_CACHE[key] = payload
    return True


def cache_get(key, default=None):
    item = _MEMORY_CACHE.get(key)
    if not item:
        return default

    if time.time() > item["expires"]:
        _MEMORY_CACHE.pop(key, None)
        return default

    return item["value"]


def cache_delete(key):
    _MEMORY_CACHE.pop(key, None)


def cache_stats():
    now = time.time()
    active = 0
    expired = 0

    for item in list(_MEMORY_CACHE.values()):
        if now > item["expires"]:
            expired += 1
        else:
            active += 1

    return {
        "mode": get_cache_mode(),
        "active_items": active,
        "expired_items": expired,
        "redis_configured": bool(os.getenv("REDIS_URL")),
    }
