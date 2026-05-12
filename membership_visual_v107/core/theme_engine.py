
MEMBERSHIP_THEMES = {
    "FREE": {
        "name": "FREE",
        "label": "FREE",
        "title": "Acceso básico",
        "color": "#38bdf8",
        "bg": "rgba(56,189,248,0.12)",
        "border": "rgba(56,189,248,0.34)",
        "glow": "rgba(56,189,248,0.20)",
        "description": "Entrada al ecosistema SHARK con funciones básicas.",
        "features": ["Picks limitados", "Partidos básicos", "Panel cliente estándar"],
    },
    "PRO": {
        "name": "PRO",
        "label": "PRO",
        "title": "Plan premium",
        "color": "#00d084",
        "bg": "rgba(0,208,132,0.13)",
        "border": "rgba(0,208,132,0.38)",
        "glow": "rgba(0,208,132,0.24)",
        "description": "Experiencia premium con picks, live y análisis SHARK.",
        "features": ["Picks PRO", "Live Center", "SHARK AI", "Analytics"],
    },
    "ELITE": {
        "name": "ELITE",
        "label": "ELITE",
        "title": "Máximo nivel",
        "color": "#fbbf24",
        "bg": "rgba(251,191,36,0.15)",
        "border": "rgba(251,191,36,0.42)",
        "glow": "rgba(251,191,36,0.28)",
        "description": "Nivel superior para alertas, value avanzado y trato premium.",
        "features": ["Picks ELITE", "Alertas Telegram", "Auto Pick", "Prioridad SHARK"],
    },
    "ADMIN": {
        "name": "ADMIN",
        "label": "ADMIN",
        "title": "Control total",
        "color": "#a78bfa",
        "bg": "rgba(167,139,250,0.14)",
        "border": "rgba(167,139,250,0.40)",
        "glow": "rgba(167,139,250,0.24)",
        "description": "Centro de control interno de NeMeSiS SHARK PRO.",
        "features": ["Admin Center", "Live Ops", "Usuarios", "APIs"],
    },
}

def normalize_plan(plan):
    value = str(plan or "FREE").upper()
    if value in MEMBERSHIP_THEMES:
        return value
    if value in ["VIP", "PREMIUM"]:
        return "PRO"
    return "FREE"

def get_theme(plan):
    return MEMBERSHIP_THEMES[normalize_plan(plan)]

def build_membership_visual_payload(active_plan="PRO"):
    plan = normalize_plan(active_plan)
    return {
        "version": "V107_MEMBERSHIP_VISUAL_PRO",
        "active_plan": plan,
        "active_theme": get_theme(plan),
        "themes": MEMBERSHIP_THEMES,
        "rules": {
            "FREE": "azul básico",
            "PRO": "verde/neón premium",
            "ELITE": "dorado premium",
            "ADMIN": "morado interno"
        }
    }
