
"""
Rutas V73 Observability.
"""

from flask import Blueprint, jsonify, render_template
from .observability_engine import get_observability_status, create_performance_snapshot

observability_v73_bp = Blueprint("observability_v73", __name__)


@observability_v73_bp.route("/admin/observability")
def admin_observability():
    return render_template("admin_observability_v73.html", status=get_observability_status())


@observability_v73_bp.route("/api/observability-status")
def api_observability_status():
    return jsonify(get_observability_status())


@observability_v73_bp.route("/api/observability/snapshot", methods=["POST", "GET"])
def api_observability_snapshot():
    return jsonify(create_performance_snapshot())
