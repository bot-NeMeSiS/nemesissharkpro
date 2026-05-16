# -*- coding: utf-8 -*-
"""Motor de flujo de partido V325. Seguro y sin dependencias externas."""
from __future__ import annotations
from datetime import datetime
from typing import Dict, Any


def build_match_flow_engine_v325() -> Dict[str, Any]:
    return {
        'ok': True,
        'version': 'V325',
        'touches_api': False,
        'engine': 'match_flow_engine',
        'states': [
            {'key': 'hot', 'label': 'HOT', 'meaning': 'Partido con actividad o cambio relevante.'},
            {'key': 'watch', 'label': 'WATCH', 'meaning': 'Partido interesante para vigilar sin entrar todavía.'},
            {'key': 'value', 'label': 'VALUE', 'meaning': 'Posible valor detectado, requiere revisar contexto.'},
            {'key': 'low_data', 'label': 'LOW DATA', 'meaning': 'Datos insuficientes: evitar decisiones fuertes.'},
        ],
        'rules': [
            'No recomendar acción fuerte si la salud de datos es baja.',
            'Explicar siempre el motivo de cada cambio de estado.',
            'Priorizar claridad cliente sobre cantidad de información.',
        ],
        'generated_at': datetime.utcnow().isoformat(timespec='seconds') + 'Z'
    }
