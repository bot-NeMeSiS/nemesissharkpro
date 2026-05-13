from flask import Blueprint, jsonify, render_template, request
from datetime import datetime

bp_shark_ai_copilot_v208 = Blueprint('shark_ai_copilot_v208', __name__)


def _safe_live_context():
    context = {'radar': [], 'live': [], 'odds': []}
    try:
        from premium_match_radar_v207.routes import premium_match_radar_payload
        context['radar'] = (premium_match_radar_payload().get('cards') or [])[:6]
    except Exception:
        pass
    try:
        from live_command_v204.routes import live_command_payload
        context['live'] = (live_command_payload().get('cards') or [])[:6]
    except Exception:
        pass
    try:
        from odds_movement_v206.routes import odds_movement_payload
        context['odds'] = (odds_movement_payload().get('movimientos') or [])[:6]
    except Exception:
        pass
    return context


def copilot_answer(question=''):
    q = (question or '').strip().lower()
    ctx = _safe_live_context()
    hot = ctx['radar'][:3] or ctx['live'][:3]
    if not hot:
        return {
            'respuesta': 'Ahora mismo no tengo suficientes datos reales cargados para recomendar partidos. Sin datos reales, no invento análisis.',
            'motivos': ['No hay radar/live suficiente en caché', 'Puedes sincronizar fixtures o revisar proveedor'],
            'contexto': ctx,
        }
    lines = []
    for m in hot:
        partido = m.get('partido') or f"{m.get('local','Local')} vs {m.get('visitante','Visitante')}"
        estado = m.get('estado') or m.get('nivel') or 'Seguimiento'
        marcador = m.get('marcador') or 'sin marcador'
        lines.append(f"{partido}: {estado}, marcador {marcador}.")
    return {
        'respuesta': 'Veo estos focos reales ahora mismo: ' + ' '.join(lines),
        'motivos': ['Usa radar/live/cuotas reales disponibles', 'No crea partidos ni resultados inventados'],
        'contexto': ctx,
    }


@bp_shark_ai_copilot_v208.route('/api/v208/shark-copilot', methods=['GET','POST'])
def api_shark_copilot_v208():
    question = ''
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        question = data.get('question') or data.get('mensaje') or ''
    else:
        question = request.args.get('q') or ''
    payload = copilot_answer(question)
    payload['version'] = 'V208_SHARK_AI_COPILOT_REAL_PRO'
    payload['generado'] = datetime.utcnow().isoformat() + 'Z'
    return jsonify(payload)


@bp_shark_ai_copilot_v208.route('/cliente/shark-copilot')
@bp_shark_ai_copilot_v208.route('/cliente/ai-live')
@bp_shark_ai_copilot_v208.route('/shark-copilot-real')
def page_shark_copilot_v208():
    return render_template('shark_ai_copilot_v208.html', data=copilot_answer('resumen'))


@bp_shark_ai_copilot_v208.route('/admin/shark-copilot')
def admin_shark_copilot_v208():
    return render_template('shark_ai_copilot_v208.html', data=copilot_answer('admin'), admin=True)
