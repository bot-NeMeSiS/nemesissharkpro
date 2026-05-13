from flask import Blueprint, jsonify, render_template, request
from .engine import build_history_center

history_v98_bp = Blueprint("history_v98", __name__)

@history_v98_bp.route("/api/v98/history")
def api_history_v98():
    limit = request.args.get("limit", "250")
    try:
        limit = max(20, min(1000, int(limit)))
    except Exception:
        limit = 250
    return jsonify(build_history_center(limit=limit))

@history_v98_bp.route("/historial-pro")
@history_v98_bp.route("/v98/history")
def page_history_v98():
    center = build_history_center(limit=250)
    return render_template("history_roi_v98.html", center=center)
