from flask import Blueprint, jsonify, render_template, request
from datetime import datetime

match_center_v155_bp = Blueprint('match_center_v155_bp', __name__)


def _team_initials(name):
    parts = [p for p in str(name or '').replace('-', ' ').split() if p]
    if not parts:
        return 'NS'
    if len(parts) == 1:
        return parts[0][:2].upper()
    return ''.join(p[0] for p in parts[:2]).upper()


def _find_real_core_match(match_id=None):
    try:
        from core.real_core_engine import RealCoreEngine
        if match_id:
            match, feed = RealCoreEngine.find(match_id, force=False)
            return match, feed
        feed = RealCoreEngine.fetch(force=False)
        matches = feed.get('matches') or []
        return (matches[0] if matches else None), feed
    except Exception as exc:
        return None, {'ok': False, 'matches': [], 'message': 'Real Core no disponible', 'error': str(exc)}


def _as_float(value, default=None):
    try:
        if value is None or value == '':
            return default
        return float(str(value).replace(',', '.'))
    except Exception:
        return default


def _normalize_risk(value):
    raw = str(value or '').strip().lower()
    if 'bajo' in raw or 'low' in raw:
        return 'Bajo'
    if 'alto' in raw or 'high' in raw:
        return 'Alto'
    if 'medio' in raw or 'medium' in raw:
        return 'Medio'
    return value or 'Pendiente'


def build_shark_context(match):
    """V156: lectura contextual derivada solo de datos reales ya presentes."""
    status = str(match.get('status') or '').upper()
    is_live = any(token in status for token in ['DIRECTO', 'LIVE', 'IN PLAY', 'EN JUEGO'])
    odds = _as_float(match.get('odds'), None)
    score = _as_float(match.get('shark_score') or match.get('quality_score'), None)
    risk = _normalize_risk(match.get('risk'))
    stake = match.get('stake') or 'Pendiente'
    market = match.get('market') or match.get('pick') or 'Mercado pendiente'

    confidence = 50 if score is None else max(0, min(100, int(score)))
    if odds is None:
        value_label = 'Pendiente'
        value_detail = 'No hay cuota real suficiente para valorar entrada. Mejor esperar actualización del feed.'
    elif confidence >= 80 and risk in ['Bajo', 'Medio']:
        value_label = 'Valor potencial'
        value_detail = 'La señal tiene buena calidad SHARK y riesgo controlado. Aun así, confirma alineaciones/estado antes de apostar.'
    elif confidence >= 65:
        value_label = 'Revisar con calma'
        value_detail = 'Hay datos suficientes para estudiar el mercado, pero no es entrada automática.'
    else:
        value_label = 'No forzar'
        value_detail = 'La lectura SHARK no recomienda forzar entrada con los datos actuales.'

    if risk == 'Alto':
        caution = 'Riesgo alto: reducir stake o evitar si no hay confirmación adicional.'
    elif risk == 'Bajo':
        caution = 'Riesgo bajo: mantener disciplina de banca y no aumentar stake por impulso.'
    elif risk == 'Medio':
        caution = 'Riesgo medio: entrada solo si la cuota y el contexto siguen siendo favorables.'
    else:
        caution = 'Riesgo pendiente: esperar más datos reales antes de decidir.'

    if is_live:
        live_note = 'Partido en directo/cerca del directo: SHARK prioriza prudencia y lectura por eventos reales.'
    else:
        live_note = 'Prepartido: revisar cuota, hora, mercado y posibles cambios antes del inicio.'

    avoid = []
    if odds is None:
        avoid.append('No entrar sin cuota real cargada.')
    if risk == 'Alto':
        avoid.append('No usar stake alto en señales de riesgo alto.')
    if confidence < 70:
        avoid.append('No convertir una señal débil en apuesta principal.')
    if not avoid:
        avoid.append('No sobreexponerse aunque la señal tenga buena pinta.')

    return {
        'value_label': value_label,
        'value_detail': value_detail,
        'confidence': confidence,
        'risk': risk,
        'stake': stake,
        'market': market,
        'caution': caution,
        'live_note': live_note,
        'avoid': avoid,
        'quick_answers': {
            'valor': value_detail,
            'stake': f'Stake recomendado: {stake}. Mantener gestión de banca y evitar subirlo manualmente.',
            'riesgo': caution,
            'evitar': ' '.join(avoid),
            'resumen': f'{value_label}. {live_note} Mercado: {market}. Riesgo: {risk}.'
        }
    }


