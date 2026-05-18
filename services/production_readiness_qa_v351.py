
QA_CHECKS = [
    {"area": "Cliente", "route": "/cliente/pro", "status": "review"},
    {"area": "Navegación", "route": "/api/client/navigation-audit/status-v349", "status": "review"},
    {"area": "Experiencia final", "route": "/api/client/experience-final/status-v350", "status": "review"},
    {"area": "Datos reales", "route": "/api/real-data/pipeline/status-v346", "status": "review"},
    {"area": "Normalizador live", "route": "/api/live/normalizer/status-v347", "status": "review"},
    {"area": "UI datos", "route": "/api/client/real-data-ui/status-v348", "status": "review"},
    {"area": "1X2", "route": "/cliente/1x2", "status": "review"},
    {"area": "Membresías", "route": "/cliente/membresia", "status": "review"},
    {"area": "Telegram", "route": "/api/telegram/linked-chats-v317", "status": "review"},
    {"area": "Launch", "route": "/api/launch/status-v330", "status": "review"},
]

def qa_status():
    return {
        "ok": True,
        "version": "V351",
        "name": "PRODUCTION_READINESS_QA_CENTER_PRO",
        "commercial_state": "beta premium controlada",
        "checks": QA_CHECKS,
        "manual_review_needed": [
            "probar login cliente",
            "probar registro",
            "probar mobile desde iPhone",
            "probar Render env vars",
            "probar Telegram /start",
            "probar 1X2 con THE_ODDS_API_KEY real"
        ],
        "recommended_next": "Release candidate clean package",
        "real_only": True
    }
