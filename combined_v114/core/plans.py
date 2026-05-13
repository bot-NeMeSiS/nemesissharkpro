
PLANS = {
    "FREE": {
        "price": "0€",
        "title": "FREE",
        "color": "free",
        "description": "Acceso básico para probar SHARK PRO.",
        "features": ["Partidos básicos", "Picks limitados", "Panel cliente"],
    },
    "PRO": {
        "price": "Premium",
        "title": "PRO",
        "color": "pro",
        "description": "Plan premium para picks, live y SHARK AI.",
        "features": ["Picks PRO", "Live Center", "SHARK AI", "Rendimiento"],
    },
    "ELITE": {
        "price": "Top",
        "title": "ELITE",
        "color": "elite",
        "description": "Máximo nivel para señales, alertas y value avanzado.",
        "features": ["Picks ELITE", "Auto Pick", "Alertas", "Prioridad SHARK"],
    },
}

def plans_payload():
    return {"version": "V114", "plans": PLANS}
