
from flask import Blueprint, jsonify, request, render_template

from mega_v125.core.architecture_split import build_architecture_split_status
from mega_v125.core.auto_result_engine import build_results_report
from mega_v125.core.live_momentum_engine import build_momentum
from mega_v125.core.shark_ai_real import shark_answer
from mega_v125.core.mobile_app_feel import mobile_payload
from mega_v125.core.saas_ready import saas_status

mega_v125_bp = Blueprint("mega_v125", __name__)

@mega_v125_bp.route("/api/v120/architecture/split")
def v120_split():
    return jsonify(build_architecture_split_status())

@mega_v125_bp.route("/api/v121/results/report", methods=["POST"])
def v121_results():
    payload = request.get_json(silent=True) or {}
    return jsonify(build_results_report(payload.get("picks") or []))

@mega_v125_bp.route("/api/v122/live/momentum", methods=["POST"])
def v122_momentum():
    payload = request.get_json(silent=True) or {}
    return jsonify(build_momentum(payload.get("match") or payload))

@mega_v125_bp.route("/api/v123/shark-ai", methods=["POST"])
def v123_ai():
    payload = request.get_json(silent=True) or {}
    return jsonify(shark_answer(payload.get("question") or payload.get("message") or "", payload.get("context") or {}))

@mega_v125_bp.route("/api/v124/mobile")
def v124_mobile():
    return jsonify(mobile_payload())

@mega_v125_bp.route("/api/v125/saas/status")
def v125_saas():
    return jsonify(saas_status())

@mega_v125_bp.route("/admin/mega-control")
@mega_v125_bp.route("/mega-control")
@mega_v125_bp.route("/admin/v125")
def mega_control_page():
    return render_template(
        "mega_control_v125.html",
        split=build_architecture_split_status(),
        mobile=mobile_payload(),
        saas=saas_status()
    )
