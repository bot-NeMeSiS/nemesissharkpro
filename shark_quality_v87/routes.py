
from flask import Blueprint, jsonify, render_template, request
from .quality_engine import get_v87_status, demo_picks, filter_picks, quality_report

shark_quality_v87_bp = Blueprint("shark_quality_v87", __name__)

@shark_quality_v87_bp.route("/admin/shark-quality")
def admin_shark_quality():
    return render_template("admin_shark_quality_v87.html", status=get_v87_status())

@shark_quality_v87_bp.route("/shark-quality")
def shark_quality():
    hide_rejected = request.args.get("hide_rejected", "true").lower() == "true"
    picks = filter_picks(demo_picks(), hide_rejected=hide_rejected)
    return render_template("shark_quality_v87.html", picks=picks, report=quality_report(demo_picks()))

@shark_quality_v87_bp.route("/api/shark-quality/status")
def api_shark_quality_status():
    return jsonify(get_v87_status())

@shark_quality_v87_bp.route("/api/shark-quality/demo")
def api_shark_quality_demo():
    hide_rejected = request.args.get("hide_rejected", "true").lower() == "true"
    picks = filter_picks(demo_picks(), hide_rejected=hide_rejected)
    return jsonify({"picks": picks, "report": quality_report(demo_picks())})
