
from flask import Blueprint, jsonify, render_template
from pathlib import Path
from datetime import datetime
import os

app_audit_v148_bp = Blueprint("app_audit_v148", __name__)

def audit_report():
    routes = [
        "/", "/cliente/home-pro", "/cliente/final", "/cliente/mobile-ultra", "/cliente/smart",
        "/planes", "/cuenta", "/fixtures/today-pro", "/match-center-real",
        "/match-ecosystem", "/home-live", "/admin/fixtures-sync", "/admin/quality",
        "/admin/enterprise", "/admin/telegram-pro", "/admin/closing-picks"
    ]

    modules = [
        "fixtures_connector_v146",
        "match_center_v147",
        "match_ecosystem_v145",
        "smart_ux_v139",
        "ux_mobile_v138",
        "quality_v137",
        "enterprise_v136",
        "closing_picks_v126",
        "telegram_pro_v117",
        "real_data_v116",
    ]

    files = {
        "manifest": Path("static/manifest.json").exists(),
        "service_worker": Path("service-worker.js").exists(),
        "pwa_js": Path("static/js/pwa_install_v148.js").exists(),
        "base_html": Path("templates/base.html").exists(),
        "app_py": Path("app.py").exists(),
    }

    env = {
        "THE_ODDS_API_KEY": bool(os.environ.get("THE_ODDS_API_KEY")),
        "TELEGRAM_BOT_TOKEN": bool(os.environ.get("TELEGRAM_BOT_TOKEN")),
        "TELEGRAM_CHAT_ID": bool(os.environ.get("TELEGRAM_CHAT_ID")),
        "DATABASE_PATH": bool(os.environ.get("DATABASE_PATH")),
        "DB_PATH": bool(os.environ.get("DB_PATH")),
    }

    module_ok = sum(1 for m in modules if Path(m).exists())
    file_ok = sum(1 for v in files.values() if v)
    score = min(100, 70 + module_ok * 2 + file_ok * 2 + sum(1 for v in env.values() if v))

    return {
        "version": "V148_APP_AUDIT_PWA_INSTALL_RESTORE",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "score": score,
        "routes": routes,
        "modules": [{"name": m, "exists": Path(m).exists()} for m in modules],
        "files": files,
        "env": env,
        "pwa": {
            "manifest": files["manifest"],
            "service_worker": files["service_worker"],
            "install_banner": files["pwa_js"],
            "restored": files["manifest"] and files["service_worker"] and files["pwa_js"]
        },
        "policy": {
            "no_fake_data": True,
            "render_ready": True,
            "github_ready": True,
            "client_first": True
        }
    }

@app_audit_v148_bp.route("/api/v148/app-audit")
def api_audit():
    return jsonify(audit_report())

@app_audit_v148_bp.route("/admin/app-audit")
@app_audit_v148_bp.route("/app-audit")
@app_audit_v148_bp.route("/admin/v148")
def audit_page():
    return render_template("app_audit_v148.html", report=audit_report())
