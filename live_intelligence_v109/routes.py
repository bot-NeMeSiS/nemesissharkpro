
from flask import Blueprint, jsonify, render_template
from live_intelligence_v109.engine import demo_live_feed

live_intelligence_v109_bp = Blueprint("live_intelligence_v109", __name__)

@live_intelligence_v109_bp.route("/api/v109/live-intelligence")
def live_intelligence_api():
    return jsonify({
        "version": "V109_REAL_LIVE_INTELLIGENCE",
        "signals": demo_live_feed()
    })

@live_intelligence_v109_bp.route("/live-center-pro")
def live_center_pro():
    return render_template("live_center_v109.html", signals=demo_live_feed())
