
from flask import Blueprint, jsonify, request, render_template
from real_data_v116.core.real_data_engine import (
    build_real_data_status,
    build_client_real_feed,
    save_cache,
    load_cache,
    log_sync,
    latest_sync_logs,
    ensure_real_data_schema,
)

real_data_v116_bp = Blueprint("real_data_v116", __name__)

@real_data_v116_bp.route("/api/v116/real-data/status")
def status():
    return jsonify(build_real_data_status())

@real_data_v116_bp.route("/api/v116/real-data/client-feed")
def client_feed():
    return jsonify(build_client_real_feed())

@real_data_v116_bp.route("/api/v116/real-data/cache/save", methods=["POST"])
def cache_save():
    payload = request.get_json(silent=True) or {}
    source = payload.get("source") or "real_core"
    data_type = payload.get("data_type") or "generic"
    cache_key = payload.get("cache_key") or "default"
    data = payload.get("payload") or {}
    ttl = int(payload.get("ttl_minutes") or 10)
    save_cache(source, data_type, cache_key, data, ttl_minutes=ttl)
    log_sync(source, data_type, "OK", f"Cache actualizado: {cache_key}")
    return jsonify({"ok": True, "source": source, "data_type": data_type, "cache_key": cache_key})

@real_data_v116_bp.route("/api/v116/real-data/cache")
def cache_list():
    return jsonify({"cache": load_cache()})

@real_data_v116_bp.route("/api/v116/real-data/logs")
def logs():
    return jsonify({"logs": latest_sync_logs()})

@real_data_v116_bp.route("/admin/real-data-sync")
@real_data_v116_bp.route("/admin/data-sync")
def real_data_sync_page():
    ensure_real_data_schema()
    return render_template(
        "real_data_sync_v116.html",
        status=build_real_data_status(),
        feed=build_client_real_feed(),
        logs=latest_sync_logs()
    )
