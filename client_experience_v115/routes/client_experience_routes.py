
from flask import Blueprint, render_template, session

client_experience_v115_bp = Blueprint("client_experience_v115", __name__)

@client_experience_v115_bp.route("/cliente/home-pro")
@client_experience_v115_bp.route("/cliente/inicio")
def client_home_pro():
    plan = session.get("membership", "PRO") if session else "PRO"

    highlights = [
        {"title": "Picks destacados", "desc": "Selección premium SHARK.", "href": "/cliente/picks", "icon": "🎯"},
        {"title": "Partidos live", "desc": "Momentum y señales en directo.", "href": "/live-ultra", "icon": "📡"},
        {"title": "SHARK AI", "desc": "Asistente deportivo inteligente.", "href": "/cliente/shark-ai", "icon": "🦈"},
        {"title": "Rendimiento", "desc": "ROI, winrate y banca.", "href": "/cliente/rendimiento", "icon": "📊"},
    ]

    quick = [
        {"label": "Hoy", "href": "/cliente/partidos?filtro=hoy"},
        {"label": "Live", "href": "/live-center-pro"},
        {"label": "Top picks", "href": "/cliente/picks"},
        {"label": "Mi cuenta", "href": "/cuenta"},
    ]

    return render_template(
        "client_home_v115.html",
        plan=plan,
        highlights=highlights,
        quick=quick
    )
