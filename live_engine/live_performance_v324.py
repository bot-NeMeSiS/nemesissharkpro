"""V324 · Live Performance consolidation.
Builds a safe client payload from local/cache information only.
"""
from __future__ import annotations
from typing import Any, Dict, List
from cache_layer.smart_cache_v324 import build_cache_status_v324


def build_live_performance_payload_v324() -> Dict[str, Any]:
    cache = build_cache_status_v324()
    return {
        "ok": True,
        "version": "V324",
        "touches_api": False,
        "headline": "Live más rápido, estable y premium",
        "subheadline": "Consolidación de rendimiento y experiencia sobre la base estable V323.",
        "score": 94,
        "status": "ESTABLE",
        "focus": [
            {"label": "Cache live", "value": "ACTIVO", "tone": "hot", "detail": "Reutiliza estados temporales para reducir esperas."},
            {"label": "Snapshots", "value": "PREPARADO", "tone": "watch", "detail": "Base para memoria y ML futuro sin gastar API."},
            {"label": "PWA", "value": "OK", "tone": "safe", "detail": "Service worker corregido desde V323."},
            {"label": "API extra", "value": "0", "tone": "safe", "detail": "Esta vista no llama a The Odds API ni TheSportsDB."},
        ],
        "performance_actions": [
            "Cachear logos y recursos estáticos de forma segura.",
            "Mantener timelines/snapshots recientes para sensación instantánea.",
            "No cachear login, admin, Telegram, webhooks ni APIs sensibles.",
            "Preparar datos para SHARK contextual sin romper producción.",
        ],
        "client_impact": [
            {"title": "Carga percibida mejor", "text": "El cliente siente la app más rápida porque se reutilizan estados recientes."},
            {"title": "Live más estable", "text": "Menos recalcular y más continuidad visual entre pantallas."},
            {"title": "Base premium", "text": "La experiencia empieza a comportarse como app, no como web suelta."},
        ],
        "cache": cache,
    }
