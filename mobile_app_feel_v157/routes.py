from flask import Blueprint, jsonify, render_template
from datetime import datetime

mobile_app_feel_v157_bp = Blueprint('mobile_app_feel_v157_bp', __name__)


def _safe_live_pulse():
    try:
        from live_visual_v154.routes import build_live_pulse
        return build_live_pulse()
    except Exception as exc:
        return {'ok': False, 'message': 'Live pulse no disponible', 'error': str(exc), 'items': []}


@mobile_app_feel_v157_bp.route('/api/v157/app-feel')
def api_v157_app_feel():
    pulse = _safe_live_pulse()
    items = pulse.get('items') or pulse.get('matches') or []
    live_count = 0
    try:
        live_count = int(pulse.get('live_count') or pulse.get('counts', {}).get('live') or 0)
    except Exception:
        live_count = 0
    return jsonify({
        'ok': True,
        'version': 'V157_MOBILE_APP_FEEL_AND_LIVE_POLISH_PRO',
        'real_only': True,
        'no_fake_policy': True,
        'live_count': live_count,
        'signal_count': len(items),
        'pwa': 'ready',
        'mobile_feel': {
            'bottom_nav': True,
            'smooth_transitions': True,
            'skeleton_loading': True,
            'live_ticker': True,
            'compact_cards': True,
        },
        'now': datetime.utcnow().isoformat() + 'Z',
    })


@mobile_app_feel_v157_bp.route('/cliente/app')
@mobile_app_feel_v157_bp.route('/app-pro')
def page_v157_app_feel():
    return render_template('mobile_app_feel_v157.html')
