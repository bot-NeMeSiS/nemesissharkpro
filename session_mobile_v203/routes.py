from flask import Blueprint, jsonify, render_template, session
from datetime import datetime

bp_session_mobile_v203 = Blueprint('session_mobile_v203', __name__)


def _user():
    u = session.get('user') if session else None
    return u if isinstance(u, dict) else {}


def current_identity():
    u = _user()
    username = str(u.get('username') or u.get('name') or '').strip()
    if not username:
        username = 'Cliente'
    plan = str(u.get('plan') or u.get('membership') or 'FREE').upper()
    if plan not in ('FREE', 'PRO', 'ELITE', 'ADMIN'):
        plan = 'FREE'
    return {
        'version': 'V203_SESSION_FIX_MOBILE_UX_REBUILD_PRO',
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'usuario': username,
        'membresia': plan,
        'rol': str(u.get('role') or 'cliente'),
        'sesion_limpia': bool(u.get('id') or username != 'Cliente'),
        'nota': 'Identidad tomada de la sesión actual. Sin nombres hardcodeados.',
    }


@bp_session_mobile_v203.route('/api/v203/session/identity')
def api_v203_identity():
    return jsonify(current_identity())


@bp_session_mobile_v203.route('/cliente/setup-pendiente')
def client_setup_pending_v203():
    return render_template('setup_pending_v203.html', identity=current_identity())


@bp_session_mobile_v203.route('/admin/setup-pendiente')
def admin_setup_pending_v203():
    return render_template('setup_pending_v203.html', identity=current_identity(), admin=True)
