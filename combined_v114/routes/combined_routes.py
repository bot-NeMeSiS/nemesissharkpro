
from flask import Blueprint, jsonify, request, render_template, redirect, session

from combined_v114.core.picks_manager import create_pick, list_picks, close_pick, analytics, ensure_picks_manager_schema
from combined_v114.core.plans import plans_payload
from combined_v114.core.system_guard import build_system_guard

combined_v114_bp = Blueprint("combined_v114", __name__)

# ---- Plans / Home ----
@combined_v114_bp.route("/")
def home_v114():
    return render_template("home_v114.html", plans=plans_payload()["plans"])

@combined_v114_bp.route("/planes")
@combined_v114_bp.route("/membresias")
@combined_v114_bp.route("/pricing")
def plans_page_v114():
    return render_template("plans_v114.html", plans=plans_payload()["plans"])

@combined_v114_bp.route("/api/v114/plans")
def plans_api_v114():
    return jsonify(plans_payload())

# ---- Account / logout recovery ----
@combined_v114_bp.route("/cuenta")
@combined_v114_bp.route("/cliente/cuenta-pro")
def account_v114():
    plan = session.get("membership", "PRO") if session else "PRO"
    return render_template("account_v114.html", plan=plan)

@combined_v114_bp.route("/logout-v114")
def logout_v114_extra():
    try:
        session.clear()
    except Exception:
        pass
    return redirect("/")

# ---- Picks Manager PRO ----
@combined_v114_bp.route("/api/v112/picks-manager/health")
def picks_manager_health():
    ensure_picks_manager_schema()
    return jsonify({"ok": True, "version": "V112", "module": "PICKS_MANAGER_PRO"})

@combined_v114_bp.route("/api/v112/picks-manager/list")
def picks_manager_list():
    return jsonify({"picks": list_picks()})

@combined_v114_bp.route("/api/v112/picks-manager/create", methods=["POST"])
def picks_manager_create():
    payload = request.get_json(silent=True) or {}
    return jsonify(create_pick(payload))

@combined_v114_bp.route("/api/v112/picks-manager/close/<int:pick_id>", methods=["POST"])
def picks_manager_close(pick_id):
    payload = request.get_json(silent=True) or {}
    result = payload.get("result") or request.args.get("result") or "VOID"
    return jsonify(close_pick(pick_id, result))

@combined_v114_bp.route("/api/v112/picks-manager/analytics")
def picks_manager_analytics():
    return jsonify(analytics())

@combined_v114_bp.route("/admin/picks-manager")
@combined_v114_bp.route("/admin/picks")
def picks_manager_page():
    ensure_picks_manager_schema()
    return render_template("picks_manager_v112.html", picks=list_picks(), stats=analytics())

# ---- Live UI Ultra ----
@combined_v114_bp.route("/live-ultra")
@combined_v114_bp.route("/cliente/live-ultra")
@combined_v114_bp.route("/live-center-ultra")
def live_ultra_page():
    return render_template("live_ultra_v113.html")

# ---- V114 System ----
@combined_v114_bp.route("/api/v114/system/guard")
def system_guard_api():
    return jsonify(build_system_guard())

@combined_v114_bp.route("/admin/system-guard")
@combined_v114_bp.route("/admin/v114")
def system_guard_page():
    return render_template("system_guard_v114.html", status=build_system_guard())
