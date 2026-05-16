# -*- coding: utf-8 -*-
"""V325 · Smart Client Match Flow
Capa segura: no llama APIs externas. Construye una experiencia guiada usando
estado local, snapshots/cache disponibles y fallbacks seguros.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List


def _safe_len(value: Any) -> int:
    try:
        return len(value or [])
    except Exception:
        return 0


def build_smart_client_flow_v325(base: Dict[str, Any] | None = None) -> Dict[str, Any]:
    base = base or {}
    timeline_events = base.get('timeline') or base.get('events') or []
    signals = base.get('signals') or base.get('turning_points') or []
    live_count = max(_safe_len(timeline_events), _safe_len(signals), 3)

    flow_steps: List[Dict[str, str]] = [
        {
            'title': '1. Revisa tu foco live',
            'text': 'Empieza por los partidos con mayor actividad, no por una lista infinita.',
            'action': 'Abrir foco live',
            'tone': 'hot'
        },
        {
            'title': '2. Mira el motivo',
            'text': 'Cada señal debe explicar qué cambió: momentum, timing, valor o salud de datos.',
            'action': 'Ver explicación SHARK',
            'tone': 'value'
        },
        {
            'title': '3. Decide sin ruido',
            'text': 'Seguir, esperar o descartar. La app guía la decisión sin forzar apuestas.',
            'action': 'Tomar decisión',
            'tone': 'safe'
        },
    ]

    return {
        'ok': True,
        'version': 'V325',
        'touches_api': False,
        'headline': 'Smart Client Match Flow activo',
        'subheadline': 'Una capa que convierte live, timeline y SHARK en recorrido claro para el cliente.',
        'client_score': min(99, 90 + live_count),
        'status': 'ESTABLE',
        'today_focus': [
            {'label': 'Foco recomendado', 'value': 'Live + Timeline', 'tone': 'hot'},
            {'label': 'Ruido reducido', 'value': 'Alto', 'tone': 'safe'},
            {'label': 'API extra', 'value': '0', 'tone': 'safe'},
            {'label': 'Continuidad', 'value': 'Activa', 'tone': 'value'},
        ],
        'flow_steps': flow_steps,
        'match_actions': [
            {'title': 'Seguir partido caliente', 'text': 'Prioriza partidos con cambios recientes y señal limpia.', 'tag': 'HOT'},
            {'title': 'Esperar mejor timing', 'text': 'Si hay baja salud de datos, la mejor acción puede ser observar.', 'tag': 'WATCH'},
            {'title': 'Abrir Match Center', 'text': 'Para decisiones importantes, entrar al ecosistema completo del partido.', 'tag': 'MATCH'},
            {'title': 'Preguntar a SHARK', 'text': 'Pedir explicación contextual cuando el momentum cambie.', 'tag': 'SHARK'},
        ],
        'premium_notes': [
            'Menos pantallas sueltas y más recorrido guiado.',
            'Mejor sensación de app nativa sin tocar APIs externas.',
            'Base preparada para personalización y memoria real.'
        ],
        'generated_at': datetime.utcnow().isoformat(timespec='seconds') + 'Z'
    }
