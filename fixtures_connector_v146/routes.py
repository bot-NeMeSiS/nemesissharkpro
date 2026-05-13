
from flask import Blueprint, jsonify, request, render_template
from fixtures_connector_v146.core import sync_fixtures, list_fixtures, status, logs, ensure_schema

fixtures_connector_v146_bp = Blueprint("fixtures_connector_v146", __name__)

@fixtures_connector_v146_bp.route("/api/v146/fixtures/status")
def api_status():
    return jsonify(status())

@fixtures_connector_v146_bp.route("/api/v146/fixtures/list")
def api_list():
    f = request.args.get("filter", "today")
    return jsonify({"filter": f, "fixtures": list_fixtures(f), "policy": {"no_fake_matches": True}})

@fixtures_connector_v146_bp.route("/api/v146/fixtures/sync", methods=["POST"])
def api_sync():
    payload = request.get_json(silent=True) or {}
    return jsonify(sync_fixtures(payload.get("fixtures") or payload.get("matches") or [], payload.get("source") or "real_core"))

@fixtures_connector_v146_bp.route("/api/v146/fixtures/logs")
def api_logs():
    return jsonify({"logs": logs()})

@fixtures_connector_v146_bp.route("/fixtures/today-pro")
@fixtures_connector_v146_bp.route("/partidos/hoy-pro")
@fixtures_connector_v146_bp.route("/cliente/partidos-pro")
def page_today():
    ensure_schema()
    f = request.args.get("filter", "today")
    return render_template("fixtures_today_v146.html", fixtures=list_fixtures(f), status=status(), filter_name=f)

@fixtures_connector_v146_bp.route("/admin/fixtures-sync")
def page_sync():
    ensure_schema()
    return render_template("fixtures_sync_v146.html", status=status(), logs=logs())
