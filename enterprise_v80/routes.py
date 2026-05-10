
from flask import Blueprint, jsonify, render_template, request
from .enterprise_status import get_enterprise_scale_status
from .queue import enqueue_job, process_enterprise_jobs
from .database import init_enterprise_db_settings
from .migration_readiness import get_migration_readiness

enterprise_v80_bp = Blueprint("enterprise_v80", __name__)


@enterprise_v80_bp.route("/admin/enterprise-scale")
def admin_enterprise_scale():
    return render_template("admin_enterprise_scale_v80.html", status=get_enterprise_scale_status())


@enterprise_v80_bp.route("/api/enterprise-scale")
def api_enterprise_scale():
    return jsonify(get_enterprise_scale_status())


@enterprise_v80_bp.route("/api/enterprise-scale/optimize-db", methods=["GET", "POST"])
def api_enterprise_optimize_db():
    init_enterprise_db_settings()
    return jsonify({"ok": True, "message": "SQLite enterprise settings applied"})


@enterprise_v80_bp.route("/api/enterprise-scale/enqueue", methods=["GET", "POST"])
def api_enterprise_enqueue():
    job_type = request.values.get("job_type", "MANUAL_TEST")
    payload = request.values.get("payload", "{}")
    priority = request.values.get("priority", "NORMAL")
    enqueue_job(job_type, payload, priority)
    return jsonify({"ok": True, "job_type": job_type})


@enterprise_v80_bp.route("/api/enterprise-scale/process-jobs", methods=["GET", "POST"])
def api_enterprise_process_jobs():
    limit = int(request.values.get("limit", 5))
    return jsonify(process_enterprise_jobs(limit=limit))


@enterprise_v80_bp.route("/api/enterprise-scale/migration-readiness")
def api_migration_readiness():
    return jsonify(get_migration_readiness())
