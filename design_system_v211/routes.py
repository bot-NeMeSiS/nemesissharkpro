
from flask import Blueprint, jsonify, render_template
from datetime import datetime

bp_design_system_v211 = Blueprint('design_system_v211', __name__)

TOKENS = {
    'colores': {
        'fondo': '#050817', 'panel': '#0b1224', 'borde': 'rgba(148,163,184,.22)',
        'texto': '#f8fafc', 'muted': '#94a3b8', 'accent': '#22d3ee',
        'free': '#38bdf8', 'pro': '#2563eb', 'elite': '#facc15', 'danger': '#fb7185', 'ok': '#34d399'
    },
    'componentes': ['botones', 'cards', 'badges', 'headers', 'navbar movil', 'estados live', 'confianza', 'riesgo'],
    'reglas': [
        'Un solo lenguaje visual para cliente y admin.',
        'Texto cliente sin versiones técnicas ni mensajes internos.',
        'Estados claros: En directo, Próximo, Finalizado, Pendiente de datos.',
        'FREE/PRO/ELITE mantienen color propio sin romper legibilidad.',
        'Móvil primero: cards compactas, navegación limpia y acciones rápidas.'
    ]
}

@bp_design_system_v211.route('/api/v211/design-system/status')
def api_design_system_status():
    return jsonify({
        'version': 'V211',
        'nombre': 'Design System SHARK PRO',
        'estado': 'activo',
        'tokens': TOKENS,
        'fecha': datetime.utcnow().isoformat(timespec='seconds') + 'Z'
    })

@bp_design_system_v211.route('/admin/design-system')
@bp_design_system_v211.route('/admin/design-system-v211')
def admin_design_system_v211():
    return render_template('design_system_v211_admin.html', tokens=TOKENS)

@bp_design_system_v211.route('/cliente/design-system')
def cliente_design_system_v211():
    return render_template('design_system_v211_client.html', tokens=TOKENS)
