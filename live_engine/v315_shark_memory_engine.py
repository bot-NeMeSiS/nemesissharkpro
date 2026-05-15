
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import os
import hashlib


def _data_dir() -> Path:
    base = os.environ.get("DATABASE_PATH") or os.environ.get("DB_PATH") or "/data/database.db"
    try:
        p = Path(base)
        if p.suffix:
            d = p.parent
        else:
            d = p
        d.mkdir(parents=True, exist_ok=True)
        return d
    except Exception:
        fallback = Path("instance")
        fallback.mkdir(exist_ok=True)
        return fallback


def _store_path() -> Path:
    return _data_dir() / "shark_memory_snapshots_v315.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_int(value, default=0):
    try:
        return int(float(value or default))
    except Exception:
        return default


def _match_key(item: dict) -> str:
    raw = "|".join([
        str(item.get("id") or ""),
        str(item.get("title") or item.get("match") or ""),
        str(item.get("league") or ""),
        str(item.get("kickoff_time") or item.get("time") or ""),
    ])
    return hashlib.sha1(raw.encode("utf-8", errors="ignore")).hexdigest()[:14]


def _read_store() -> dict:
    p = _store_path()
    if not p.exists():
        return {"version": "V315", "created_at": _now(), "snapshots": [], "matches": {}}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("bad store")
        data.setdefault("version", "V315")
        data.setdefault("created_at", _now())
        data.setdefault("snapshots", [])
        data.setdefault("matches", {})
        return data
    except Exception:
        return {"version": "V315", "created_at": _now(), "snapshots": [], "matches": {}, "recovered": True}


def _write_store(data: dict) -> None:
    p = _store_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)


def build_shark_memory_v315(v314_payload: dict, persist: bool = True) -> dict:
    """Memoria live cache-first sobre V314.
    Guarda snapshots ligeros en disco persistente (/data si existe), sin tocar APIs externas.
    """
    generated_at = _now()
    centers = list((v314_payload or {}).get("centers") or [])
    store = _read_store()
    memory_matches = dict(store.get("matches") or {})

    snapshot_items = []
    for center in centers[:20]:
        key = _match_key(center)
        previous = dict(memory_matches.get(key) or {})
        momentum = _safe_int(center.get("momentum"), 0)
        prev_momentum = _safe_int(previous.get("last_momentum"), momentum)
        delta = momentum - prev_momentum
        signal = str(center.get("signal") or center.get("trigger") or "WATCH").upper()
        history_count = _safe_int(previous.get("history_count"), 0) + 1
        trend = _trend(delta, signal, history_count)
        memory_status = _memory_status(history_count, delta, signal)
        item = {
            "key": key,
            "title": center.get("title") or center.get("match") or "Partido",
            "league": center.get("league") or "Competición",
            "signal": signal,
            "momentum": momentum,
            "previous_momentum": prev_momentum,
            "delta": delta,
            "trend": trend,
            "memory_status": memory_status,
            "history_count": history_count,
            "data_health": center.get("data_health") or {"level": center.get("health") or "WATCH"},
            "decision": center.get("decision") or center.get("recommended_action") or "Seguir observando",
            "recap": center.get("recap") or center.get("subtitle") or "Snapshot live guardado para contexto futuro.",
            "updated_at": generated_at,
        }
        snapshot_items.append(item)
        memory_matches[key] = {
            "title": item["title"],
            "league": item["league"],
            "first_seen_at": previous.get("first_seen_at") or generated_at,
            "last_seen_at": generated_at,
            "last_signal": signal,
            "last_momentum": momentum,
            "best_momentum": max(_safe_int(previous.get("best_momentum"), momentum), momentum),
            "history_count": history_count,
            "last_trend": trend,
            "last_delta": delta,
        }

    snapshot = {
        "id": hashlib.sha1((generated_at + str(len(snapshot_items))).encode()).hexdigest()[:16],
        "created_at": generated_at,
        "total": len(snapshot_items),
        "hot": len([x for x in snapshot_items if x["signal"] == "HOT"]),
        "value": len([x for x in snapshot_items if x["signal"] == "VALUE"]),
        "rising": len([x for x in snapshot_items if x["delta"] > 0]),
        "falling": len([x for x in snapshot_items if x["delta"] < 0]),
        "avg_momentum": int(round(sum(x["momentum"] for x in snapshot_items) / max(1, len(snapshot_items)))) if snapshot_items else 0,
    }

    snapshots = list(store.get("snapshots") or [])
    snapshots.append(snapshot)
    snapshots = snapshots[-80:]
    store.update({
        "version": "V315",
        "updated_at": generated_at,
        "snapshots": snapshots,
        "matches": memory_matches,
    })
    if persist:
        try:
            _write_store(store)
        except Exception as exc:
            store["write_error"] = str(exc)[:160]

    return {
        "ok": True,
        "version": "V315",
        "mode": "shark-memory-snapshot-cache-first",
        "touches_api": False,
        "generated_at": generated_at,
        "headline": _headline(snapshot, snapshot_items),
        "summary": {
            **snapshot,
            "stored_matches": len(memory_matches),
            "stored_snapshots": len(snapshots),
            "memory_health": _memory_health(len(memory_matches), len(snapshots), snapshot_items),
        },
        "memory_cards": snapshot_items,
        "timeline": _timeline(snapshots),
        "ai_context": _ai_context(snapshot, snapshot_items),
        "ml_ready": {
            "enabled": True,
            "message": "Base preparada para ML futuro: snapshots, momentum, deltas, señales y salud de datos.",
            "features": ["momentum", "delta", "signal", "history_count", "data_health", "decision"],
        },
        "storage": {"path": str(_store_path()), "persistent_ready": str(_store_path()).startswith("/data")},
        "source_version": (v314_payload or {}).get("version", "V314"),
    }


