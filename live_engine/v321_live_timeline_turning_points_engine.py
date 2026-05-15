"""
NeMeSiS SHARK PRO · V321
Live Timeline & Turning Points PRO

Convierte el Command Center en una historia viva: eventos, cambios de momentum,
turning points, feed de decisión y recap. Cache-first: no llama APIs externas.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Any, Dict, List


def _lst(v: Any) -> List[Dict[str, Any]]:
    return [x for x in v if isinstance(x, dict)] if isinstance(v, list) else []


def _int(v: Any, default: int = 0) -> int:
    try:
        return int(float(v))
    except Exception:
        return default


def _decision(score: int) -> Dict[str, str]:
    if score >= 84:
        return {"label": "PUNTO CLAVE", "tone": "hot", "copy": "El partido o módulo merece revisión inmediata."}
    if score >= 68:
        return {"label": "CAMBIO IMPORTANTE", "tone": "watch", "copy": "Hay señal suficiente para vigilar la evolución."}
    if score >= 50:
        return {"label": "SEÑAL SUAVE", "tone": "info", "copy": "Contexto útil, todavía sin presión de acción."}
    return {"label": "SIN FORZAR", "tone": "safe", "copy": "Mejor esperar a datos más claros."}


def _event_type(score: int, status: str) -> str:
    text = (status or "").upper()
    if score >= 84 or "HOT" in text:
        return "HOT_SHIFT"
    if "VALUE" in text or score >= 72:
        return "VALUE_WINDOW"
    if "WATCH" in text or score >= 60:
        return "WATCH_SIGNAL"
    if "LOW" in text:
        return "DATA_HEALTH"
    return "CONTEXT"


def build_live_timeline_turning_points_v321(v320_payload: Dict[str, Any]) -> Dict[str, Any]:
    v320_payload = v320_payload or {}
    cards = _lst(v320_payload.get("command_cards"))
    base_time = datetime.utcnow().replace(second=0, microsecond=0)

    events: List[Dict[str, Any]] = []
    for idx, card in enumerate(cards[:10]):
        score = _int(card.get("priority"), 50)
        status = str(card.get("status") or "WATCH")
        dec = _decision(score)
        minute = max(1, min(90, 7 + idx * 8 + (score % 9)))
        event_type = _event_type(score, status)
        events.append({
            "id": f"v321-{idx+1}",
            "minute": minute,
            "clock": (base_time + timedelta(minutes=idx*3)).isoformat(timespec="minutes") + "Z",
            "title": str(card.get("title") or "Señal monitorizada"),
            "event_type": event_type,
            "tone": dec["tone"],
            "impact": score,
            "decision": dec,
            "summary": str(card.get("headline") or dec["copy"]),
            "why_it_matters": str(card.get("reason") or "Este punto modifica la prioridad del seguimiento."),
            "action_label": str(card.get("primary_action") or dec["label"]),
            "href": str(card.get("href") or "/cliente/command-center"),
            "data_health": "ALTA" if score >= 72 else "MEDIA" if score >= 50 else "BAJA",
        })

    if not events:
        events = [
            {"id":"v321-safe-1","minute":12,"clock":base_time.isoformat(timespec="minutes")+"Z","title":"Timeline preparado","event_type":"CONTEXT","tone":"safe","impact":52,"decision":_decision(52),"summary":"Cuando haya datos cacheados, aquí se ordenarán los cambios importantes.","why_it_matters":"La pantalla no consume API y mantiene una experiencia segura.","action_label":"Abrir Command Center","href":"/cliente/command-center","data_health":"SEGURA"},
            {"id":"v321-safe-2","minute":24,"clock":(base_time+timedelta(minutes=3)).isoformat(timespec="minutes")+"Z","title":"Radar live listo","event_type":"WATCH_SIGNAL","tone":"watch","impact":64,"decision":_decision(64),"summary":"Zona preparada para detectar momentum y turning points.","why_it_matters":"Conecta continuidad, memoria y centro de mando.","action_label":"Ir a Mi día","href":"/cliente/experiencia","data_health":"MEDIA"},
        ]

    events = sorted(events, key=lambda e: e.get("impact", 0), reverse=True)
    turning_points = [e for e in events if _int(e.get("impact"), 0) >= 68]
    hot = [e for e in events if _int(e.get("impact"), 0) >= 84]
    watch = [e for e in events if 60 <= _int(e.get("impact"), 0) < 84]
    timeline_score = max(86, min(99, 88 + len(hot)*3 + len(turning_points)))

    recap = {
        "title": "Resumen inteligente del directo",
        "text": "El sistema ordena los puntos de cambio por impacto para que el cliente entienda qué está pasando sin saltar entre pantallas.",
        "best_next_step": hot[0]["action_label"] if hot else (turning_points[0]["action_label"] if turning_points else "Seguir en radar"),
        "best_href": hot[0]["href"] if hot else (turning_points[0]["href"] if turning_points else "/cliente/command-center"),
    }

    return {
        "ok": True,
        "version": "V321",
        "name": "Live Timeline & Turning Points PRO",
        "touches_api": False,
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "headline": "La historia viva del partido, ordenada por impacto.",
        "subheadline": "Momentum, señales, cambios importantes y acciones en un timeline premium sin llamadas extra a API.",
        "timeline_score": timeline_score,
        "timeline_strip": [
            {"label": "Puntos clave", "value": str(len(turning_points)), "tone": "hot" if turning_points else "safe"},
            {"label": "HOT", "value": str(len(hot)), "tone": "hot" if hot else "safe"},
            {"label": "Radar", "value": str(len(watch)), "tone": "watch" if watch else "safe"},
            {"label": "API", "value": "0", "tone": "ok"},
        ],
        "events": events,
        "turning_points": turning_points[:5],
        "recap": recap,
        "experience_principles": [
            "El cliente entiende qué ha cambiado.",
            "Cada señal tiene impacto, motivo y acción.",
            "El timeline crea emoción sin saturar.",
            "Base directa para SHARK AI contextual y ML futuro.",
            "No consume API al abrir: trabaja sobre caché y memoria."
        ],
        "bridge": {"from": "V320 Command Center", "to": "V321 Live Timeline", "next": "V322 Smart Flow / Shark Contextual Feed"}
    }
