# -*- coding: utf-8 -*-
"""V322 · SHARK AI LIVE COPILOT PRO
Safe contextual layer. Does not call external APIs. Uses cached/local payloads when available.
"""
from __future__ import annotations
from datetime import datetime


def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def build_shark_live_copilot_v322(previous_payload=None):
    previous_payload = previous_payload or {}
    events = previous_payload.get("events") or []
    turning_points = previous_payload.get("turning_points") or []
    timeline_score = _safe_int(previous_payload.get("timeline_score"), 82)
    hot_events = [e for e in events if str(e.get("tone","")).lower() in ("hot","danger","value")]
    watch_events = [e for e in events if str(e.get("tone","")).lower() in ("watch","info")]
    if hot_events:
        main_mode = "HOT CONTEXTUAL"
        main_message = "SHARK detecta un tramo de alta atención. Conviene mirar momentum, evento reciente y salud de datos antes de decidir."
        action = "Abrir Match Center"
        href = "/cliente/match-center-premium"
        tone = "hot"
    elif turning_points:
        main_mode = "CAMBIO DETECTADO"
        main_message = "Hay puntos de giro recientes. SHARK recomienda revisar qué cambió y si el partido sigue estable."
        action = "Ver Turning Points"
        href = "/cliente/turning-points"
        tone = "watch"
    elif timeline_score >= 80:
        main_mode = "RADAR ACTIVO"
        main_message = "El directo está estable y con señales suficientes para seguimiento inteligente sin forzar decisiones."
        action = "Seguir timeline"
        href = "/cliente/live-timeline"
        tone = "watch"
    else:
        main_mode = "BAJA SEÑAL"
        main_message = "No hay suficiente intensidad o datos. Mejor esperar y dejar que el motor acumule snapshots."
        action = "Volver al centro"
        href = "/cliente/command-center"
        tone = "safe"

    return {
        "ok": True,
        "version": "V322",
        "touches_api": False,
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "headline": "SHARK Live Copilot activo",
        "subheadline": "Copiloto contextual sobre timeline, momentum y memoria sin gastar API extra.",
        "copilot_mode": main_mode,
        "copilot_tone": tone,
        "main_message": main_message,
        "primary_action": {"label": action, "href": href},
        "context_cards": [
            {"label": "Timeline", "value": timeline_score, "suffix": "/100", "tone": "watch" if timeline_score >= 70 else "safe"},
            {"label": "Eventos HOT", "value": len(hot_events), "suffix": "", "tone": "hot" if hot_events else "safe"},
            {"label": "Puntos de giro", "value": len(turning_points), "suffix": "", "tone": "watch" if turning_points else "safe"},
            {"label": "API", "value": 0, "suffix": " llamadas", "tone": "safe"},
        ],
        "insights": [
            {"title": "Qué está viendo SHARK", "text": "Cruza timeline, eventos recientes, score de actividad y puntos de giro cacheados."},
            {"title": "Qué debe hacer el cliente", "text": main_message},
            {"title": "Por qué es importante", "text": "Convierte el directo en una explicación clara, no solo en datos sueltos."},
        ],
        "next_steps": [
            {"label": "Centro de mando", "href": "/cliente/command-center"},
            {"label": "Timeline live", "href": "/cliente/live-timeline"},
            {"label": "Match Center", "href": "/cliente/match-center-premium"},
        ],
        "previous": previous_payload,
    }
