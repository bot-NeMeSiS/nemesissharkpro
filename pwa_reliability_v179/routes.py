from flask import Blueprint, jsonify, render_template, request
from pathlib import Path
from datetime import datetime
import os, json

pwa_reliability_v179_bp = Blueprint('pwa_reliability_v179_bp', __name__)
ROOT = Path(__file__).resolve().parent.parent

def _exists(path):
    try: return Path(path).exists()
    except Exception: return False

def build_pwa_report():
    manifest_root = ROOT / 'manifest.json'
    manifest_static = ROOT / 'static' / 'manifest.json'
    service_worker = ROOT / 'service-worker.js'
    icon_192 = ROOT / 'static' / 'icons' / 'icon-192.png'
    icon_512 = ROOT / 'static' / 'icons' / 'icon-512.png'
    manifest = {}
    source = None
    for p in (manifest_root, manifest_static):
        if p.exists():
            try:
                manifest = json.loads(p.read_text(encoding='utf-8'))
                source = str(p.name if p == manifest_root else 'static/manifest.json')
                break
            except Exception:
                pass
    start_url = manifest.get('start_url') or ''
    display = manifest.get('display') or ''
    icons = manifest.get('icons') or []
    problems = []
    if not manifest_root.exists(): problems.append('Falta manifest.json raíz. Chrome PC suele necesitarlo para /manifest.json.')
    if not service_worker.exists(): problems.append('Falta service-worker.js raíz.')
    if display not in ('standalone','fullscreen','minimal-ui'): problems.append('Manifest display no está en modo instalable.')
    if not start_url: problems.append('Manifest sin start_url.')
    if not icon_192.exists() or not icon_512.exists(): problems.append('Faltan iconos 192/512 para instalación.')
    if not problems: problems.append('PWA lista. Si Chrome no muestra instalar, limpiar caché/site data o entrar por HTTPS en Render.')
    return {
        'ok': True,
        'version': 'V179_PWA_INSTALL_RELIABILITY_AND_PUSH_FULL',
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'files': {
            'manifest_root': manifest_root.exists(),
            'manifest_static': manifest_static.exists(),
            'service_worker': service_worker.exists(),
            'icon_192': icon_192.exists(),
            'icon_512': icon_512.exists()
        },
        'manifest': {
            'source': source,
            'name': manifest.get('name'),
            'short_name': manifest.get('short_name'),
            'start_url': start_url,
            'scope': manifest.get('scope'),
            'display': display,
            'icons_count': len(icons),
            'shortcuts_count': len(manifest.get('shortcuts') or [])
        },
        'install_rules': {
            'https_required': True,
            'beforeinstallprompt_required_for_button': True,
            'hidden_when_standalone': True,
            'hidden_after_dismiss': True,
            'manual_fallback_pc': 'Chrome/Edge: icono instalar en barra o menú ⋮ > Guardar y compartir > Instalar página como aplicación',
            'manual_fallback_mobile': 'Chrome móvil: menú ⋮ > Añadir a pantalla de inicio / Instalar app'
        },
        'problems_or_notes': problems,
        'push': {
            'foundation_ready': True,
            'vapid_public_key': bool(os.environ.get('VAPID_PUBLIC_KEY')),
            'vapid_private_key': bool(os.environ.get('VAPID_PRIVATE_KEY')),
            'telegram_admin_chat_id': bool(os.environ.get('TELEGRAM_ADMIN_CHAT_ID')),
            'telegram_channel_chat_id': bool(os.environ.get('TELEGRAM_CHAT_ID'))
        }
    }

@pwa_reliability_v179_bp.route('/api/v179/pwa-install-status')
def api_pwa_install_status():
    return jsonify(build_pwa_report())

@pwa_reliability_v179_bp.route('/api/v179/app-install-health')
def api_app_install_health():
    return jsonify(build_pwa_report())

@pwa_reliability_v179_bp.route('/admin/pwa-install')
@pwa_reliability_v179_bp.route('/admin/app-install')
@pwa_reliability_v179_bp.route('/admin/pwa-health')
def page_pwa_install():
    return render_template('v179/pwa_install_reliability.html', data=build_pwa_report())
