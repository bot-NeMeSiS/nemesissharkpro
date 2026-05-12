
from pathlib import Path
from datetime import datetime

def build_architecture_split_status():
    modules = [
        "admin_center_v105",
        "live_ops_v106",
        "membership_visual_v107",
        "client_ux_v108",
        "live_intelligence_v109",
        "pro_architecture_v110",
        "combined_v114",
        "client_experience_v115",
        "real_data_v116",
        "telegram_pro_v117",
        "product_control_v119",
        "mega_v125",
    ]

    app_lines = 0
    app_file = Path("app.py")
    if app_file.exists():
        app_lines = len(app_file.read_text(encoding="utf-8", errors="ignore").splitlines())

    return {
        "version": "V120_APP_SPLIT_ENGINE",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "app_py_lines": app_lines,
        "modules": [{"name": m, "exists": Path(m).exists()} for m in modules],
        "strategy": [
            "No tocar rutas legacy que funcionan.",
            "Añadir nuevas funciones por blueprints separados.",
            "Mantener Render estable.",
            "Preparar limpieza profunda futura de app.py sin romper cliente.",
        ],
        "status": "safe_split_ready"
    }
