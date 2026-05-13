
from flask import Blueprint, jsonify, render_template, request
from .engine import build_client_dashboard

client_panel_v92_bp = Blueprint("client_panel_v92", __name__)

@client_panel_v92_bp.route("/cliente")
@client_panel_v92_bp.route("/panel")
@client_panel_v92_bp.route("/mi-panel")
def client_panel():
    vm = build_client_dashboard(force=request.args.get("force", "false").lower() == "true")
    return render_template("client_panel_v92.html", vm=vm)

@client_panel_v92_bp.route("/cliente/picks")
def client_picks():
    vm = build_client_dashboard(force=request.args.get("force", "false").lower() == "true")
    return render_template("client_picks_v92.html", vm=vm)

@client_panel_v92_bp.route("/cliente/partidos")
def client_matches():
    vm = build_client_dashboard(force=request.args.get("force", "false").lower() == "true")
    return render_template("client_matches_v92.html", vm=vm)

@client_panel_v92_bp.route("/cliente/rendimiento")
def client_performance():
    return render_template("client_performance_v92.html", vm=build_client_dashboard(False))

@client_panel_v92_bp.route("/api/client-panel/status")
def api_client_panel_status():
    vm = build_client_dashboard(False)
    return jsonify({"version": "V92", "client_panel_recovered": True, "real_core_only": True,
                    "no_demo_fallback": True, "counts": vm["counts"], "health": vm["health"]})