def build_live_history_v315(limit: int = 30) -> dict:
    store = _read_store()
    matches = list((store.get("matches") or {}).values())
    matches.sort(key=lambda x: x.get("last_seen_at") or "", reverse=True)
    snapshots = list(store.get("snapshots") or [])[-limit:]
    return {
        "ok": True,
        "version": "V315",
        "touches_api": False,
        "summary": {
            "stored_matches": len(matches),
            "stored_snapshots": len(snapshots),
            "last_snapshot": snapshots[-1] if snapshots else None,
        },
        "recent_matches": matches[:limit],
        "snapshots": snapshots,
        "storage": {"path": str(_store_path()), "persistent_ready": str(_store_path()).startswith("/data")},
    }


def _trend(delta: int, signal: str, count: int) -> str:
    if count <= 1:
        return "NUEVO"
    if delta >= 12 or signal == "HOT":
        return "SUBE FUERTE"
    if delta >= 4:
        return "SUBE"
    if delta <= -10:
        return "BAJA FUERTE"
    if delta <= -3:
        return "BAJA"
    return "ESTABLE"


def _memory_status(count: int, delta: int, signal: str) -> str:
    if count <= 1:
        return "Primer snapshot guardado"
    if signal == "HOT" and delta >= 0:
        return "Patrón caliente confirmado"
    if abs(delta) <= 3:
        return "Comportamiento estable"
    if delta > 0:
        return "Momentum ganando fuerza"
    return "Momentum perdiendo fuerza"


def _memory_health(total_matches: int, total_snapshots: int, items: list) -> str:
    if not items:
        return "ESPERANDO DATOS"
    if total_snapshots >= 10 and total_matches >= 10:
        return "HISTÓRICO FUERTE"
    if total_snapshots >= 3:
        return "MEMORIA ACTIVA"
    return "INICIANDO MEMORIA"


def _headline(snapshot: dict, items: list) -> str:
    if not items:
        return "SHARK Memory preparado: esperando Match Center cacheado."
    if snapshot.get("hot"):
        return f"SHARK Memory detecta {snapshot['hot']} foco(s) HOT y guarda contexto live."
    if snapshot.get("rising"):
        return f"SHARK Memory guarda {snapshot['rising']} partido(s) con momentum al alza."
    return "SHARK Memory activo: contexto live guardado para continuidad y ML futuro."


def _timeline(snapshots: list) -> list:
    out = []
    for s in snapshots[-12:]:
        out.append({
            "time": s.get("created_at"),
            "label": f"{s.get('total', 0)} partidos · {s.get('avg_momentum', 0)} momentum medio",
            "hot": s.get("hot", 0),
            "rising": s.get("rising", 0),
        })
    return out


def _ai_context(snapshot: dict, items: list) -> dict:
    top = sorted(items, key=lambda x: (x.get("signal") != "HOT", -x.get("momentum", 0)))[:3]
    return {
        "summary_for_shark_ai": "Contexto live persistente preparado para respuestas más inteligentes.",
        "top_focus": [{"title": x["title"], "signal": x["signal"], "momentum": x["momentum"], "trend": x["trend"]} for x in top],
        "recommended_tone": "prudente" if snapshot.get("avg_momentum", 0) < 55 else "alerta premium",
    }
