
"""
Rutas V71 Security + Scale.
Registrar:
from security_v71.routes import security_v71_bp
app.register_blueprint(security_v71_bp)
"""

from flask import Blueprint, jsonify, render_template
from .hardening import get_security_scale_status

security_v71_bp = Blueprint("security_v71", __name__)


@security_v71_bp.route("/admin/security-scale")
def admin_security_scale():
    return render_template("admin_security_scale_v71.html", status=get_security_scale_status())


@security_v71_bp.route("/api/security-scale")
def api_security_scale():
    return jsonify(get_security_scale_status())
