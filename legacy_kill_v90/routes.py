
from flask import Blueprint, jsonify, render_template
from .guard import get_real_feed_safe, purge_fake_db
legacy_kill_v90_bp=Blueprint("legacy_kill_v90",__name__)
@legacy_kill_v90_bp.route("/admin/legacy-kill")
def admin_legacy_kill(): return render_template("admin_legacy_kill_v90.html", feed=get_real_feed_safe(False))
@legacy_kill_v90_bp.route("/api/legacy-kill/status")
def status():
    f=get_real_feed_safe(False)
    return jsonify({"version":"V90","legacy_cards_disabled":True,"detail_routes_real_only":True,"dashboard_real_only":True,"no_demo_fallback":True,"feed_ok":f.get("ok"),"counts":f.get("counts"),"message":f.get("message"),"error":f.get("error")})
@legacy_kill_v90_bp.route("/api/legacy-kill/purge")
def purge():
    try:
        from app import get_db
    except Exception:
        get_db=None
    return jsonify(purge_fake_db(get_db))
