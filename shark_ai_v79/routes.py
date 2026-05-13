
"""
Rutas V79 SHARK AI Real Evolution.
"""

from flask import Blueprint, jsonify, render_template, request
from .prediction_engine import (
    get_shark_ai_v79_status,
    predict_pick,
    rebuild_pattern_memory,
    create_model_snapshot,
)

shark_ai_v79_bp = Blueprint("shark_ai_v79", __name__)


@shark_ai_v79_bp.route("/admin/shark-ai-v79")
def admin_shark_ai_v79():
    return render_template("admin_shark_ai_v79.html", status=get_shark_ai_v79_status())


@shark_ai_v79_bp.route("/api/shark-ai-v79/status")
def api_shark_ai_v79_status():
    return jsonify(get_shark_ai_v79_status())


@shark_ai_v79_bp.route("/api/shark-ai-v79/predict", methods=["POST", "GET"])
def api_shark_ai_v79_predict():
    payload = {
        "pick_id": request.values.get("pick_id", "manual-test"),
        "sport": request.values.get("sport", "Fútbol"),
        "league": request.values.get("league", "General"),
        "match_name": request.values.get("match_name", "Partido demo interno"),
        "market": request.values.get("market", "1X2"),
        "selection": request.values.get("selection", "Local"),
        "odds": float(request.values.get("odds", 1.85)),
        "shark_score": float(request.values.get("shark_score", 72)),
    }
    save = request.values.get("save", "true").lower() != "false"
    return jsonify(predict_pick(payload, save=save))


@shark_ai_v79_bp.route("/api/shark-ai-v79/rebuild-patterns", methods=["POST", "GET"])
def api_shark_ai_v79_rebuild_patterns():
    return jsonify(rebuild_pattern_memory())


@shark_ai_v79_bp.route("/api/shark-ai-v79/snapshot", methods=["POST", "GET"])
def api_shark_ai_v79_snapshot():
    return jsonify(create_model_snapshot())
