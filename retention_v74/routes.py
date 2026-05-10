
"""
Rutas V74 UX Automation + Retention Engine.
"""

from flask import Blueprint, jsonify, render_template, request
from .retention_engine import (
    get_retention_status,
    run_retention_rules,
    track_engagement_event,
    get_user_experience_payload,
    calculate_user_engagement,
)

retention_v74_bp = Blueprint("retention_v74", __name__)


@retention_v74_bp.route("/admin/retention")
def admin_retention():
    return render_template("admin_retention_v74.html", status=get_retention_status())


@retention_v74_bp.route("/api/retention-status")
def api_retention_status():
    return jsonify(get_retention_status())


@retention_v74_bp.route("/api/retention/run", methods=["POST", "GET"])
def api_retention_run():
    return jsonify(run_retention_rules())


@retention_v74_bp.route("/api/ux/track", methods=["POST", "GET"])
def api_ux_track():
    user_id = request.values.get("user_id", "anonymous")
    event_type = request.values.get("event_type", "PAGE_VIEW")
    event_value = request.values.get("event_value", "")
    page = request.values.get("page", request.path)
    source = request.values.get("source", "APP")

    track_engagement_event(user_id, event_type, event_value, page, source)
    engagement = calculate_user_engagement(user_id)
    return jsonify({"ok": True, "engagement": engagement})


@retention_v74_bp.route("/api/ux/payload")
def api_ux_payload():
    user_id = request.values.get("user_id", "anonymous")
    return jsonify(get_user_experience_payload(user_id))
