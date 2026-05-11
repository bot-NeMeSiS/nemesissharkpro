from flask import Blueprint, jsonify, render_template, request
from core.real_core_engine import RealCoreEngine
from live_center_v96.engine import build_live_center
from shark_ai_v96.engine import answer_question, build_match_reading

shark_ai_v96_bp = Blueprint("shark_ai_v96", __name__)


@shark_ai_v96_bp.route("/api/v96/live-center")
def api_live_center_v96():
    force = request.args.get("force", "false").lower() == "true"
    feed = RealCoreEngine.fetch(force=force)
    return jsonify(build_live_center(feed))


@shark_ai_v96_bp.route("/api/v96/shark-ai", methods=["GET", "POST"])
def api_shark_ai_v96():
    force = request.args.get("force", "false").lower() == "true"
    feed = RealCoreEngine.fetch(force=force)
    question = ""
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        question = data.get("question") or data.get("q") or ""
    else:
        question = request.args.get("q", "")
    return jsonify(answer_question(question, feed))


@shark_ai_v96_bp.route("/api/v96/match/<match_id>/reading")
def api_match_reading_v96(match_id):
    match, feed = RealCoreEngine.find(match_id, force=False)
    if not match:
        return jsonify({"ok": False, "message": "Partido no disponible en Real Core", "feed_status": feed.get("message")}), 404
    return jsonify({"ok": True, "version": "V96", "reading": build_match_reading(match)})


@shark_ai_v96_bp.route("/live-center-pro")
@shark_ai_v96_bp.route("/v96/live-center")
def page_live_center_v96():
    force = request.args.get("force", "false").lower() == "true"
    feed = RealCoreEngine.fetch(force=force)
    center = build_live_center(feed)
    return render_template("live_center_v96.html", center=center)


@shark_ai_v96_bp.route("/shark-ai-pro")
@shark_ai_v96_bp.route("/v96/shark-ai")
def page_shark_ai_v96():
    feed = RealCoreEngine.fetch(force=False)
    initial = answer_question("resumen", feed)
    return render_template("shark_ai_v96.html", initial=initial)
