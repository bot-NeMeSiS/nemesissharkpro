# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, Any


def build_client_experience_summary_v325(flow: Dict[str, Any], match_flow: Dict[str, Any], shark: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'ok': True,
        'version': 'V325',
        'touches_api': False,
        'flow': flow,
        'match_flow': match_flow,
        'shark': shark,
        'summary': {
            'headline': 'Experiencia cliente guiada y consolidada',
            'impact': 'Más claridad, menos ruido y mejor sensación premium.',
            'safe_to_open': True
        }
    }
