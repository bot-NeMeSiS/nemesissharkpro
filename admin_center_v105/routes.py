
from flask import Blueprint, jsonify, render_template

from admin_center_v105.engine import build_admin_center_status

admin_center_v105_bp = Blueprint("admin_center_v105", __name__)

@admin_center_v105_bp.route("/api/v105/admin/center")
def admin_center_api():
    return jsonify(build_admin_center_status())

@admin_center_v105_bp.route("/admin")
@admin_center_v105_bp.route("/admin/")
@admin_center_v105_bp.route("/admin/pro")
@admin_center_v105_bp.route("/admin-panel")
@admin_center_v105_bp.route("/admin/dashboard")
@admin_center_v105_bp.route("/admin-pro-saas")
def admin_center_page():
    status = build_admin_center_status()
    return render_template("admin_center_v105.html", status=status)
