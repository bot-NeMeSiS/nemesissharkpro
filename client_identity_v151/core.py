
from datetime import datetime

def normalize_plan(plan):
    value = str(plan or "PRO").upper()
    if value in ["VIP", "PREMIUM"]:
        return "PRO"
    if value not in ["FREE", "PRO", "ELITE", "ADMIN"]:
        return "PRO"
    return value

def client_name_from_session(session):
    for key in ["name", "username", "user_name", "email"]:
        value = session.get(key) if session else None
        if value:
            text = str(value)
            if "@" in text:
                return text.split("@")[0].replace(".", " ").title()
            return text
    return "Damian"

def build_client_identity(session):
    plan = normalize_plan(session.get("membership", session.get("plan", "ELITE")) if session else "ELITE")
    name = client_name_from_session(session or {})
    return {
        "version": "V151_CLIENT_IDENTITY_PRO",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "name": name,
        "plan": plan,
        "membership_label": plan,
        "status": "Activo",
        "avatar": "🦈",
        "greeting": f"Bienvenido, {name}",
        "subtitle": "Tu centro SHARK personalizado",
        "quick_actions": [
            {"label": "Partidos de hoy", "href": "/fixtures/today-pro", "icon": "⚽"},
            {"label": "Mis favoritos", "href": "/cliente/favoritos", "icon": "⭐"},
            {"label": "Home live", "href": "/cliente/home-live-real", "icon": "📡"},
            {"label": "Match Center", "href": "/match-center-real", "icon": "📊"},
            {"label": "SHARK AI", "href": "/cliente/shark-ai", "icon": "🦈"},
            {"label": "Mi cuenta", "href": "/cuenta", "icon": "👤"},
        ],
        "client_nav": [
            {"label": "Inicio", "href": "/cliente/pro", "icon": "🏠"},
            {"label": "Partidos", "href": "/fixtures/today-pro", "icon": "⚽"},
            {"label": "Favoritos", "href": "/cliente/favoritos", "icon": "⭐"},
            {"label": "Live", "href": "/cliente/home-live-real", "icon": "📡"},
            {"label": "SHARK", "href": "/cliente/shark-ai", "icon": "🦈"},
            {"label": "Cuenta", "href": "/cuenta", "icon": "👤"},
        ],
        "admin_hidden": True,
        "no_fake_policy": True
    }
