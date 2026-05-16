"""V324 · Smart Cache + Live Performance layer.
Safe file-based cache for Render persistent disk. It does not call external APIs.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_CACHE_DIR = Path(os.getenv("NEMESIS_CACHE_DIR", "/data/nemesis_cache"))
FALLBACK_CACHE_DIR = Path(os.getenv("NEMESIS_FALLBACK_CACHE_DIR", ".nemesis_cache"))

TTL = {
    "assets": 60 * 60 * 24 * 30,
    "logos": 60 * 60 * 24 * 14,
    "standings": 60 * 60 * 6,
    "matches": 60 * 4,
    "live": 30,
    "timeline": 60 * 3,
    "snapshots": 60 * 5,
    "default": 60 * 5,
}


def _safe_key(key: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(key))[:160]


def _cache_dir() -> Path:
    for candidate in (DEFAULT_CACHE_DIR, FALLBACK_CACHE_DIR):
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            test = candidate / ".write_test"
            test.write_text("ok", encoding="utf-8")
            test.unlink(missing_ok=True)
            return candidate
        except Exception:
            continue
    return Path(".")


class SmartCacheV324:
    def __init__(self, namespace: str = "default") -> None:
        self.namespace = _safe_key(namespace or "default")
        self.root = _cache_dir() / self.namespace
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, key: str) -> Path:
        return self.root / f"{_safe_key(key)}.json"

    def get(self, key: str, ttl: Optional[int] = None) -> Optional[Any]:
        path = self.path_for(key)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            created_at = float(payload.get("created_at", 0))
            ttl_value = int(ttl if ttl is not None else payload.get("ttl", TTL["default"]))
            if ttl_value > 0 and time.time() - created_at > ttl_value:
                return None
            return payload.get("data")
        except Exception:
            return None

    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> Dict[str, Any]:
        ttl_value = int(ttl if ttl is not None else TTL["default"])
        payload = {"created_at": time.time(), "ttl": ttl_value, "data": data}
        path = self.path_for(key)
        try:
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            return {"ok": True, "path": str(path), "ttl": ttl_value}
        except Exception as exc:
            return {"ok": False, "error": str(exc), "ttl": ttl_value}

    def status(self) -> Dict[str, Any]:
        files = list(self.root.glob("*.json")) if self.root.exists() else []
        total_bytes = sum(p.stat().st_size for p in files if p.exists())
        return {
            "namespace": self.namespace,
            "root": str(self.root),
            "items": len(files),
            "size_kb": round(total_bytes / 1024, 2),
            "ttl_profile": TTL,
        }


def build_cache_status_v324() -> Dict[str, Any]:
    namespaces = ["matches", "live", "timeline", "snapshots", "logos", "standings"]
    return {
        "ok": True,
        "version": "V324",
        "touches_api": False,
        "title": "Smart Cache + Live Performance",
        "summary": "Capa segura para acelerar experiencia live sin llamadas extra a APIs.",
        "namespaces": [SmartCacheV324(ns).status() for ns in namespaces],
    }
