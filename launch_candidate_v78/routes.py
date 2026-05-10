
from flask import Blueprint, jsonify, render_template
from .launch_candidate_engine import get_launch_candidate_status

launch_candidate_v78_bp = Blueprint("launch_candidate_v78", __name__)

@launch_candidate_v78_bp.route("/admin/launch-candidate")
def admin_launch_candidate():
    return render_template("admin_launch_candidate_v78.html", status=get_launch_candidate_status())

@launch_candidate_v78_bp.route("/api/launch-candidate")
def api_launch_candidate():
    return jsonify(get_launch_candidate_status())
