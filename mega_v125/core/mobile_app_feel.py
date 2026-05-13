
def mobile_payload():
    return {
        "version": "V124_MOBILE_APP_FEEL",
        "navigation": [
            {"label": "Inicio", "href": "/cliente/home-pro", "icon": "🏠"},
            {"label": "Picks", "href": "/cliente/picks", "icon": "🎯"},
            {"label": "Live", "href": "/live-ultra", "icon": "📡"},
            {"label": "AI", "href": "/cliente/shark-ai", "icon": "🦈"},
            {"label": "Cuenta", "href": "/cuenta", "icon": "👤"},
        ],
        "features": ["bottom_nav", "pwa_ready", "premium_empty_states", "safe_logout"]
    }
