
import os
from pathlib import Path
from datetime import datetime

def path_status(path):
    p = Path(path)
    return {
        "path": str(path),
        "exists": p.exists(),
        "is_dir": p.is_dir() if p.exists() else False,
        "is_file": p.is_file() if p.exists() else False,
    }

def build_diagnostics():
    app_file = Path("app.py")
    app_lines = 0
    if app_file.exists():
        try:
            app_lines = len(app_file.read_text(encoding="utf-8", errors="ignore").splitlines())
        except Exception:
            app_lines = 0

    modules = [
        "admin_center_v105",
        "live_ops_v106",
        "membership_visual_v107",
        "client_ux_v108",
        "live_intelligence_v109",
        "pro_architecture_v110",
        "auto_pick_v104",
    ]

    module_status = []
    for module in modules:
        p = Path(module)
        module_status.append({
            "module": module,
            "exists": p.exists(),
            "status": "OK" if p.exists() else "MISSING",
        })

    env_keys = [
        "THE_ODDS_API_KEY",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "OPENAI_API_KEY",
        "DATABASE_PATH",
        "DB_PATH",
        "RENDER_EXTERNAL_URL",
    ]

    env = [{"name": k, "configured": bool(os.environ.get(k))} for k in env_keys]

    architecture_score = 70
    architecture_score += min(15, sum(1 for m in module_status if m["exists"]) * 2)
    if app_lines and app_lines > 4500:
        architecture_score -= 8
    if app_lines and app_lines > 7000:
        architecture_score -= 8
    architecture_score = max(0, min(100, architecture_score))

    return {
        "version": "V110_PRO_ARCHITECTURE",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "architecture_score": architecture_score,
        "app_py_lines": app_lines,
        "modules": module_status,
        "env": env,
        "paths": [
            path_status("templates"),
            path_status("static"),
            path_status("public"),
            path_status("/data"),
        ],
        "recommendations": [
            "Mantener app.py estable y no añadir lógica pesada nueva directamente ahí.",
            "Seguir creando módulos separados por versión/función.",
            "Siguiente salto recomendado: V111 Telegram PRO REAL o limpieza profunda por blueprints.",
        ],
    }
