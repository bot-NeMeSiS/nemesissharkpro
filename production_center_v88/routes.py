
from flask import Blueprint, jsonify, render_template
from .production_engine import get_production_status, health_payload

production_center_v88_bp = Blueprint("production_center_v88", __name__)

@production_center_v88_bp.route("/admin/production-center")
def admin_production_center():
    return render_template("admin_production_center_v88.html", status=get_production_status())

@production_center_v88_bp.route("/api/production-center/status")
def api_production_center_status():
    return jsonify(get_production_status())

@production_center_v88_bp.route("/health")
def health():
    return jsonify(health_payload())
