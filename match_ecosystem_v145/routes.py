
from flask import Blueprint, jsonify, render_template, request
from datetime import datetime

match_ecosystem_v145_bp = Blueprint("match_ecosystem_v145", __name__)

def empty_matches_payload():
    return {
        "version": "V145_MATCH_ECOSYSTEM_ULTRA",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "matches": [],
        "empty_state": True,
        "message": "Esperando partidos reales del Real Core/feed. No se muestran partidos inventados.",
        "policy": {
            "no_fake_matches": True,
            "no_fake_scores": True,
            "real_core_first": True
        }
    }

def match_center_payload():
    return {
        "version": "V141_MATCH_CENTER_REAL",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "match": None,
        "timeline": [],
        "stats": {},
        "picks": [],
        "empty_state": True,
        "message": "Selecciona un partido real para abrir el Match Center.",
        "policy": {"no_fake_data": True}
    }

def favorites_payload():
    return {
        "version": "V142_FAVORITES_SYSTEM",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "teams": [],
        "leagues": [],
        "matches": [],
        "empty_state": True,
        "message": "Favoritos preparados para equipos, ligas y partidos reales."
    }

def timeline_payload():
    return {
        "version": "V143_LIVE_TIMELINE_ENGINE",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "events": [],
        "empty_state": True,
        "message": "Timeline preparado para goles, tarjetas, corners, cuotas y momentum reales."
    }

def home_feed_payload():
    return {
        "version": "V144_HOME_FEED_LIVE",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "feed": [],
        "empty_state": True,
        "message": "Home live preparada para actividad real: goles, señales, value y momentum."
    }

def push_payload():
    return {
        "version": "V145_LIVE_PUSH_SYSTEM",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "telegram_ready": False,
        "push_ready": True,
        "alerts": [],
        "policy": {"no_fake_alerts": True, "admin_controlled": True}
    }

# APIs
@match_ecosystem_v145_bp.route("/api/v140/today")
def api_today():
    return jsonify(empty_matches_payload())

@match_ecosystem_v145_bp.route("/api/v141/match-center")
def api_match_center():
    return jsonify(match_center_payload())

@match_ecosystem_v145_bp.route("/api/v142/favorites")
def api_favorites():
    return jsonify(favorites_payload())

@match_ecosystem_v145_bp.route("/api/v143/live-timeline")
def api_timeline():
    return jsonify(timeline_payload())

@match_ecosystem_v145_bp.route("/api/v144/home-feed")
def api_home_feed():
    return jsonify(home_feed_payload())

@match_ecosystem_v145_bp.route("/api/v145/push-status")
def api_push():
    return jsonify(push_payload())

# Pages
@match_ecosystem_v145_bp.route("/matches/today")
@match_ecosystem_v145_bp.route("/partidos/hoy")
def today_page():
    return render_template("matches_today_v140.html", data=empty_matches_payload())

@match_ecosystem_v145_bp.route("/match-center")
@match_ecosystem_v145_bp.route("/partido")
def match_center_page():
    return render_template("match_center_v141.html", data=match_center_payload())

@match_ecosystem_v145_bp.route("/favorites")
@match_ecosystem_v145_bp.route("/favoritos")
def favorites_page():
    return render_template("favorites_v142.html", data=favorites_payload())

@match_ecosystem_v145_bp.route("/live-timeline")
def timeline_page():
    return render_template("live_timeline_v143.html", data=timeline_payload())

@match_ecosystem_v145_bp.route("/home-live")
@match_ecosystem_v145_bp.route("/cliente/live-home")
def home_live_page():
    return render_template("home_feed_live_v144.html", data=home_feed_payload())

@match_ecosystem_v145_bp.route("/push-center")
@match_ecosystem_v145_bp.route("/admin/push-center")
def push_center_page():
    return render_template("push_center_v145.html", data=push_payload())

@match_ecosystem_v145_bp.route("/match-ecosystem")
@match_ecosystem_v145_bp.route("/ecosistema-partidos")
def ecosystem_page():
    return render_template("match_ecosystem_v145.html")
