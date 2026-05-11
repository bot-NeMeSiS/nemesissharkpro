
from flask import Blueprint, jsonify, render_template, request
from .premium_engine import (
    get_v84_admin_status,
    get_user_premium_payload,
    add_xp,
    complete_mission,
    log_premium_event,
)

premium_v84_bp = Blueprint("premium_v84", __name__)


@premium_v84_bp.route("/admin/premium-experience")
def admin_premium_experience():
    return render_template("admin_premium_experience_v84.html", status=get_v84_admin_status())


@premium_v84_bp.route("/premium-experience")
def premium_experience():
    user_id = request.values.get("user_id", "anonymous")
    return render_template("premium_experience_v84.html", payload=get_user_premium_payload(user_id))


@premium_v84_bp.route("/api/premium-experience/status")
def api_premium_experience_status():
    return jsonify(get_v84_admin_status())


@premium_v84_bp.route("/api/premium-experience/user")
def api_premium_experience_user():
    user_id = request.values.get("user_id", "anonymous")
    return jsonify(get_user_premium_payload(user_id))


@premium_v84_bp.route("/api/premium-experience/xp", methods=["GET", "POST"])
def api_premium_experience_xp():
    user_id = request.values.get("user_id", "anonymous")
    amount = int(request.values.get("amount", 10))
    reason = request.values.get("reason", "Actividad SHARK")
    return jsonify(add_xp(user_id, amount, reason))


@premium_v84_bp.route("/api/premium-experience/mission", methods=["GET", "POST"])
def api_premium_experience_mission():
    user_id = request.values.get("user_id", "anonymous")
    mission_key = request.values.get("mission_key", "open_live_center")
    return jsonify(complete_mission(user_id, mission_key))


@premium_v84_bp.route("/api/premium-experience/event", methods=["GET", "POST"])
def api_premium_experience_event():
    log_premium_event(
        request.values.get("event_type", "UX_EVENT"),
        request.values.get("user_id", "anonymous"),
        request.values.get("title", "Evento UX"),
        {"raw": dict(request.values)}
    )
    return jsonify({"ok": True})
