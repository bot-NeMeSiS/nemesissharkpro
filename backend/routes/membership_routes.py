from flask import Blueprint, jsonify

membership_bp = Blueprint("membership", __name__)

PLANS = {
    "FREE": {"live_center": False, "daily_picks": 2},
    "PRO": {"live_center": True, "daily_picks": 10},
    "ELITE": {"live_center": True, "daily_picks": 999}
}

@membership_bp.route("/api/v99/membership/plans")
def plans():
    return jsonify(PLANS)

@membership_bp.route("/api/v99/membership/status")
def status():
    return jsonify({
        "plan": "PRO",
        "access": True,
        "features": PLANS["PRO"]
    })
