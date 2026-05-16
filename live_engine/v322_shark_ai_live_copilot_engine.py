"""
NeMeSiS SHARK PRO · V322
SHARK AI Live Copilot PRO

Convierte el timeline V321 en un copiloto contextual: explica momentum,
resume cambios, prioriza acciones y prepara memoria para ML futuro.
Cache-first: no llama APIs externas.
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


def _tone(score: int) -> str:
    if score >= 84:
        return "hot"
    if score >= 68:
        return "watch"
    if score >= 50:
        return "info"
    return "safe"


def _copilot_verdict(score: int, title: str) -> Dict[str, str]:
    if score >= 88:
        return {
            "label": "MIRAR AHORA",
            "tone": "hot",
            "message": f"SHARK detecta una señal fuerte en {title}. Conviene revisarlo ya, sin entrar a ciegas.",
            "next_step": "Abrir análisis del punto caliente",
        }
    if score >= 72:
        return {
            "label": "VIGILAR DE CERCA",
            "tone": "watch",
            "message": f"Hay movimiento interesante en {title}. Todavía no fuerza acción, pero merece seguimiento.",
            "next_step": "Mantener en radar live",
        }
    if score >= 55:
        return {
            "label": "CONTEXTO ÚTIL",
            "tone": "info",
            "message": f"{title} aporta contexto para entender el directo, pero la señal aún no es decisiva.",
            "next_step": "Esperar más datos",
        }
    return {
        "label": "NO FORZAR",
        "tone": "safe",
        "message": f"SHARK no ve suficiente claridad en {title}. Mejor proteger banca y esperar.",
        "next_step": "Volver al Command Center",
    }


def build_shark_ai_live_copilot_v322(v321_payload: Dict[str, Any]) -> Dict[str, Any]:
    v321_payload = v321_payload or {}
    events = _lst(v321_payload.get("events"))
    turning_points = _lst(v321_payload.get("turning_points")) or events[:3]

    insights: List[Dict[str, Any]] = []
    for idx, event in enumerate(events[:8]):
        score = _int(event.get("impact"), 50)
        title = str(event.get("title") or "señal live")
        verdict = _copilot_verdict(score, title)
        event_type = str(event.get("event_type") or "CONTEXT")
        insight = {
            "id": f"v322-insight-{idx+1}",
            "title": title,
            "score": score,
            "tone": verdict["tone"],
            "verdict": verdict["label"],
            "explanation": verdict["message"],
            "why": str(event.get("why_it_matters") or "La señal modifica la prioridad del seguimiento."),
            "changed": event_type.replace("_", " ").title(),
            "next_step": verdict["next_step"],
            "href": str(event.get("href") or "/cliente/live-timeline"),
            "source": "timeline_v321",
        }
        insights.append(insight)

    if not insights:
        insights = [{
            "id": "v322-safe-1",
            "title": "Copiloto SHARK preparado",
            "score": 61,
            "tone": "watch",
            "verdict": "RADAR LISTO",
            "explanation": "SHARK está listo para explicar momentum, cambios y próximos pasos cuando haya datos cacheados.",
            "why": "Mantiene experiencia premium sin gastar API al abrir.",
            "changed": "Contexto seguro",
            "next_step": "Abrir Command Center",
            "href": "/cliente/command-center",
            "source": "safe_fallback",
        }]

    hot = [x for x in insights if _int(x.get("score"), 0) >= 84]
    watch = [x for x in insights if 68 <= _int(x.get("score"), 0) < 84]
    copilot_score = max(88, min(99, 90 + len(hot) * 3 + len(watch)))
    top = insights[0]

    conversation_cards = [
        {
            "role": "SHARK",
            "label": top.get("verdict", "RADAR"),
            "text": top.get("explanation", "SHARK mantiene el radar activo."),
            "tone": top.get("tone", "watch"),
        },
        {
            "role": "Contexto",
            "label": "Qué cambió",
            "text": f"Cambio principal detectado: {top.get('changed','Contexto live')}. {top.get('why','')}",
            "tone": "info",
        },
        {
            "role": "Acción",
            "label": "Siguiente paso",
            "text": top.get("next_step", "Seguir mirando el directo."),
            "tone": top.get("tone", "watch"),
        },
    ]

    memory_seed = {
        "watched_events": len(events),
        "turning_points": len(turning_points),
        "hot_signals": len(hot),
        "watch_signals": len(watch),
        "last_context": top.get("title"),
        "ready_for_ml": True,
    }

    return {
        "ok": True,
        "version": "V322",
        "name": "SHARK AI Live Copilot PRO",
        "touches_api": False,
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "headline": "SHARK ya no solo muestra datos: te explica qué está pasando.",
        "subheadline": "Copiloto live contextual con momentum explicado, próximos pasos y memoria preparada para ML.",
        "copilot_score": copilot_score,
        "status_strip": [
            {"label": "Insights", "value": str(len(insights)), "tone": "info"},
            {"label": "HOT", "value": str(len(hot)), "tone": "hot" if hot else "safe"},
            {"label": "WATCH", "value": str(len(watch)), "tone": "watch" if watch else "safe"},
            {"label": "API", "value": "0", "tone": "ok"},
        ],
        "primary_insight": top,
        "insights": insights,
        "conversation_cards": conversation_cards,
        "memory_seed": memory_seed,
        "smart_actions": [
            {"label": "Abrir Timeline Live", "href": "/cliente/live-timeline", "type": "timeline"},
            {"label": "Ir al Command Center", "href": "/cliente/command-center", "type": "command"},
            {"label": "Continuar mi día", "href": "/cliente/experiencia", "type": "continue"},
            {"label": "Mi cuenta", "href": "/cliente/dashboard", "type": "account"},
        ],
        "experience_principles": [
            "Explicar antes de empujar acción.",
            "Convertir momentum en lenguaje claro.",
            "Reducir pantallas sueltas: SHARK guía el recorrido.",
            "Preparar memoria y patrones para ML futuro.",
            "Cero gasto API al abrir esta experiencia.",
        ],
        "bridge": {"from": "V321 Live Timeline", "to": "V322 SHARK AI Live Copilot", "next": "V323 Flow Automation / ML Signals"},
    }
