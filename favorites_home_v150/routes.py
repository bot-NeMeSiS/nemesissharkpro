
from flask import Blueprint, jsonify, request, render_template, session
from favorites_home_v150.core import (
    add_favorite, remove_favorite, list_favorites, add_feed_item, list_feed,
    build_home_live, status, ensure_schema
)

favorites_home_v150_bp = Blueprint("favorites_home_v150", __name__)

def user_id():
    try:
        return str(session.get("user_id") or session.get("username") or "default")
    except Exception:
        return "default"

@favorites_home_v150_bp.route("/api/v149/favorites")
def api_favorites():
    return jsonify({"favorites": list_favorites(request.args.get("user_id") or user_id())})

@favorites_home_v150_bp.route("/api/v149/favorites/add", methods=["POST"])
def api_add_favorite():
    data = request.get_json(silent=True) or {}
    data["user_id"] = data.get("user_id") or user_id()
    return jsonify(add_favorite(data))

@favorites_home_v150_bp.route("/api/v149/favorites/remove", methods=["POST"])
def api_remove_favorite():
    data = request.get_json(silent=True) or {}
    return jsonify(remove_favorite(data.get("user_id") or user_id(), data.get("type") or data.get("fav_type"), data.get("key") or data.get("fav_key")))

@favorites_home_v150_bp.route("/api/v150/home-live")
def api_home_live():
    return jsonify(build_home_live(request.args.get("user_id") or user_id()))

@favorites_home_v150_bp.route("/api/v150/feed/add", methods=["POST"])
def api_feed_add():
    return jsonify(add_feed_item(request.get_json(silent=True) or {}))

@favorites_home_v150_bp.route("/api/v150/feed")
def api_feed():
    return jsonify({"feed": list_feed()})

@favorites_home_v150_bp.route("/api/v150/status")
def api_status():
    return jsonify(status())

@favorites_home_v150_bp.route("/favorites-pro")
@favorites_home_v150_bp.route("/favoritos-pro")
@favorites_home_v150_bp.route("/cliente/favoritos")
def favorites_page():
    ensure_schema()
    return render_template("favorites_pro_v149.html", favorites=list_favorites(user_id()))

@favorites_home_v150_bp.route("/home-live-real")
@favorites_home_v150_bp.route("/cliente/home-live-real")
@favorites_home_v150_bp.route("/inicio-live")
def home_live_page():
    ensure_schema()
    return render_template("home_live_real_v150.html", data=build_home_live(user_id()))

@favorites_home_v150_bp.route("/admin/home-feed")
def admin_home_feed():
    ensure_schema()
    return render_template("home_feed_admin_v150.html", data=build_home_live("default"), status=status())
