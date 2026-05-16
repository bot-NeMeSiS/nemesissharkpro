# -*- coding: utf-8 -*-
"""Briefing SHARK para cliente V325. No llama OpenAI ni APIs externas."""
from __future__ import annotations
from typing import Dict, Any


def build_shark_client_briefing_v325(context: Dict[str, Any] | None = None) -> Dict[str, Any]:
    context = context or {}
    return {
        'ok': True,
        'version': 'V325',
        'touches_api': False,
        'briefing_title': 'Briefing SHARK del día',
        'briefing': 'Entra por el foco live, revisa el motivo de cada señal y usa Match Center para decidir con contexto.',
        'insights': [
            'La prioridad ya no es ver más partidos, sino ver mejor los importantes.',
            'Las señales HOT/WATCH deben ir acompañadas de explicación y salud de datos.',
            'Cuando haya duda, SHARK debe recomendar esperar antes que forzar una entrada.'
        ],
        'context_received': bool(context)
    }
