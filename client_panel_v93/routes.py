
from flask import Blueprint, jsonify, render_template, request
from .engine import build_vm

client_panel_v93_bp = Blueprint("client_panel_v93", __name__)

@client_panel_v93_bp.route("/")
@client_panel_v93_bp.route("/dashboard")
@client_panel_v93_bp.route("/cliente")
@client_panel_v93_bp.route("/panel")
@client_panel_v93_bp.route("/mi-panel")
def home():
    return render_template("client_pro_v93.html", vm=build_vm(request.args.get("force","false").lower()=="true"))

@client_panel_v93_bp.route("/picks")
@client_panel_v93_bp.route("/cliente/picks")
def picks():
    return render_template("picks_pro_v93.html", vm=build_vm(request.args.get("force","false").lower()=="true"))

@client_panel_v93_bp.route("/partidos")
@client_panel_v93_bp.route("/partidos-hoy")
@client_panel_v93_bp.route("/cliente/partidos")
def matches():
    return render_template("matches_pro_v93.html", vm=build_vm(request.args.get("force","false").lower()=="true"))

@client_panel_v93_bp.route("/mi-cuenta")
@client_panel_v93_bp.route("/cliente/rendimiento")
def account():
    return render_template("account_pro_v93.html", vm=build_vm(False))

@client_panel_v93_bp.route("/api/v93/status")
def status():
    vm = build_vm(False)
    return jsonify({"version":"V93","real_core_only":True,"no_fake":True,"counts":vm["counts"],"health":vm["health"]})
