
from flask import Blueprint, jsonify, render_template, request
from .personalization_engine import (
    get_personalization_admin_status,
    get_personalization_payload,
    infer_user_profile,
    refresh_recommendations,
)

personalization_v75_bp = Blueprint("personalization_v75", __name__)

@personalization_v75_bp.route("/admin/personalization")
def admin_personalization():
    return render_template("admin_personalization_v75.html", status=get_personalization_admin_status())

@personalization_v75_bp.route("/api/personalization-status")
def api_personalization_status():
    return jsonify(get_personalization_admin_status())

@personalization_v75_bp.route("/api/personalization/payload")
def api_personalization_payload():
    user_id = request.values.get("user_id", "anonymous")
    return jsonify(get_personalization_payload(user_id))

@personalization_v75_bp.route("/api/personalization/refresh", methods=["POST", "GET"])
def api_personalization_refresh():
    user_id = request.values.get("user_id", "anonymous")
    return jsonify(refresh_recommendations(user_id))

@personalization_v75_bp.route("/api/personalization/infer", methods=["POST", "GET"])
def api_personalization_infer():
    user_id = request.values.get("user_id", "anonymous")
    return jsonify(infer_user_profile(user_id))
