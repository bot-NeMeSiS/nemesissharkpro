
from flask import Blueprint, jsonify, render_template, request
from .engine import build_vm, build_match_analysis

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


@client_panel_v93_bp.route("/analisis-pro/<match_id>")
@client_panel_v93_bp.route("/partido-pro/<match_id>")
def match_detail_pro(match_id):
    try:
        from core.real_core_engine import RealCoreEngine
        match, feed = RealCoreEngine.find(match_id, force=request.args.get("force","false").lower()=="true")
    except Exception as exc:
        match, feed = None, {"ok": False, "message": "Real Core no disponible", "error": str(exc), "matches": []}
    if not match:
        return render_template("real_core_empty_v91.html", title="Partido no disponible en feed real", feed=feed), 404
    return render_template("match_detail_pro_v94.html", analysis=build_match_analysis(match), feed=feed, vm=build_vm(False))

@client_panel_v93_bp.route("/api/v94/analysis/<match_id>")
def api_match_detail_pro(match_id):
    from core.real_core_engine import RealCoreEngine
    match, feed = RealCoreEngine.find(match_id, force=False)
    if not match:
        return jsonify({"ok": False, "message": "Partido no disponible en feed real"}), 404
    return jsonify({"ok": True, "version": "V94", "analysis": build_match_analysis(match)})

@client_panel_v93_bp.route("/api/v93/status")
def status():
    vm = build_vm(False)
    return jsonify({"version":"V94","real_core_only":True,"no_fake":True,"counts":vm["counts"],"health":vm["health"]})
