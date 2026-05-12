
def client_final_payload(plan="PRO"):
    plan = str(plan or "PRO").upper()
    if plan in ["VIP", "PREMIUM"]:
        plan = "PRO"
    return {
        "version": "V129_CLIENT_EXPERIENCE_FINAL",
        "plan": plan,
        "navigation": [
            {"label": "Inicio", "href": "/cliente/final", "icon": "🏠"},
            {"label": "Picks", "href": "/cliente/picks", "icon": "🎯"},
            {"label": "Live", "href": "/live-center-pro-final", "icon": "📡"},
            {"label": "SHARK AI", "href": "/cliente/shark-ai", "icon": "🦈"},
            {"label": "Cuenta", "href": "/cuenta", "icon": "👤"},
        ],
        "quick_actions": [
            {"label": "Partidos de hoy", "href": "/cliente/partidos?filtro=hoy"},
            {"label": "Picks activos", "href": "/cliente/picks"},
            {"label": "Live ahora", "href": "/live-center-pro-final"},
            {"label": "Cerrar sesión", "href": "/logout"},
        ]
    }
