
from flask import Blueprint, jsonify, request, render_template

from auto_alerts_v105.engine import build_alert_from_candidate, build_alert_batch

auto_alerts_v105_bp = Blueprint("auto_alerts_v105", __name__)

@auto_alerts_v105_bp.route("/api/v105/alerts/health")
def health():
    return jsonify({
        "ok": True,
        "version": "V105",
        "module": "AUTO_ALERTS_ENGINE",
        "status": "ready"
    })

@auto_alerts_v105_bp.route("/api/v105/alerts/build", methods=["POST"])
def build_alert():
    payload = request.get_json(silent=True) or {}
    candidate = payload.get("candidate") or payload
    return jsonify(build_alert_from_candidate(candidate))

@auto_alerts_v105_bp.route("/api/v105/alerts/batch", methods=["POST"])
def build_batch():
    payload = request.get_json(silent=True) or {}
    candidates = payload.get("candidates") or []
    min_priority = payload.get("min_priority") or "MEDIUM"
    return jsonify(build_alert_batch(candidates, min_priority=min_priority))

@auto_alerts_v105_bp.route("/auto-alerts-engine")
def alerts_page():
    return render_template("auto_alerts_v105.html")
