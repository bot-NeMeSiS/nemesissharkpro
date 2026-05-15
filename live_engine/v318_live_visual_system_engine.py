# -*- coding: utf-8 -*-
"""V318 · Live Visual System PRO.
Capa visual cache-first sobre V317. No llama a APIs externas.
Convierte el estado live en señales visuales premium para cliente.
"""
from __future__ import annotations
from datetime import datetime


def _clamp(n, lo=0, hi=100):
    try:
        return max(lo, min(hi, int(round(float(n)))))
    except Exception:
        return lo


def _pulse_for(status: str, momentum: int) -> str:
    s = (status or '').upper()
    if 'HOT' in s or momentum >= 76:
        return 'hot-pulse'
    if 'WATCH' in s or momentum >= 56:
        return 'watch-pulse'
    if 'LOW' in s:
        return 'data-pulse'
    return 'soft-pulse'


def _tone_for(status: str, momentum: int) -> str:
    s = (status or '').upper()
    if 'HOT' in s or momentum >= 76:
        return 'HOT'
    if 'WATCH' in s or momentum >= 56:
        return 'WATCH'
    if 'VALUE' in s:
        return 'VALUE'
    if 'LOW' in s:
        return 'LOW DATA'
    return 'CALM'


def build_live_visual_system_v318(v317_payload: dict | None) -> dict:
    base = v317_payload or {}
    summary = dict(base.get('summary') or {})
    matches = list(base.get('top_matches') or [])
    modules = list(base.get('modules') or [])
    journey = list(base.get('journey') or [])

    visual_matches = []
    hot_count = 0
    watch_count = 0
    energy_sum = 0
    for idx, m in enumerate(matches[:12], 1):
        momentum = _clamp(m.get('momentum') or m.get('score') or 0)
        badge = m.get('badge') or m.get('status') or ('HOT' if momentum >= 76 else 'WATCH' if momentum >= 56 else 'CALM')
        tone = _tone_for(badge, momentum)
        if tone == 'HOT': hot_count += 1
        if tone == 'WATCH': watch_count += 1
        energy = _clamp(momentum + (12 if tone == 'HOT' else 6 if tone == 'WATCH' else 0))
        energy_sum += energy
        visual_matches.append({
            'rank': m.get('rank') or idx,
            'title': m.get('title') or m.get('match') or 'Partido en seguimiento',
            'league': m.get('league') or 'Competición',
            'action': m.get('action') or 'Revisar contexto y esperar señal clara.',
            'momentum': momentum,
            'energy': energy,
            'tone': tone,
            'pulse': _pulse_for(tone, momentum),
            'glow': 'glow-hot' if tone == 'HOT' else 'glow-watch' if tone == 'WATCH' else 'glow-soft',
            'microcopy': 'Movimiento fuerte ahora' if tone == 'HOT' else 'Vigilar evolución' if tone == 'WATCH' else 'Lectura tranquila',
        })

    visual_modules = []
    for mod in modules:
        score = _clamp(mod.get('score') or 0)
        status = mod.get('status') or ('HOT' if score >= 75 else 'WATCH' if score >= 50 else 'READY')
        visual_modules.append({**mod, 'score': score, 'tone': _tone_for(status, score), 'pulse': _pulse_for(status, score)})

    avg_energy = _clamp(energy_sum / max(1, len(visual_matches))) if visual_matches else _clamp(summary.get('avg_momentum') or 0)
    activity = 'ALTA' if avg_energy >= 72 or hot_count else 'MEDIA' if avg_energy >= 45 or watch_count else 'TRANQUILA'

    return {
        'ok': True,
        'version': 'V318',
        'mode': 'cache-first-live-visual-system',
        'touches_api': False,
        'generated_at': datetime.utcnow().isoformat(timespec='seconds') + 'Z',
        'headline': 'Live Visual System activo: la app se siente más viva, clara y premium.',
        'mood': 'LIVE FEEL ' + activity,
        'activity': activity,
        'visual_summary': {
            'hot': hot_count or summary.get('hot', 0),
            'watch': watch_count or summary.get('watch', 0),
            'energy': avg_energy,
            'motion': 'premium',
            'api_cost': 0,
        },
        'summary': summary,
        'modules': visual_modules,
        'journey': journey,
        'visual_matches': visual_matches,
        'microinteractions': [
            {'name': 'Pulso HOT', 'text': 'Señales importantes destacan con glow y respiración visual.', 'level': 'premium'},
            {'name': 'Momentum bar', 'text': 'Cada partido muestra energía visual sin saturar al cliente.', 'level': 'premium'},
            {'name': 'Estado vivo', 'text': 'La pantalla comunica actividad aunque no haya nuevas APIs.', 'level': 'safe'},
            {'name': 'Transición suave', 'text': 'Cards, botones y bloques tienen movimiento controlado.', 'level': 'ux'},
        ],
        'next_actions': base.get('next_actions') or ['Abrir partidos de hoy', 'Revisar Live Focus', 'Volver a mi cuenta'],
        'client_navigation': [
            {'label': 'Mi app', 'href': '/cliente/experiencia'},
            {'label': 'Live Visual', 'href': '/cliente/live-visual'},
            {'label': 'Live Focus', 'href': '/cliente/smart-live-hub'},
            {'label': 'Match Center', 'href': '/cliente/match-center-premium'},
            {'label': 'Mi cuenta', 'href': '/cliente/dashboard'},
        ],
        'empty_state': {'title': 'Sin señales live cacheadas', 'text': 'La pantalla mantiene experiencia premium y no consume API al abrir.'},
    }
