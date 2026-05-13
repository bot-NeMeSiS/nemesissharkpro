
"""
Rutas V70 Visual Premium.
Registrar en app.py:
from ui_v70.routes import ui_v70_bp
app.register_blueprint(ui_v70_bp)
"""

from flask import Blueprint, jsonify, render_template
from .visual_status import get_visual_v70_status

ui_v70_bp = Blueprint("ui_v70", __name__)


@ui_v70_bp.route("/admin/visual-v70")
def admin_visual_v70():
    return render_template("admin_visual_v70.html", status=get_visual_v70_status())


@ui_v70_bp.route("/api/visual-v70")
def api_visual_v70():
    return jsonify(get_visual_v70_status())
