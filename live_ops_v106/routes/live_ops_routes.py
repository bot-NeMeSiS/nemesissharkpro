
from flask import Blueprint, jsonify, request, render_template

from live_ops_v106.services.live_ops_service import get_ops_dashboard, get_modules, run_safe_auto_scan
from live_ops_v106.core.unified_ops_engine import build_visible_routes_map
from live_ops_v106.services.telegram_ops import telegram_config_status, send_test_alert, send_telegram_message

live_ops_v106_bp = Blueprint("live_ops_v106", __name__)

@live_ops_v106_bp.route("/api/v106/live-ops/status")
def status():
    return jsonify(get_ops_dashboard())

@live_ops_v106_bp.route("/api/v106/live-ops/modules")
def modules():
    return jsonify({"version": "V106", "modules": get_modules()})

@live_ops_v106_bp.route("/api/v106/live-ops/routes")
def routes_map():
    return jsonify({"version": "V106", "routes": build_visible_routes_map()})

@live_ops_v106_bp.route("/api/v106/live-ops/scan", methods=["POST"])
def scan():
    payload = request.get_json(silent=True) or {}
    matches = payload.get("matches") or []
    return jsonify(run_safe_auto_scan(matches))

@live_ops_v106_bp.route("/api/v106/live-ops/telegram/status")
def telegram_status():
    return jsonify(telegram_config_status())

@live_ops_v106_bp.route("/api/v106/live-ops/telegram/test", methods=["GET", "POST"])
def telegram_test():
    return jsonify(send_test_alert())

@live_ops_v106_bp.route("/api/v106/live-ops/telegram/send", methods=["POST"])
def telegram_send():
    payload = request.get_json(silent=True) or {}
    text = payload.get("text") or "🦈 NeMeSiS SHARK PRO · Mensaje manual desde V106 Live Ops."
    return jsonify(send_telegram_message(text))

@live_ops_v106_bp.route("/admin/live-ops")
@live_ops_v106_bp.route("/admin/operaciones")
@live_ops_v106_bp.route("/admin/control")
def live_ops_page():
    status = get_ops_dashboard()
    return render_template("live_ops_v106.html", status=status)
