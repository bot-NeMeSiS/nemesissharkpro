
"""
Rutas V69 ML Center.
Si tu app usa Blueprints, registra ml_bp en app.py:
from ml_foundation.ml_routes import ml_bp
app.register_blueprint(ml_bp)
"""

from flask import Blueprint, jsonify, render_template, send_file
from .learning_engine import get_ml_center_status, rebuild_learning_patterns
from .dataset_export import export_ml_dataset_csv, export_ml_dataset_json

ml_bp = Blueprint("ml_center", __name__)


@ml_bp.route("/admin/ml-center")
def admin_ml_center():
    try:
        status = get_ml_center_status()
    except Exception as exc:
        status = {
            "engine_status": "ERROR",
            "error": str(exc),
            "dataset_size": 0,
            "settled_picks": 0,
            "global_accuracy": 0,
            "global_roi": 0,
            "best_pattern": None,
            "worst_pattern": None,
        }
    return render_template("admin_ml_center.html", status=status)


@ml_bp.route("/api/ml-center")
def api_ml_center():
    return jsonify(get_ml_center_status())


@ml_bp.route("/api/ml-center/rebuild", methods=["POST", "GET"])
def api_ml_rebuild():
    return jsonify(rebuild_learning_patterns())


@ml_bp.route("/api/ml-center/export/csv")
def api_ml_export_csv():
    path = export_ml_dataset_csv()
    return send_file(path, as_attachment=True)


@ml_bp.route("/api/ml-center/export/json")
def api_ml_export_json():
    path = export_ml_dataset_json()
    return send_file(path, as_attachment=True)
