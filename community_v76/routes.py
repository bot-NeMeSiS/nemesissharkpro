
from flask import Blueprint, jsonify, render_template, request
from .community_engine import get_community_status, track_popular_pick, rebuild_leaderboard, add_community_activity

community_v76_bp = Blueprint("community_v76", __name__)

@community_v76_bp.route("/community")
def public_community():
    return render_template("community_v76.html", status=get_community_status())

@community_v76_bp.route("/admin/community")
def admin_community():
    return render_template("admin_community_v76.html", status=get_community_status())

@community_v76_bp.route("/api/community-status")
def api_community_status():
    return jsonify(get_community_status())

@community_v76_bp.route("/api/community/rebuild", methods=["GET", "POST"])
def api_community_rebuild():
    return jsonify(rebuild_leaderboard())

@community_v76_bp.route("/api/community/track-pick", methods=["GET", "POST"])
def api_track_pick():
    pick_id = request.values.get("pick_id", "unknown")
    sport = request.values.get("sport", "")
    match_name = request.values.get("match_name", "")
    market = request.values.get("market", "")
    action = request.values.get("action", "view")
    track_popular_pick(pick_id, sport, match_name, market, action)
    return jsonify({"ok": True})

@community_v76_bp.route("/api/community/activity", methods=["GET", "POST"])
def api_activity():
    add_community_activity(
        request.values.get("activity_type", "SYSTEM"),
        request.values.get("user_id", "system"),
        request.values.get("title", "Actividad SHARK"),
        request.values.get("message", "Nueva actividad registrada."),
    )
    return jsonify({"ok": True})
