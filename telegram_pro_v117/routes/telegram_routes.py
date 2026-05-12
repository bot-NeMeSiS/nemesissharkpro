
from flask import Blueprint, jsonify, request, render_template

from telegram_pro_v117.core.telegram_engine import (
    dashboard_payload,
    config_status,
    send_test_alert,
    send_telegram_alert,
    send_pick_alert,
    send_live_alert,
    latest_logs,
)

telegram_pro_v117_bp = Blueprint("telegram_pro_v117", __name__)

@telegram_pro_v117_bp.route("/api/v117/telegram/status")
def telegram_status():
    return jsonify(config_status())

@telegram_pro_v117_bp.route("/api/v117/telegram/dashboard")
def telegram_dashboard_api():
    return jsonify(dashboard_payload())

@telegram_pro_v117_bp.route("/api/v117/telegram/test", methods=["GET", "POST"])
def telegram_test():
    return jsonify(send_test_alert())

@telegram_pro_v117_bp.route("/api/v117/telegram/send", methods=["POST"])
def telegram_send():
    data = request.get_json(silent=True) or {}
    title = data.get("title") or "Alerta SHARK"
    body = data.get("body") or data.get("message") or "Mensaje manual desde admin."
    plan = data.get("plan") or "PRO"
    alert_type = data.get("alert_type") or "MANUAL"
    force = bool(data.get("force", False))
    return jsonify(send_telegram_alert(title, body, plan, alert_type, force))

@telegram_pro_v117_bp.route("/api/v117/telegram/pick", methods=["POST"])
def telegram_pick():
    data = request.get_json(silent=True) or {}
    return jsonify(send_pick_alert(data))

@telegram_pro_v117_bp.route("/api/v117/telegram/live", methods=["POST"])
def telegram_live():
    data = request.get_json(silent=True) or {}
    return jsonify(send_live_alert(data))

@telegram_pro_v117_bp.route("/api/v117/telegram/logs")
def telegram_logs():
    return jsonify({"logs": latest_logs()})

@telegram_pro_v117_bp.route("/admin/telegram-pro")
@telegram_pro_v117_bp.route("/admin/telegram")
@telegram_pro_v117_bp.route("/admin/alerts")
def telegram_admin_page():
    return render_template("telegram_pro_v117.html", data=dashboard_payload())
