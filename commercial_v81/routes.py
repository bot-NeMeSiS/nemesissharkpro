
from flask import Blueprint, jsonify, render_template, request, redirect
from .commercial_engine import (
    get_commercial_status,
    get_landing_metrics,
    create_or_update_public_profile,
    get_public_profile,
    share_pick,
    get_shared_pick,
    log_commercial_event,
)

commercial_v81_bp = Blueprint("commercial_v81", __name__)


@commercial_v81_bp.route("/premium")
def premium_landing():
    log_commercial_event("LANDING_VIEW", "WEB", "Landing premium visitada")
    return render_template("premium_landing_v81.html", landing=get_landing_metrics())


@commercial_v81_bp.route("/beta")
def beta_landing():
    log_commercial_event("BETA_PAGE_VIEW", "WEB", "Página beta visitada")
    return render_template("beta_landing_v81.html", landing=get_landing_metrics())


@commercial_v81_bp.route("/admin/commercial")
def admin_commercial():
    return render_template("admin_commercial_v81.html", status=get_commercial_status())


@commercial_v81_bp.route("/api/commercial-status")
def api_commercial_status():
    return jsonify(get_commercial_status())


@commercial_v81_bp.route("/profile/<user_id>")
def public_profile(user_id):
    profile = get_public_profile(user_id)
    if not profile:
        profile = create_or_update_public_profile(user_id)
    return render_template("public_profile_v81.html", payload=profile)


@commercial_v81_bp.route("/api/profile/create", methods=["GET", "POST"])
def api_profile_create():
    user_id = request.values.get("user_id", "anonymous")
    display_name = request.values.get("display_name")
    avatar_emoji = request.values.get("avatar_emoji", "🦈")
    bio = request.values.get("bio", "Perfil SHARK PRO")
    return jsonify(create_or_update_public_profile(user_id, display_name, avatar_emoji, bio))


@commercial_v81_bp.route("/share/<share_code>")
def public_shared_pick(share_code):
    pick = get_shared_pick(share_code, increment_view=True)
    if not pick:
        return redirect("/premium")
    return render_template("shared_pick_v81.html", pick=pick)


@commercial_v81_bp.route("/api/share-pick", methods=["GET", "POST"])
def api_share_pick():
    data = share_pick(
        pick_id=request.values.get("pick_id", "manual"),
        user_id=request.values.get("user_id", "anonymous"),
        title=request.values.get("title", "Pick SHARK PRO"),
        match_name=request.values.get("match_name", "Partido destacado"),
        market=request.values.get("market", "Mercado premium"),
        odds=float(request.values.get("odds", 1.85)),
        shark_score=float(request.values.get("shark_score", 78)),
        confidence=request.values.get("confidence", "ALTA"),
    )
    return jsonify({"ok": True, "shared_pick": data, "url": f"/share/{data['share_code']}"})


@commercial_v81_bp.route("/api/commercial/event", methods=["GET", "POST"])
def api_commercial_event():
    log_commercial_event(
        request.values.get("event_type", "COMMERCIAL_EVENT"),
        request.values.get("source", "APP"),
        request.values.get("title", "Evento comercial"),
        {"raw": dict(request.values)}
    )
    return jsonify({"ok": True})
