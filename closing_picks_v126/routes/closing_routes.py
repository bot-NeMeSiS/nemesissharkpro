
from flask import Blueprint, jsonify, request, render_template
from closing_picks_v126.core.closing_engine import (
    ensure_schema, create_pick, list_picks, close_pick, bulk_close, performance
)

closing_picks_v126_bp = Blueprint("closing_picks_v126", __name__)

@closing_picks_v126_bp.route("/api/v126/closing/health")
def health():
    ensure_schema()
    return jsonify({"ok": True, "version": "V126", "module": "CLOSING_PICKS_PRO"})

@closing_picks_v126_bp.route("/api/v126/closing/create", methods=["POST"])
def create():
    payload = request.get_json(silent=True) or {}
    return jsonify(create_pick(payload))

@closing_picks_v126_bp.route("/api/v126/closing/list")
def list_api():
    status = request.args.get("status")
    return jsonify({"picks": list_picks(status=status)})

@closing_picks_v126_bp.route("/api/v126/closing/close/<int:pick_id>", methods=["POST"])
def close_api(pick_id):
    payload = request.get_json(silent=True) or {}
    result = payload.get("result") or request.args.get("result") or "VOID"
    return jsonify(close_pick(pick_id, result))

@closing_picks_v126_bp.route("/api/v126/closing/bulk-close", methods=["POST"])
def bulk_close_api():
    payload = request.get_json(silent=True) or {}
    return jsonify(bulk_close(payload.get("items") or []))

@closing_picks_v126_bp.route("/api/v126/closing/performance")
def performance_api():
    return jsonify(performance(user_id=request.args.get("user_id")))

@closing_picks_v126_bp.route("/admin/closing-picks")
@closing_picks_v126_bp.route("/admin/results")
@closing_picks_v126_bp.route("/admin/pick-results")
def closing_page():
    ensure_schema()
    return render_template("closing_picks_v126.html", stats=performance(), picks=list_picks())
