
from datetime import datetime, timezone


def build_match_center_premium_v314(v313_payload):
    """Match Center Premium sobre V313.
    Convierte señales cacheadas en una experiencia por partido: decisión, momentum,
    timeline, recap, data health y próximos pasos. No llama APIs externas.
    """
    matches = list((v313_payload or {}).get('match_center') or [])
    summary = dict((v313_payload or {}).get('summary') or {})
    centers = [_center(m, idx) for idx, m in enumerate(matches[:10], start=1)]
    return {
        'ok': True,
        'version': 'V314',
        'mode': 'premium-match-center-cache-first',
        'touches_api': False,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'headline': _headline(centers, summary),
        'summary': {
            'total_centers': len(centers),
            'hot': len([c for c in centers if c['signal'] == 'HOT']),
            'value': len([c for c in centers if c['signal'] == 'VALUE']),
            'watch': len([c for c in centers if c['signal'] in ('WATCH','TIMING')]),
            'low_data': len([c for c in centers if c['data_health']['level'] == 'LOW DATA']),
            'momentum_avg': int(round(sum(c['momentum'] for c in centers) / max(1, len(centers)))) if centers else int(summary.get('momentum_avg') or 0),
        },
        'centers': centers,
        'empty_state': _empty_state() if not centers else None,
        'client_loop': _client_loop(centers),
        'source_version': (v313_payload or {}).get('version', 'V313'),
    }


def _headline(centers, summary):
    if not centers:
        return 'Match Center Premium preparado: esperando datos reales cacheados.'
    hot = [c for c in centers if c['signal'] == 'HOT']
    if hot:
        return f'{len(hot)} partido(s) requieren atención inmediata en Match Center.'
    value = [c for c in centers if c['signal'] == 'VALUE']
    if value:
        return f'{len(value)} partido(s) con zona VALUE para revisar con calma.'
    return 'Match Center Premium activo: seguimiento claro, visual y responsable.'


def _center(m, idx):
    momentum = int(m.get('momentum') or 0)
    signal = m.get('trigger') or 'WATCH'
    health = m.get('health') or 'WATCH'
    return {
        'rank': idx,
        'id': m.get('id'),
        'title': m.get('title') or 'Partido',
        'league': m.get('league') or 'Liga',
        'status': m.get('status') or 'PROGRAMADO',
        'minute': m.get('minute') or '',
        'scoreline': m.get('scoreline') or '',
        'pick': m.get('pick') or 'Sin pick confirmado',
        'odds': m.get('odds') or '',
        'signal': signal,
        'momentum': momentum,
        'decision': _decision(signal, health, momentum),
        'decision_label': _decision_label(signal, health, momentum),
        'why': m.get('why') or 'Señal generada por el motor live.',
        'action': m.get('action') or 'Guardar en seguimiento.',
        'timeline': _timeline(m, signal, momentum, health),
        'recap': _recap(signal, momentum, health),
        'data_health': _data_health(health, m),
        'value_box': _value_box(m, signal, momentum),
        'next_steps': _next_steps(signal, health),
    }


def _decision(signal, health, momentum):
    if health == 'LOW DATA':
        return 'WAIT'
    if signal == 'HOT' and momentum >= 78:
        return 'FOCUS_NOW'
    if signal == 'VALUE':
        return 'REVIEW_VALUE'
    if signal == 'TIMING':
        return 'WATCH_TIMING'
    return 'OBSERVE'


def _decision_label(signal, health, momentum):
    return {
        'WAIT': 'Esperar más datos',
        'FOCUS_NOW': 'Mirar ahora',
        'REVIEW_VALUE': 'Revisar valor',
        'WATCH_TIMING': 'Minuto sensible',
        'OBSERVE': 'Observar',
    }[_decision(signal, health, momentum)]


def _timeline(m, signal, momentum, health):
    title = m.get('title') or 'Partido'
    events = [
        {'phase': 'Contexto', 'text': f'{title} entra en seguimiento premium.'},
        {'phase': 'Señal', 'text': f'Momentum {momentum}/99 · estado {signal}.'},
    ]
    if m.get('scoreline') or m.get('minute'):
        events.append({'phase': 'Live', 'text': f"Marcador {m.get('scoreline') or 'pendiente'} · minuto {m.get('minute') or 'sin minuto'}."})
    if health == 'LOW DATA':
        events.append({'phase': 'Data Health', 'text': 'Datos incompletos: el sistema evita recomendar de más.'})
    else:
        events.append({'phase': 'Decisión', 'text': m.get('action') or 'Seguir evolución antes de actuar.'})
    return events


def _recap(signal, momentum, health):
    if health == 'LOW DATA':
        return 'No hay suficiente señal para una lectura agresiva. Mejor esperar y proteger al cliente.'
    if signal == 'HOT':
        return 'Partido con pulso alto. Conviene abrirlo, revisar cuota y controlar el timing.'
    if signal == 'VALUE':
        return 'Hay indicios de valor. Revisar pick, cuota y stake antes de decidir.'
    if signal == 'TIMING':
        return 'Momento temporal delicado. Ideal para seguimiento live, no para entrar a ciegas.'
    return 'Partido estable para seguimiento. No exige acción inmediata.'


def _data_health(health, m):
    missing = []
    if not m.get('scoreline'): missing.append('marcador')
    if not m.get('minute'): missing.append('minuto')
    if not m.get('pick') or m.get('pick') == 'Sin pick confirmado': missing.append('pick')
    if not m.get('odds'): missing.append('cuota')
    return {
        'level': health,
        'text': 'Datos suficientes' if health != 'LOW DATA' else 'Faltan datos clave',
        'missing': missing[:4],
    }


def _value_box(m, signal, momentum):
    odds = m.get('odds') or '—'
    pick = m.get('pick') or 'Sin pick confirmado'
    if signal == 'VALUE':
        tone = 'Posible oportunidad si cuota y contexto acompañan.'
    elif signal == 'HOT':
        tone = 'Primero confirmar live/marcador; después valorar entrada.'
    else:
        tone = 'Seguimiento sin presión: no forzar apuesta.'
    return {'pick': pick, 'odds': odds, 'tone': tone, 'confidence': f'{min(99, max(1, momentum))}/99'}


def _next_steps(signal, health):
    if health == 'LOW DATA':
        return ['Esperar actualización real', 'No recomendar entrada', 'Mantener en observación']
    if signal == 'HOT':
        return ['Abrir partido', 'Revisar cuota y marcador', 'Confirmar stake responsable']
    if signal == 'VALUE':
        return ['Comparar cuota', 'Leer motivo SHARK', 'Decidir sin prisa']
    if signal == 'TIMING':
        return ['Vigilar minuto', 'Esperar evento clave', 'Evitar entrada impulsiva']
    return ['Guardar seguimiento', 'Volver al hub live', 'Esperar mejor señal']


def _client_loop(centers):
    if not centers:
        return ['Smart Home', 'Cargar datos reales', 'Live Engine', 'Match Center']
    first = centers[0]
    return ['Smart Home', f"Foco: {first['title']}", first['decision_label'], 'Recap y siguiente acción']


def _empty_state():
    return {
        'title': 'Sin partidos cacheados ahora mismo',
        'text': 'La pantalla está lista para datos reales sin gastar API desde este punto.',
        'action': 'Carga partidos desde las pantallas reales y vuelve al Match Center.',
    }
