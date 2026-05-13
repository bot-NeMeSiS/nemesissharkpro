
from flask import Blueprint, jsonify, render_template

from pro_architecture_v110.core.system_diagnostics import build_diagnostics

pro_architecture_v110_bp = Blueprint("pro_architecture_v110", __name__)

@pro_architecture_v110_bp.route("/api/v110/architecture/status")
def architecture_status():
    return jsonify(build_diagnostics())

@pro_architecture_v110_bp.route("/admin/architecture")
@pro_architecture_v110_bp.route("/admin/diagnostics")
def architecture_page():
    status = build_diagnostics()
    return render_template("architecture_v110.html", status=status)
