
from flask import Blueprint, jsonify, render_template
from .live_experience_engine import get_live_experience_status, demo_live_matches

live_experience_v83_bp = Blueprint("live_experience_v83", __name__)


@live_experience_v83_bp.route("/live-experience")
def live_experience_page():
    return render_template("live_experience_v83.html", status=get_live_experience_status())


@live_experience_v83_bp.route("/admin/live-experience")
def admin_live_experience_page():
    return render_template("admin_live_experience_v83.html", status=get_live_experience_status())


@live_experience_v83_bp.route("/api/live-experience")
def api_live_experience():
    return jsonify(get_live_experience_status())


@live_experience_v83_bp.route("/api/live-experience/demo")
def api_live_experience_demo():
    return jsonify(demo_live_matches())
