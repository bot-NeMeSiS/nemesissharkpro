# -*- coding: utf-8 -*-
"""
V316 · Client Continuity Intelligence Engine
Une SHARK Memory V315 con una experiencia cliente accionable:
- Continuar donde lo dejaste
- Tendencias del día
- Partidos vigilados
- Recomendaciones de acción
- Todo cache-first, sin llamadas externas
"""
from __future__ import annotations
from datetime import datetime


def _safe_num(v, default=0):
    try:
        if v is None or v == "": return default
        return float(v)
    except Exception:
        return default


def _badge_from_score(score):
    score = _safe_num(score, 0)
    if score >= 78: return "HOT"
    if score >= 62: return "WATCH"
    if score >= 45: return "SEGUIR"
    return "LOW DATA"


def _action_for_card(card):
    title = (card.get('title') or card.get('match') or 'Partido').strip()
    momentum = _safe_num(card.get('momentum') or card.get('momentum_score'), 0)
    ev = _safe_num(card.get('ev'), 0)
    health = (card.get('data_health') or card.get('health') or '').upper()
    if momentum >= 78 and ev > 0:
        return f"Revisar {title}: momentum alto y posible value."
    if momentum >= 62:
        return f"Mantener {title} en vigilancia activa."
    if 'LOW' in health:
        return f"Esperar más datos antes de decidir en {title}."
    return f"Guardar {title} como seguimiento suave."


def build_client_continuity_v316(memory_payload: dict | None) -> dict:
    memory_payload = memory_payload or {}
    cards = []
    for key in ('memory_cards','cards','recent_matches','matches'):
        val = memory_payload.get(key)
        if isinstance(val, list):
            cards = val
            break
    normalized=[]
    for idx, c in enumerate(cards[:10]):
        if not isinstance(c, dict): continue
        title = c.get('title') or c.get('match') or c.get('name') or f'Partido {idx+1}'
        momentum = _safe_num(c.get('momentum') or c.get('momentum_score') or c.get('score'), 0)
        ev = _safe_num(c.get('ev'), 0)
        badge = c.get('badge') or _badge_from_score(momentum)
        normalized.append({
            'id': c.get('id') or c.get('match_id') or idx+1,
            'title': title,
            'league': c.get('league') or c.get('competition') or 'Competición',
            'status': c.get('status') or c.get('live_status') or 'Seguimiento',
            'minute': c.get('minute') or c.get('live_minute') or '',
            'scoreline': c.get('scoreline') or c.get('live_score') or '',
            'momentum': round(momentum, 1),
            'ev': round(ev, 2),
            'badge': badge,
            'action': _action_for_card(c),
            'health': c.get('data_health') or c.get('health') or 'OK',
        })
    hot=[x for x in normalized if x['badge']=='HOT']
    watch=[x for x in normalized if x['badge'] in ('WATCH','SEGUIR')]
    low=[x for x in normalized if x['badge']=='LOW DATA' or 'LOW' in str(x.get('health','')).upper()]
    avg = round(sum(x['momentum'] for x in normalized)/len(normalized),1) if normalized else 0
    if hot:
        headline = 'Tu sesión live tiene partidos calientes para revisar ahora.'
        primary = hot[0]
    elif watch:
        headline = 'Tu sesión live está en modo vigilancia inteligente.'
        primary = watch[0]
    else:
        headline = 'No hay urgencia live: SHARK mantiene memoria y espera mejores señales.'
        primary = normalized[0] if normalized else None
    return {
        'ok': True,
        'version': 'V316',
        'touches_api': False,
        'generated_at': datetime.utcnow().isoformat(timespec='seconds')+'Z',
        'headline': headline,
        'session_resume': {
            'title': 'Continuar donde lo dejaste',
            'text': primary['action'] if primary else 'Cuando haya partidos cacheados, aparecerán aquí tus mejores continuaciones.',
            'primary_match': primary,
        },
        'summary': {
            'tracked': len(normalized),
            'hot': len(hot),
            'watch': len(watch),
            'low_data': len(low),
            'avg_momentum': avg,
            'continuity_health': 'ALTA' if normalized else 'ESPERANDO DATOS',
        },
        'daily_trends': [
            {'label':'Momentum medio', 'value': avg, 'hint':'Pulso general de la sesión'},
            {'label':'HOT ahora', 'value': len(hot), 'hint':'Partidos con señales fuertes'},
            {'label':'En vigilancia', 'value': len(watch), 'hint':'Partidos para seguir sin forzar apuesta'},
            {'label':'Baja información', 'value': len(low), 'hint':'Evitar decisiones precipitadas'},
        ],
        'watchlist': normalized,
        'recommended_actions': [x['action'] for x in (hot or watch or normalized)[:5]] or [
            'Abrir partidos de hoy para alimentar el ecosistema.',
            'Revisar Match Center Premium cuando existan datos cacheados.',
            'Mantener SHARK Memory activo para acumular contexto.'
        ],
        'client_path': ['Smart Home', 'Live Hub', 'Match Center', 'SHARK Memory', 'Continuity Center'],
        'empty_state': {
            'title':'Continuity Center preparado',
            'text':'No llama a APIs externas. Usa lo que ya hay cacheado/guardado para construir continuidad real.'
        }
    }
