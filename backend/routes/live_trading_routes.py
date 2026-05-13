from flask import Blueprint, jsonify, request

from backend.core.live_trading_engine import build_live_trading_reading, build_live_center

live_trading_bp = Blueprint("live_trading_v101", __name__)

@live_trading_bp.route("/api/v101/live-trading/health")
def live_trading_health():
    return jsonify({
        "ok": True,
        "version": "V101",
        "module": "LIVE_TRADING_CENTER",
        "status": "ready"
    })

@live_trading_bp.route("/api/v101/live-trading/analyze", methods=["POST"])
def analyze_live_match():
    payload = request.get_json(silent=True) or {}
    match = payload.get("match") or payload
    return jsonify(build_live_trading_reading(match))

@live_trading_bp.route("/api/v101/live-trading/center", methods=["POST"])
def live_center():
    payload = request.get_json(silent=True) or {}
    matches = payload.get("matches") or []
    return jsonify(build_live_center(matches))
