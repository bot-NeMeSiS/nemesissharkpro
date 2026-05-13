
from flask import Blueprint, jsonify, request, render_template
from match_center_v147.core import build_center, add_events, upsert_stats, ensure_schema

match_center_v147_bp = Blueprint("match_center_v147", __name__)

@match_center_v147_bp.route("/api/v147/match-center")
def api_center():
    return jsonify(build_center(request.args.get("fixture_id"), request.args.get("external_id")))

@match_center_v147_bp.route("/api/v147/match-center/events/<int:fixture_id>", methods=["POST"])
def api_events(fixture_id):
    data = request.get_json(silent=True) or {}
    return jsonify(add_events(fixture_id, data.get("events") or []))

@match_center_v147_bp.route("/api/v147/match-center/stats/<int:fixture_id>", methods=["POST"])
def api_stats(fixture_id):
    data = request.get_json(silent=True) or {}
    return jsonify(upsert_stats(fixture_id, data.get("stats") or []))

@match_center_v147_bp.route("/match-center-real")
@match_center_v147_bp.route("/partido-real")
@match_center_v147_bp.route("/cliente/match-center-real")
def page_center():
    ensure_schema()
    return render_template("match_center_real_v147.html", data=build_center(request.args.get("fixture_id"), request.args.get("external_id")))
