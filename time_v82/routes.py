
from flask import Blueprint, jsonify, request
from .time_engine import get_time_v82_status, format_match_datetime
time_v82_bp = Blueprint("time_v82", __name__)
@time_v82_bp.route("/api/timezone-status")
def api_timezone_status():
    return jsonify(get_time_v82_status())
@time_v82_bp.route("/api/format-match-time")
def api_format_match_time():
    value = request.values.get("time") or request.values.get("commence_time")
    return jsonify(format_match_datetime(value))
