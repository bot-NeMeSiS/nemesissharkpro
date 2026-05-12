from flask import Blueprint, jsonify, request

from backend.core.shark_ai_ultra_engine import build_shark_ultra_reading, build_chat_answer

shark_ai_ultra_bp = Blueprint("shark_ai_ultra_v100", __name__)

@shark_ai_ultra_bp.route("/api/v100/shark-ai-ultra/health")
def shark_ai_ultra_health():
    return jsonify({
        "ok": True,
        "version": "V100",
        "module": "SHARK_AI_ULTRA",
        "status": "ready"
    })

@shark_ai_ultra_bp.route("/api/v100/shark-ai-ultra/analyze", methods=["POST"])
def analyze_match():
    payload = request.get_json(silent=True) or {}
    match = payload.get("match") or payload
    return jsonify(build_shark_ultra_reading(match))

@shark_ai_ultra_bp.route("/api/v100/shark-ai-ultra/chat", methods=["POST"])
def shark_chat():
    payload = request.get_json(silent=True) or {}
    question = payload.get("question") or payload.get("message") or ""
    context = payload.get("context") or {}
    return jsonify(build_chat_answer(question, context))
