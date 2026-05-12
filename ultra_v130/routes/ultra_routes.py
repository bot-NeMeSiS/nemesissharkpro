
from flask import Blueprint, jsonify, request, render_template, session

from ultra_v130.core.match_room_engine import build_match_room
from ultra_v130.core.live_center_pro_engine import build_live_center_pro
from ultra_v130.core.client_final_engine import client_final_payload
from ultra_v130.core.business_admin_engine import business_admin_payload

ultra_v130_bp = Blueprint("ultra_v130", __name__)

@ultra_v130_bp.route("/api/v127/match-room", methods=["POST"])
def api_match_room():
    payload = request.get_json(silent=True) or {}
    return jsonify(build_match_room(payload.get("match") or payload))

@ultra_v130_bp.route("/api/v128/live-center-pro", methods=["POST"])
def api_live_center_pro():
    payload = request.get_json(silent=True) or {}
    return jsonify(build_live_center_pro(payload.get("matches") or []))

@ultra_v130_bp.route("/api/v129/client-final")
def api_client_final():
    plan = session.get("membership", "PRO") if session else "PRO"
    return jsonify(client_final_payload(plan))

@ultra_v130_bp.route("/api/v130/business-admin")
def api_business_admin():
    return jsonify(business_admin_payload())

@ultra_v130_bp.route("/match-room-pro")
@ultra_v130_bp.route("/cliente/match-room")
def match_room_page():
    return render_template("match_room_v127.html")

@ultra_v130_bp.route("/live-center-pro-final")
@ultra_v130_bp.route("/cliente/live-final")
def live_center_final_page():
    return render_template("live_center_pro_v128.html")

@ultra_v130_bp.route("/cliente/final")
@ultra_v130_bp.route("/cliente/app")
def client_final_page():
    plan = session.get("membership", "PRO") if session else "PRO"
    return render_template("client_final_v129.html", payload=client_final_payload(plan))

@ultra_v130_bp.route("/admin/business")
@ultra_v130_bp.route("/admin/business-center")
@ultra_v130_bp.route("/admin/v130")
def business_admin_page():
    return render_template("business_admin_v130.html", data=business_admin_payload())
