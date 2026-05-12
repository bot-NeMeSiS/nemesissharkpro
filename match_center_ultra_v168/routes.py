from flask import Blueprint, jsonify, render_template, request
from datetime import datetime

match_center_ultra_v168_bp = Blueprint('match_center_ultra_v168_bp', __name__)


def _base_match_center(match_id=None):
    try:
        from match_center_v155.routes import build_match_center
        return build_match_center(match_id)
    except Exception as exc:
        return {
            'ok': False,
            'version': 'V168_MATCH_CENTER_ULTRA_PRO',
            'message': 'Match Center base no disponible todavía. Estado vacío premium sin datos inventados.',
            'error': str(exc),
            'events': [], 'stats': [], 'v158_signals': [], 'related_picks': [],
            'now': datetime.utcnow().isoformat() + 'Z'
        }


def _safe_text(value, fallback='Pendiente'):
    value = '' if value is None else str(value).strip()
    return value or fallback


def _ultra_actions(match_id):
    mid = _safe_text(match_id, 'selected')
    return [
        {'key': 'analyze', 'label': 'Analizar con SHARK', 'href': f'/api/v168/shark-live-analysis?match_id={mid}', 'tone': 'cyan'},
        {'key': 'favorite', 'label': 'Guardar favorito', 'href': f'/api/v168/match-actions?action=favorite&match_id={mid}', 'tone': 'gold'},
        {'key': 'alert', 'label': 'Crear alerta', 'href': f'/api/v168/match-actions?action=alert&match_id={mid}', 'tone': 'pink'},
        {'key': 'picks', 'label': 'Ver picks relacionados', 'href': '/picks', 'tone': 'green'},
    ]


def build_match_ultra(match_id=None):
    data = _base_match_center(match_id)
    data['version'] = 'V168_MATCH_CENTER_ULTRA_PRO'
    data['ultra'] = {
        'title': 'Match Center ULTRA PRO',
        'subtitle': 'Centro premium de partido con señales SHARK, timeline, momentum y acciones rápidas.',
        'real_only': True,
        'no_fake_policy': True,
        'actions': _ultra_actions(match_id or ((data.get('match') or {}).get('id') if data.get('match') else 'selected')),
        'badges': ['Real Core', 'SHARK AI', 'Favoritos', 'Alertas', 'No fake'],
    }
    match = data.get('match') or {}
    momentum = int(data.get('momentum') or 50)
    status = _safe_text(match.get('status'), 'Pendiente')
    risk = _safe_text(match.get('risk'), 'Pendiente')
    has_events = bool(data.get('events'))
    has_stats = bool(data.get('stats'))
    data['ultra']['insights'] = [
        {'label': 'Lectura partido', 'value': 'LIVE' if data.get('is_live') else 'Prepartido', 'tone': 'live' if data.get('is_live') else 'soft'},
        {'label': 'Momentum', 'value': f'{momentum}%', 'tone': 'good' if momentum >= 70 else ('warn' if momentum >= 50 else 'soft')},
        {'label': 'Riesgo', 'value': risk, 'tone': 'danger' if risk.lower() == 'alto' else ('warn' if risk.lower() == 'medio' else 'good')},
        {'label': 'Eventos', 'value': 'Cargados' if has_events else 'Pendientes', 'tone': 'good' if has_events else 'soft'},
        {'label': 'Stats', 'value': 'Cargadas' if has_stats else 'Pendientes', 'tone': 'good' if has_stats else 'soft'},
        {'label': 'Estado', 'value': status, 'tone': 'live' if data.get('is_live') else 'soft'},
    ]
    data['ultra']['market_signals'] = [
        {'market': _safe_text((data.get('shark_context') or {}).get('market'), 'Mercado pendiente'), 'signal': _safe_text((data.get('shark_context') or {}).get('value_label'), 'Pendiente'), 'risk': risk, 'stake': _safe_text(match.get('stake'), 'Pendiente')},
        {'market': 'Gestión de banca', 'signal': 'No sobreexponerse', 'risk': 'Control', 'stake': _safe_text(match.get('stake'), 'Pendiente')},
        {'market': 'Política de datos', 'signal': 'Sin inventar eventos', 'risk': 'Real only', 'stake': '—'},
    ]
    data['ultra']['empty_help'] = 'Si el proveedor todavía no entrega timeline o estadísticas, el Match Center muestra estado premium vacío y conserva la política no fake.'
    return data


@match_center_ultra_v168_bp.route('/api/v168/match-ultra')
def api_v168_match_ultra():
    match_id = request.args.get('match_id') or request.args.get('id')
    return jsonify(build_match_ultra(match_id))


@match_center_ultra_v168_bp.route('/api/v168/shark-live-analysis')
def api_v168_shark_live_analysis():
    match_id = request.args.get('match_id') or request.args.get('id')
    data = build_match_ultra(match_id)
    if not data.get('ok'):
        return jsonify({'ok': False, 'version': 'V168_MATCH_CENTER_ULTRA_PRO', 'message': data.get('message'), 'real_only': True})
    ctx = data.get('shark_context') or {}
    return jsonify({
        'ok': True,
        'version': 'V168_MATCH_CENTER_ULTRA_PRO',
        'match_id': (data.get('match') or {}).get('id'),
        'summary': (ctx.get('quick_answers') or {}).get('resumen') or data.get('reading'),
        'value': ctx.get('value_label'),
        'risk': ctx.get('risk'),
        'stake': ctx.get('stake'),
        'avoid': ctx.get('avoid') or [],
        'momentum': data.get('momentum'),
        'real_only': True,
        'no_fake_policy': True,
    })


@match_center_ultra_v168_bp.route('/api/v168/match-actions')
def api_v168_match_actions():
    match_id = request.args.get('match_id') or request.args.get('id') or 'selected'
    action = (request.args.get('action') or 'status').lower()
    labels = {
        'favorite': 'Favorito preparado',
        'alert': 'Alerta preparada',
        'analyze': 'Análisis SHARK preparado',
        'picks': 'Picks relacionados preparados',
        'status': 'Acciones rápidas disponibles',
    }
    return jsonify({
        'ok': True,
        'version': 'V168_MATCH_CENTER_ULTRA_PRO',
        'match_id': match_id,
        'action': action,
        'message': labels.get(action, 'Acción premium preparada'),
        'real_only': True,
        'note': 'Endpoint de acción preparado de forma segura; no inventa datos ni fuerza apuestas.',
    })


@match_center_ultra_v168_bp.route('/match-center-ultra')
@match_center_ultra_v168_bp.route('/cliente/match-center-ultra')
def page_match_center_ultra():
    match_id = request.args.get('match_id') or request.args.get('id')
    return render_template('match_center_ultra_v168.html', data=build_match_ultra(match_id))


@match_center_ultra_v168_bp.route('/partido-ultra/<match_id>')
@match_center_ultra_v168_bp.route('/cliente/partido-ultra/<match_id>')
def page_partido_ultra(match_id):
    return render_template('match_center_ultra_v168.html', data=build_match_ultra(match_id))
