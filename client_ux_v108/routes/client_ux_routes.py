
from flask import Blueprint, jsonify, render_template, redirect, session, request
from client_ux_v108.core.client_nav import get_client_navigation

client_ux_v108_bp = Blueprint("client_ux_v108", __name__)

@client_ux_v108_bp.route("/api/v108/client/navigation")
def client_navigation_api():
    plan = request.args.get("plan", session.get("membership", "PRO") if session else "PRO")
    return jsonify(get_client_navigation(plan))

@client_ux_v108_bp.route("/cliente/cuenta")
@client_ux_v108_bp.route("/mi-cuenta")
def client_account_page():
    plan = session.get("membership", "PRO") if session else "PRO"
    payload = get_client_navigation(plan)
    return render_template("client_account_v108.html", payload=payload)

@client_ux_v108_bp.route("/cliente/shark-ai")
def client_shark_ai_page():
    plan = session.get("membership", "PRO") if session else "PRO"
    payload = get_client_navigation(plan)
    return render_template("client_shark_ai_v108.html", payload=payload)

@client_ux_v108_bp.route("/cliente/menu")
def client_menu_page():
    plan = session.get("membership", "PRO") if session else "PRO"
    payload = get_client_navigation(plan)
    return render_template("client_menu_v108.html", payload=payload)

@client_ux_v108_bp.route("/logout")
@client_ux_v108_bp.route("/salir")
@client_ux_v108_bp.route("/cerrar-sesion")
def logout_v108():
    try:
        session.clear()
    except Exception:
        pass
    return redirect("/")
