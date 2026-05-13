
"""
Rutas V72 Launch Readiness + Beta.
"""

from flask import Blueprint, jsonify, render_template, request
from .launch_engine import get_launch_status, create_beta_invite, set_setting, add_launch_event

launch_v72_bp = Blueprint("launch_v72", __name__)


@launch_v72_bp.route("/admin/launch")
def admin_launch():
    return render_template("admin_launch_v72.html", status=get_launch_status())


@launch_v72_bp.route("/api/launch-status")
def api_launch_status():
    return jsonify(get_launch_status())


@launch_v72_bp.route("/api/beta-invite/create", methods=["POST", "GET"])
def api_beta_invite_create():
    email = request.values.get("email", "").strip()
    plan = request.values.get("plan", "PRO").strip().upper()
    notes = request.values.get("notes", "").strip()

    if not email:
        return jsonify({"ok": False, "error": "email_required"}), 400

    invite_code = create_beta_invite(email, plan, notes)
    add_launch_event("BETA_INVITE", "CREATED", f"Invitación creada para {email}")
    return jsonify({"ok": True, "email": email, "invite_code": invite_code, "plan": plan})


@launch_v72_bp.route("/api/launch-setting", methods=["POST", "GET"])
def api_launch_setting():
    key = request.values.get("key", "").strip()
    value = request.values.get("value", "").strip()

    if not key:
        return jsonify({"ok": False, "error": "key_required"}), 400

    set_setting(key, value)
    add_launch_event("SETTING", "UPDATED", f"{key} = {value}")
    return jsonify({"ok": True, "key": key, "value": value})
