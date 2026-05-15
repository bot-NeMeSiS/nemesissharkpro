"""
NeMeSiS SHARK PRO · V320
Premium Client Command Center PRO

Capa de producto para que el cliente no vea pantallas sueltas, sino un centro de mando:
foco, decisión, urgencia, continuidad, alertas y acciones claras. Cache-first y sin APIs externas.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List


def _lst(v: Any) -> List[Dict[str, Any]]:
    return [x for x in v if isinstance(x, dict)] if isinstance(v, list) else []


def _int(v: Any, default: int = 0) -> int:
    try:
        return int(float(v))
    except Exception:
        return default


def _priority(card: Dict[str, Any]) -> int:
    text = " ".join(str(card.get(k, "")) for k in ("status", "headline", "title", "urgency", "reason")).upper()
    score = _int(card.get("activity"), 45)
    if "HOT" in text: score += 28
    if "VALUE" in text or "EDGE" in text: score += 18
    if "WATCH" in text or "VIGIL" in text: score += 12
    if "LOW" in text or "SAFE" in text: score -= 10
    return max(0, min(100, score))


def _decision(score: int) -> Dict[str, str]:
    if score >= 82:
        return {"label": "ACTUAR", "tone": "hot", "text": "Prioridad alta: revisar ahora y decidir con contexto."}
    if score >= 64:
        return {"label": "VIGILAR", "tone": "watch", "text": "Buen punto de seguimiento: espera confirmación o movimiento."}
    if score >= 46:
        return {"label": "SEGUIR", "tone": "calm", "text": "Contexto útil, sin urgencia fuerte todavía."}
    return {"label": "ESPERAR", "tone": "safe", "text": "No forzar decisión: datos o señal insuficiente."}


def build_client_command_center_v320(v319_payload: Dict[str, Any]) -> Dict[str, Any]:
    v319_payload = v319_payload or {}
    cards = _lst(v319_payload.get("experience_cards"))
    actions = _lst(v319_payload.get("next_actions"))
    sections = _lst(v319_payload.get("sections"))

    command_cards = []
    for idx, c in enumerate(cards[:8], start=1):
        p = _priority(c)
        d = _decision(p)
        command_cards.append({
            "rank": idx,
            "title": str(c.get("title") or "Partido / módulo monitorizado"),
            "status": str(c.get("status") or d["label"]),
            "priority": p,
            "decision": d,
            "headline": str(c.get("headline") or d["text"]),
            "reason": str(c.get("reason") or "Ordenado por prioridad del sistema cliente."),
            "primary_action": str(c.get("action") or d["label"].title()),
            "href": str(c.get("href") or "/cliente/experiencia"),
            "microcopy": "Mira esto primero" if p >= 82 else "Mantener en radar" if p >= 64 else "Sin prisa, pero guardado",
            "client_feel": "live-premium" if p >= 64 else "calm-premium"
        })

    if not command_cards:
        command_cards = [
            {"rank": 1, "title": "Tu centro de mando está preparado", "status": "READY", "priority": 55, "decision": _decision(55), "headline": "Cuando haya datos cacheados, aquí aparecerá qué mirar primero.", "reason": "Pantalla segura sin consumo extra de API.", "primary_action": "Abrir Mi día", "href": "/cliente/experiencia", "microcopy": "Entrada principal", "client_feel": "safe-premium"},
            {"rank": 2, "title": "Live Focus", "status": "WATCH", "priority": 62, "decision": _decision(62), "headline": "Zona preparada para partidos en seguimiento.", "reason": "Conecta Live, Match Center y Continuity.", "primary_action": "Ir a Live", "href": "/cliente/live-visual", "microcopy": "Vigilar directo", "client_feel": "live-premium"},
        ]

    top = sorted(command_cards, key=lambda x: x["priority"], reverse=True)
    hot = sum(1 for x in top if x["priority"] >= 82)
    watch = sum(1 for x in top if 64 <= x["priority"] < 82)
    calm = sum(1 for x in top if x["priority"] < 64)
    command_score = max(84, min(99, 88 + hot*3 + watch - calm//3))

    command_strip = [
        {"label": "Ahora", "value": f"{hot} HOT", "tone": "hot" if hot else "safe"},
        {"label": "Radar", "value": f"{watch} WATCH", "tone": "watch" if watch else "safe"},
        {"label": "Contexto", "value": f"{len(top)} módulos", "tone": "info"},
        {"label": "API", "value": "0 llamadas", "tone": "ok"},
    ]

    smart_actions = []
    if hot:
        smart_actions.append({"label": "Revisar prioridad HOT", "href": top[0].get("href", "/cliente/live-visual"), "type": "hot", "urgency": "alta"})
    smart_actions.extend(actions[:4])
    smart_actions.extend([
        {"label": "Abrir Command Center", "href": "/cliente/command-center", "type": "command", "urgency": "normal"},
        {"label": "Volver a mi cuenta", "href": "/cliente/dashboard", "type": "account", "urgency": "normal"},
    ])

    return {
        "ok": True,
        "version": "V320",
        "name": "Premium Client Command Center PRO",
        "touches_api": False,
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "headline": "Tu centro de mando decide qué merece atención ahora.",
        "subheadline": "Menos buscar, más entender: foco, prioridad, decisión y siguiente acción en una sola experiencia.",
        "command_score": command_score,
        "mood": "COMMAND CENTER PREMIUM",
        "command_strip": command_strip,
        "command_cards": top,
        "smart_actions": smart_actions[:6],
        "sections": sections or [
            {"id": "home", "label": "Mi día", "href": "/cliente/experiencia"},
            {"id": "live", "label": "Live", "href": "/cliente/live-visual"},
            {"id": "match", "label": "Match Center", "href": "/cliente/match-center-premium"},
            {"id": "account", "label": "Cuenta", "href": "/cliente/dashboard"},
        ],
        "experience_principles": [
            "El cliente entra y ve qué mirar primero.",
            "Cada card tiene decisión, prioridad y acción.",
            "La app acompaña, no obliga a navegar a ciegas.",
            "No consume API al abrir: trabaja sobre caché/memoria.",
            "Base preparada para SHARK AI contextual y timeline real."
        ],
        "bridge": {"from": "V319 Unified Experience System", "to": "V320 Premium Client Command Center", "next": "V321 Real Timeline / Decision Feed"}
    }
