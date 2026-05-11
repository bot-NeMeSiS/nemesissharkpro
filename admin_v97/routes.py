from flask import Blueprint, jsonify, render_template, request
from .engine import build_admin_center

admin_v97_bp = Blueprint("admin_v97", __name__)

@admin_v97_bp.route("/api/v97/admin/center")
def api_admin_center_v97():
    force = request.args.get("force", "false").lower() == "true"
    return jsonify(build_admin_center(force=force))

@admin_v97_bp.route("/admin-pro-saas")
@admin_v97_bp.route("/v97/admin")
def page_admin_center_v97():
    force = request.args.get("force", "false").lower() == "true"
    center = build_admin_center(force=force)
    return render_template("admin_pro_saas_v97.html", center=center)
