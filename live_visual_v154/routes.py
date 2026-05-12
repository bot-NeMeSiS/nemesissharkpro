from flask import Blueprint, jsonify
from datetime import datetime

live_visual_v154_bp = Blueprint('live_visual_v154_bp', __name__)

@live_visual_v154_bp.route('/api/v154/live-pulse')
def live_pulse():
    return jsonify({
        'version': 'V154_LIVE_VISUAL_EXPERIENCE_PRO',
        'status': 'online',
        'live_badges': True,
        'match_center_upgrade_ready': True,
        'timestamp': datetime.utcnow().isoformat()
    })