def build_match_center(match_id=None):
    match, feed = _find_real_core_match(match_id)
    if not match:
        return {
            'ok': False,
            'version': 'V156_SHARK_CONTEXTUAL_MATCH_AI_PRO',
            'message': 'No hay partido real seleccionado. Se mantiene pantalla vacía premium sin inventar datos.',
            'feed_ok': bool(feed.get('ok')) if isinstance(feed, dict) else False,
            'events': [],
            'stats': [],
            'related_picks': [],
            'shark_context': None,
            'now': datetime.utcnow().isoformat() + 'Z',
        }

    status = str(match.get('status') or '').upper()
    is_live = 'DIRECTO' in status or 'LIVE' in status or 'IN PLAY' in status or 'EN JUEGO' in status
    score_label = match.get('score') or ('LIVE' if is_live else 'VS')
    shark_score = match.get('shark_score') or match.get('quality_score') or '—'
    risk = _normalize_risk(match.get('risk'))
    stake = match.get('stake') or 'Pendiente'
    odds = match.get('odds') or None

    momentum = 50
    try:
        momentum = max(0, min(100, int(float(shark_score))))
    except Exception:
        momentum = 50

    context = build_shark_context(match)

    reading = 'Partido real validado por Real Core. No hay timeline ni estadísticas live cargadas todavía.'
    if is_live:
        reading = 'Partido en directo o cerca del directo. SHARK prioriza lectura prudente hasta recibir eventos reales.'
    elif odds:
        reading = 'Mercado real disponible. Revisa cuota, riesgo y stake antes de entrar; sin inventar marcador ni eventos.'

    return {
        'ok': True,
        'version': 'V156_SHARK_CONTEXTUAL_MATCH_AI_PRO',
        'match': match,
        'home_initials': _team_initials(match.get('home_team')),
        'away_initials': _team_initials(match.get('away_team')),
        'score_label': score_label,
        'is_live': is_live,
        'momentum': momentum,
        'reading': reading,
        'events': [],
        'stats': [],
        'shark_context': context,
        'related_picks': [{
            'market': context['market'],
            'odds': odds or 'Pendiente',
            'risk': risk,
            'stake': stake,
            'score': shark_score,
        }],
        'feed_counts': (feed or {}).get('counts', {}),
        'now': datetime.utcnow().isoformat() + 'Z',
    }


@match_center_v155_bp.route('/api/v155/match-center-pro')
@match_center_v155_bp.route('/api/v156/match-center-pro')
def api_match_center_pro():
    match_id = request.args.get('match_id') or request.args.get('id')
    return jsonify(build_match_center(match_id))


@match_center_v155_bp.route('/api/v156/shark-context')
def api_shark_context():
    match_id = request.args.get('match_id') or request.args.get('id')
    data = build_match_center(match_id)
    if not data.get('ok'):
        return jsonify({'ok': False, 'version': 'V156_SHARK_CONTEXTUAL_MATCH_AI_PRO', 'message': data.get('message')})
    q = (request.args.get('q') or request.args.get('question') or 'resumen').strip().lower()
    ctx = data.get('shark_context') or {}
    answers = ctx.get('quick_answers') or {}
    key = 'resumen'
    for candidate in ['valor', 'stake', 'riesgo', 'evitar']:
        if candidate in q:
            key = candidate
            break
    return jsonify({
        'ok': True,
        'version': 'V156_SHARK_CONTEXTUAL_MATCH_AI_PRO',
        'match_id': (data.get('match') or {}).get('id'),
        'question': q,
        'answer': answers.get(key) or answers.get('resumen'),
        'context': ctx,
        'real_only': True,
        'no_fake_policy': True,
    })


@match_center_v155_bp.route('/match-center-pro')
@match_center_v155_bp.route('/cliente/match-center-pro')
def page_match_center_pro():
    match_id = request.args.get('match_id') or request.args.get('id')
    return render_template('match_center_pro_v155.html', data=build_match_center(match_id))


@match_center_v155_bp.route('/partido-pro/<match_id>')
@match_center_v155_bp.route('/cliente/partido-pro/<match_id>')
def page_partido_pro(match_id):
    return render_template('match_center_pro_v155.html', data=build_match_center(match_id))
