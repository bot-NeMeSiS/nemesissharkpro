
from flask import Blueprint, jsonify, request, render_template

from live_intelligence_v109.engine import build_live_signal, build_live_center, empty_live_center

live_intelligence_v109_bp = Blueprint("live_intelligence_v109", __name__)

@live_intelligence_v109_bp.route("/api/v109/live-intelligence/health")
def health():
    return jsonify({
        "ok": True,
        "version": "V109",
        "module": "REAL_LIVE_INTELLIGENCE",
        "status": "ready"
    })

@live_intelligence_v109_bp.route("/api/v109/live-intelligence/analyze", methods=["POST"])
def analyze():
    payload = request.get_json(silent=True) or {}
    match = payload.get("match") or payload
    return jsonify(build_live_signal(match))

@live_intelligence_v109_bp.route("/api/v109/live-intelligence/center", methods=["POST"])
def center():
    payload = request.get_json(silent=True) or {}
    matches = payload.get("matches") or []
    return jsonify(build_live_center(matches))

@live_intelligence_v109_bp.route("/api/v109/live-intelligence")
def api_info():
    return jsonify(empty_live_center())

@live_intelligence_v109_bp.route("/live-center-pro")
@live_intelligence_v109_bp.route("/cliente/live-pro")
def live_center_page():
    return render_template("live_center_v109.html")
