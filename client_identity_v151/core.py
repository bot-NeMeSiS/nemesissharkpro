
from datetime import datetime

def normalize_plan(plan):
    value = str(plan or "PRO").upper()
    if value in ["VIP", "PREMIUM"]:
        return "PRO"
    if value not in ["FREE", "PRO", "ELITE", "ADMIN"]:
        return "PRO"
    return value

def _session_user(session):
    if not session:
        return {}
    user = session.get("user")
    return user if isinstance(user, dict) else session

def client_name_from_session(session):
    data = _session_user(session)
    for key in ["display_name", "name", "username", "user_name", "email"]:
        value = data.get(key) if data else None
        if value:
            text = str(value).strip()
            if not text:
                continue
            if "@" in text:
                return text.split("@")[0].replace(".", " ").title()
            return text
    return "Cliente"

def build_client_identity(session):
    data = _session_user(session or {})
    plan = normalize_plan(data.get("membership", data.get("plan", "FREE")) if data else "FREE")
    name = client_name_from_session(session or {})
    return {
        "version": "V203_SESSION_FIX_MOBILE_UX_REBUILD_PRO",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "name": name,
        "plan": plan,
        "membership_label": plan,
        "status": "Activo",
        "avatar": "🦈",
        "greeting": f"Hola, {name}",
        "subtitle": "Tu app deportiva premium",
        "quick_actions": [
            {"label": "Partidos de hoy", "href": "/fixtures/today-pro", "icon": "⚽"},
            {"label": "Mis favoritos", "href": "/cliente/favoritos", "icon": "⭐"},
            {"label": "En directo", "href": "/cliente/home-live-real", "icon": "🔥"},
            {"label": "Match Center", "href": "/match-center-real", "icon": "📊"},
            {"label": "SHARK AI", "href": "/cliente/shark-ai", "icon": "🦈"},
            {"label": "Mi cuenta", "href": "/cuenta", "icon": "👤"},
        ],
        "client_nav": [
            {"label": "Inicio", "href": "/cliente/pro", "icon": "🏠"},
            {"label": "Picks", "href": "/picks", "icon": "🎯"},
            {"label": "Live", "href": "/cliente/home-live-real", "icon": "🔥"},
            {"label": "Favoritos", "href": "/cliente/favoritos", "icon": "⭐"},
            {"label": "Cuenta", "href": "/cuenta", "icon": "👤"},
        ],
        "admin_hidden": True,
        "no_fake_policy": True
    }
