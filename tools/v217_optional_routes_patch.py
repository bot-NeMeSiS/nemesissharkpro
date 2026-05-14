# Rutas opcionales V217 para copiar en app.py si no se registran automáticamente.
# Mantener en español y REAL ONLY.

from flask import render_template

def register_v217_qa_routes(app):
    @app.route('/admin/quality-audit')
    @app.route('/admin/qa-v217')
    def admin_quality_audit_v217():
        return render_template('qa_v217.html')
