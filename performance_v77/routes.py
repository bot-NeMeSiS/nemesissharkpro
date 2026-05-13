
from flask import Blueprint, jsonify, render_template
from .performance_engine import get_performance_status, optimize_sqlite

performance_v77_bp = Blueprint("performance_v77", __name__)

@performance_v77_bp.route("/admin/performance")
def admin_performance():
    return render_template("admin_performance_v77.html", status=get_performance_status())

@performance_v77_bp.route("/api/performance-status")
def api_performance_status():
    return jsonify(get_performance_status())

@performance_v77_bp.route("/api/performance/optimize", methods=["GET", "POST"])
def api_performance_optimize():
    return jsonify(optimize_sqlite())
