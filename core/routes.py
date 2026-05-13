
from flask import Blueprint, jsonify, render_template, request
from .real_core_engine import RealCoreEngine, purge_legacy_db

real_core_v91_bp = Blueprint("real_core_v91", __name__)

@real_core_v91_bp.route("/admin/real-core")
def admin_real_core():
    return render_template("admin_real_core_v91.html", status=RealCoreEngine.status())

@real_core_v91_bp.route("/api/real-core/status")
def api_real_core_status():
    return jsonify(RealCoreEngine.status())

@real_core_v91_bp.route("/api/core-feed")
def api_core_feed():
    force = request.args.get("force", "false").lower() == "true"
    return jsonify(RealCoreEngine.fetch(force=force))

@real_core_v91_bp.route("/api/core-purge")
def api_core_purge():
    try:
        from app import get_db
    except Exception:
        get_db = None
    return jsonify(purge_legacy_db(get_db))
