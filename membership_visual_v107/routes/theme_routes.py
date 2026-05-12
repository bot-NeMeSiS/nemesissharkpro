
from flask import Blueprint, jsonify, request, render_template
from membership_visual_v107.core.theme_engine import build_membership_visual_payload, get_theme

membership_visual_v107_bp = Blueprint("membership_visual_v107", __name__)

@membership_visual_v107_bp.route("/api/v107/membership/theme")
def membership_theme():
    plan = request.args.get("plan", "PRO")
    return jsonify(build_membership_visual_payload(plan))

@membership_visual_v107_bp.route("/api/v107/membership/theme/<plan>")
def membership_theme_plan(plan):
    return jsonify(get_theme(plan))

@membership_visual_v107_bp.route("/membership-visual-pro")
@membership_visual_v107_bp.route("/admin/membership-visual")
def membership_visual_page():
    payload = build_membership_visual_payload("PRO")
    return render_template("membership_visual_v107.html", payload=payload)
