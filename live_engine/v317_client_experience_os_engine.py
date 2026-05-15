
# -*- coding: utf-8 -*-
"""
V317 · Client Experience OS Engine
Une Smart Home + Live Hub + Match Center + SHARK Memory + Continuity en una experiencia guiada.
Cache-first: no llama a APIs externas.
"""
from __future__ import annotations
from datetime import datetime


def _num(v, default=0):
    try:
        if v is None: return default
        return int(float(v))
    except Exception:
        return default


def _safe_list(v):
    return v if isinstance(v, list) else []


def build_client_experience_os_v317(v316_payload: dict) -> dict:
    v316_payload = v316_payload or {}
    summary = v316_payload.get('summary') or {}
    watchlist = _safe_list(v316_payload.get('watchlist'))
    actions = _safe_list(v316_payload.get('recommended_actions'))
    tracked = _num(summary.get('tracked'))
    hot = _num(summary.get('hot'))
    watch = _num(summary.get('watch'))
    low = _num(summary.get('low_data'))
    momentum = _num(summary.get('avg_momentum'))

    if hot > 0:
        mood = 'LIVE URGENTE'
        headline = 'Hay señales calientes: entra directo al Live Focus y decide con calma.'
        primary_cta = {'label': 'Abrir foco live', 'href': '/cliente/smart-live-hub', 'kind': 'hot'}
    elif tracked > 0:
        mood = 'SEGUIMIENTO ACTIVO'
        headline = 'Tu sesión tiene continuidad: partidos vigilados, memoria y próximos pasos claros.'
        primary_cta = {'label': 'Continuar seguimiento', 'href': '/cliente/continuity-center', 'kind': 'watch'}
    else:
        mood = 'MODO EXPLORACIÓN'
        headline = 'Empieza por partidos de hoy y deja que SHARK organice el camino.'
        primary_cta = {'label': 'Ver partidos de hoy', 'href': '/cliente/partidos', 'kind': 'start'}

    modules = [
        {
            'title': 'Mi día deportivo',
            'subtitle': 'Resumen inicial con lo importante nada más entrar.',
            'href': '/cliente/continuity-center',
            'status': 'Activo' if tracked else 'Preparado',
            'score': max(momentum, 35 if tracked else 20),
            'why': 'Evita que el cliente tenga que buscar desde cero cada vez.'
        },
        {
            'title': 'Live Focus',
            'subtitle': 'Señales HOT/WATCH/LOW DATA con acción recomendada.',
            'href': '/cliente/smart-live-hub',
            'status': 'HOT' if hot else ('WATCH' if watch else 'Seguro'),
            'score': min(100, momentum + hot*12 + watch*4),
            'why': 'Convierte la pantalla live en algo entendible y emocionante.'
        },
        {
            'title': 'Match Center',
            'subtitle': 'Cada partido como mini ecosistema: estado, decisión, timeline y recap.',
            'href': '/cliente/match-center-premium',
            'status': 'Premium',
            'score': 82 if tracked else 65,
            'why': 'Da sensación Sofascore/Flashscore propia dentro de NeMeSiS.'
        },
        {
            'title': 'Memoria SHARK',
            'subtitle': 'Snapshots y continuidad para futuras tendencias y ML.',
            'href': '/cliente/shark-memory',
            'status': 'ML Ready',
            'score': 76 if tracked else 55,
            'why': 'Hace que la app no olvide y prepara inteligencia real.'
        },
    ]

    journey = [
        {'step': 'Entrada', 'title': 'Resumen claro', 'text': 'El cliente ve qué importa ahora, sin navegar perdido.'},
        {'step': 'Foco', 'title': 'Prioridad live', 'text': 'La app separa HOT, WATCH y LOW DATA.'},
        {'step': 'Decisión', 'title': 'Match Center', 'text': 'Cada partido explica estado, valor, riesgo y siguiente acción.'},
        {'step': 'Memoria', 'title': 'Continuidad', 'text': 'SHARK recuerda señales, snapshots y seguimiento.'},
        {'step': 'Vuelta', 'title': 'Daily Loop', 'text': 'El cliente vuelve y continúa donde lo dejó.'},
    ]

    top_matches = []
    for i, m in enumerate(watchlist[:5], start=1):
        top_matches.append({
            'rank': i,
            'title': m.get('title') or 'Partido en seguimiento',
            'league': m.get('league') or 'Competición',
            'badge': m.get('badge') or ('HOT' if i == 1 and hot else 'WATCH'),
            'momentum': _num(m.get('momentum')),
            'action': m.get('action') or 'Revisar contexto antes de decidir.',
            'href': '/cliente/match-center-premium'
        })

    if not actions:
        actions = ['Ver partidos de hoy', 'Abrir Live Focus', 'Revisar Match Center Premium']

    return {
        'ok': True,
        'version': 'V317',
        'touches_api': False,
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'mood': mood,
        'headline': headline,
        'primary_cta': primary_cta,
        'summary': {
            'tracked': tracked,
            'hot': hot,
            'watch': watch,
            'low_data': low,
            'avg_momentum': momentum,
            'experience_health': 'PREMIUM' if tracked or hot else 'READY'
        },
        'modules': modules,
        'journey': journey,
        'top_matches': top_matches,
        'next_actions': actions[:6],
        'client_navigation': [
            {'label': 'Mi día', 'href': '/cliente/experiencia'},
            {'label': 'Live Focus', 'href': '/cliente/smart-live-hub'},
            {'label': 'Match Center', 'href': '/cliente/match-center-premium'},
            {'label': 'Memoria', 'href': '/cliente/shark-memory'},
            {'label': 'Mi cuenta', 'href': '/cliente/dashboard'},
        ],
        'empty_state': {
            'title': 'Experiencia cliente preparada',
            'text': 'Cuando haya partidos cacheados, esta pantalla se convierte en el centro inteligente de uso diario.'
        }
    }
