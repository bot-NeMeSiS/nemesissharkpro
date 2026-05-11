from flask import Blueprint, jsonify, request

from backend.core.analytics_pro_engine import build_analytics_dashboard

analytics_pro_bp = Blueprint("analytics_pro_v102", __name__)

@analytics_pro_bp.route("/api/v102/analytics/health")
def analytics_health():
    return jsonify({
        "ok": True,
        "version": "V102",
        "module": "ANALYTICS_PRO",
        "status": "ready"
    })

@analytics_pro_bp.route("/api/v102/analytics/dashboard", methods=["POST"])
def analytics_dashboard():
    payload = request.get_json(silent=True) or {}
    picks = payload.get("picks") or []
    return jsonify(build_analytics_dashboard(picks))
