
from flask import Blueprint, render_template, jsonify, session
from datetime import datetime

smart_ux_v139_bp = Blueprint("smart_ux_v139", __name__)

def engagement_payload():
    plan = session.get("membership", "PRO") if session else "PRO"
    return {
        "version": "V139_SMART_UX_ENGAGEMENT",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "plan": plan,
        "widgets": [
            {"title": "Actividad SHARK", "status": "Preparado", "icon": "🦈"},
            {"title": "Picks reales", "status": "Real Core", "icon": "🎯"},
            {"title": "Live Intelligence", "status": "Esperando feed real", "icon": "📡"},
            {"title": "Rendimiento", "status": "ROI / Winrate", "icon": "📊"},
        ],
        "notifications": [
            {"type": "info", "text": "No se muestran partidos inventados. Si no hay feed real, aparece estado premium vacío."},
            {"type": "success", "text": "Tu experiencia cliente está preparada para picks, live y alertas reales."}
        ],
        "policy": {"no_fake_data": True, "client_first": True, "premium_empty_states": True}
    }

@smart_ux_v139_bp.route("/cliente/smart")
@smart_ux_v139_bp.route("/smart-ux")
def smart_ux_page():
    return render_template("smart_ux_v139.html", data=engagement_payload())

@smart_ux_v139_bp.route("/api/v139/smart-ux")
def smart_ux_api():
    return jsonify(engagement_payload())
