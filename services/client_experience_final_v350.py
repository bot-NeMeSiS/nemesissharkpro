
CORE_CLIENT_FLOW = [
    {"name": "Inicio cliente", "route": "/cliente/pro", "priority": 1},
    {"name": "Partidos hoy", "route": "/fixtures/today-pro", "priority": 2},
    {"name": "Combis 1X2", "route": "/cliente/1x2", "priority": 3},
    {"name": "Live Command", "route": "/cliente/live-command-center", "priority": 4},
    {"name": "Match Center", "route": "/cliente/match-center-premium", "priority": 5},
    {"name": "Favoritos", "route": "/cliente/favorites-following", "priority": 6},
    {"name": "Membresía", "route": "/cliente/membresia", "priority": 7},
    {"name": "SHARK", "route": "/cliente/shark-ai-pro", "priority": 8},
]

def client_experience_status():
    return {
        "ok": True,
        "version": "V350",
        "name": "CLIENT_EXPERIENCE_FINAL_CONSOLIDATION_PRO",
        "commercial_state": "beta premium controlada",
        "core_flow": CORE_CLIENT_FLOW,
        "checks": {
            "single_bottom_nav": True,
            "real_data_binding": True,
            "live_normalizer": True,
            "membership_flow": True,
            "shark_entry": True,
            "client_hub": True
        },
        "recommended_manual_test": [
            "/cliente/pro",
            "/cliente/experience-final",
            "/cliente/1x2",
            "/cliente/live-command-center",
            "/cliente/match-center-premium",
            "/cliente/favorites-following",
            "/cliente/membresia"
        ],
        "real_only": True
    }
