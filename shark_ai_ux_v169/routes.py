from flask import Blueprint, jsonify, request
from datetime import datetime

shark_ai_ux_v169_bp = Blueprint('shark_ai_ux_v169_bp', __name__)


def _session_level():
    try:
        from flask import session
        return (session.get('membership') or session.get('plan') or 'FREE').upper()
    except Exception:
        return 'FREE'


@shark_ai_ux_v169_bp.route('/api/v169/shark-ai-ui-state')
def api_v169_shark_ai_ui_state():
    return jsonify({
        'ok': True,
        'version': 'V169_SHARK_AI_DOCK_AND_MATCH_CLEANUP',
        'mode': request.args.get('mode') or 'dock',
        'membership': _session_level(),
        'controls': {
            'can_close': True,
            'can_minimize': True,
            'can_move': True,
            'can_restore': True,
            'safe_area_mobile': True,
            'auto_collapse_on_scroll': True,
        },
        'client_only_copy': True,
        'admin_debug_hidden': True,
        'real_only': True,
        'no_fake_policy': True,
        'updated_at': datetime.utcnow().isoformat() + 'Z',
    })


@shark_ai_ux_v169_bp.route('/api/v169/match-client-flow')
def api_v169_match_client_flow():
    return jsonify({
        'ok': True,
        'version': 'V169_SHARK_AI_DOCK_AND_MATCH_CLEANUP',
        'goal': 'Navegación sencilla para cliente dentro del partido',
        'sections': [
            {'key': 'summary', 'label': 'Resumen', 'visible_to_client': True},
            {'key': 'shark', 'label': 'Lectura SHARK', 'visible_to_client': True},
            {'key': 'timeline', 'label': 'Timeline', 'visible_to_client': True},
            {'key': 'stats', 'label': 'Stats', 'visible_to_client': True},
            {'key': 'picks', 'label': 'Picks', 'visible_to_client': True},
        ],
        'hidden_for_client': ['debug', 'admin', 'raw_api', 'internal_routes'],
        'real_only': True,
    })
