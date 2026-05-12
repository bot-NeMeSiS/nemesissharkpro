
def get_client_navigation(plan="PRO"):
    plan = str(plan or "PRO").upper()
    if plan in ["VIP", "PREMIUM"]:
        plan = "PRO"

    base = [
        {"label": "Inicio", "href": "/cliente", "icon": "🏠", "admin_only": False},
        {"label": "Picks", "href": "/cliente/picks", "icon": "🎯", "admin_only": False},
        {"label": "Partidos", "href": "/cliente/partidos", "icon": "⚽", "admin_only": False},
        {"label": "En directo", "href": "/en-directo", "icon": "📡", "admin_only": False},
        {"label": "Rendimiento", "href": "/cliente/rendimiento", "icon": "📊", "admin_only": False},
        {"label": "SHARK AI", "href": "/cliente/shark-ai", "icon": "🦈", "admin_only": False},
        {"label": "Cuenta", "href": "/cliente/cuenta", "icon": "👤", "admin_only": False},
    ]

    quick = [
        {"label": "Partidos de hoy", "href": "/cliente/partidos?filtro=hoy", "icon": "🔥"},
        {"label": "Picks activos", "href": "/cliente/picks?estado=activos", "icon": "🎯"},
        {"label": "Live ahora", "href": "/en-directo", "icon": "📡"},
        {"label": "Mi rendimiento", "href": "/cliente/rendimiento", "icon": "📊"},
    ]

    account = [
        {"label": "Mi cuenta", "href": "/cliente/cuenta", "icon": "👤"},
        {"label": "Plan actual", "href": "/cliente/cuenta#plan", "icon": "⭐"},
        {"label": "Preferencias", "href": "/cliente/cuenta#preferencias", "icon": "⚙️"},
        {"label": "Cerrar sesión", "href": "/logout", "icon": "🚪", "danger": True},
    ]

    return {
        "plan": plan,
        "navigation": base,
        "quick_actions": quick,
        "account_actions": account,
        "client_safe_labels": {
            "no_admin_text": True,
            "no_debug_text": True,
            "no_fake_demo": True,
            "spanish_first": True,
        }
    }

def clean_client_copy(text):
    if not text:
        return text
    replacements = {
        "demo": "",
        "Demo": "",
        "DEBUG": "",
        "debug": "",
        "admin": "sistema",
        "Admin": "Sistema",
        "API": "datos",
        "endpoint": "acceso",
        "mock": "",
        "fake": "",
    }
    result = str(text)
    for old, new in replacements.items():
        result = result.replace(old, new)
    return " ".join(result.split())
