
from flask import Blueprint, jsonify
from .telegram_service import TelegramService
from .shark_alerts import build_shark_alert
from .live_monitor import build_live_snapshot

telegram_v95_bp = Blueprint("telegram_v95", __name__)

@telegram_v95_bp.route("/api/v95/telegram/status")
def telegram_status():
    service = TelegramService()

    return jsonify({
        "version": "V95",
        "telegram_enabled": service.enabled,
        "system": "SHARK TELEGRAM REAL"
    })

@telegram_v95_bp.route("/api/v95/live-center")
def live_center():
    return jsonify(build_live_snapshot())

@telegram_v95_bp.route("/api/v95/test-alert")
def test_alert():
    service = TelegramService()

    fake_match = {
        "home": "Real Madrid",
        "away": "Barcelona",
        "pick": "Over 2.5",
        "score": 91,
        "stake": "4/5",
        "ev": "HIGH",
        "risk": "MEDIUM",
        "analysis": "Momentum ofensivo alto y value detectado."
    }

    result = service.send_message(build_shark_alert(fake_match))

    return jsonify({
        "version": "V95",
        "telegram_result": result
    })
