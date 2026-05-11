
from flask import Blueprint, jsonify, render_template, request
from .live_data_engine import get_v86_status, demo_matches, data_quality_report, normalize_matches, bucket_matches

live_data_v86_bp = Blueprint("live_data_v86", __name__)

@live_data_v86_bp.route("/admin/live-data-quality")
def admin_live_data_quality():
    return render_template("admin_live_data_quality_v86.html", status=get_v86_status())

@live_data_v86_bp.route("/live-data-quality")
def live_data_quality():
    matches = normalize_matches(demo_matches(), hide_invalid=False)
    return render_template("live_data_quality_v86.html", matches=matches, report=data_quality_report(demo_matches()))

@live_data_v86_bp.route("/api/live-data-quality/status")
def api_live_data_status():
    return jsonify(get_v86_status())

@live_data_v86_bp.route("/api/live-data-quality/demo")
def api_live_data_demo():
    hide_invalid = request.args.get("hide_invalid", "true").lower() == "true"
    matches = normalize_matches(demo_matches(), hide_invalid=hide_invalid)
    return jsonify({
        "matches": matches,
        "report": data_quality_report(demo_matches()),
        "buckets": bucket_matches(demo_matches()),
    })
