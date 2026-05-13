
from flask import Blueprint, jsonify, render_template, request
from .real_match_engine import get_v89_status, get_real_feed

real_match_v89_bp = Blueprint("real_match_v89", __name__)

@real_match_v89_bp.route("/admin/real-match-engine")
def admin_real_match_engine():
    return render_template("admin_real_match_engine_v89.html", status=get_v89_status())

@real_match_v89_bp.route("/real-matches")
def real_matches():
    force = request.args.get("force","false").lower() == "true"
    return render_template("real_matches_v89.html", feed=get_real_feed(force=force))

@real_match_v89_bp.route("/api/real-matches")
def api_real_matches():
    force = request.args.get("force","false").lower() == "true"
    return jsonify(get_real_feed(force=force))

@real_match_v89_bp.route("/api/real-match-engine/status")
def api_real_match_engine_status():
    return jsonify(get_v89_status())
