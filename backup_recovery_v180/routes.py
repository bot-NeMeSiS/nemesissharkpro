from flask import Blueprint, jsonify, render_template, request, send_file
from datetime import datetime
from pathlib import Path
import os, sqlite3, zipfile, json

backup_recovery_v180_bp = Blueprint('backup_recovery_v180_bp', __name__)

def _now():
    return datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'

def _db_candidates():
    return [os.environ.get('DATABASE_PATH'), os.environ.get('DB_PATH'), '/data/app.db', '/data/database.db', 'app.db', 'database.db']

def _db_path():
    for p in _db_candidates():
        if p and Path(p).exists():
            return Path(p)
    fallback = os.environ.get('DATABASE_PATH') or os.environ.get('DB_PATH') or '/data/app.db'
    try:
        Path(fallback).parent.mkdir(parents=True, exist_ok=True)
        return Path(fallback)
    except Exception:
        return Path('app.db')

def _backup_dir():
    raw = os.environ.get('BACKUP_DIR') or '/data/backups'
    try:
        p = Path(raw); p.mkdir(parents=True, exist_ok=True); return p
    except Exception:
        p = Path('backups'); p.mkdir(parents=True, exist_ok=True); return p

def _connect():
    con = sqlite3.connect(str(_db_path()), timeout=8)
    con.row_factory = sqlite3.Row
    return con

def _init_db():
    try:
        con = _connect()
        con.execute("""CREATE TABLE IF NOT EXISTS backup_events_v180 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT,
            status TEXT,
            message TEXT,
            file_path TEXT,
            size_bytes INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        con.commit(); con.close()
    except Exception:
        pass

def _log(event_type, status, message, file_path='', size=0):
    try:
        _init_db(); con = _connect()
        con.execute('INSERT INTO backup_events_v180(event_type,status,message,file_path,size_bytes,created_at) VALUES(?,?,?,?,?,?)',
                    (event_type, status, message, file_path, int(size or 0), _now()))
        con.commit(); con.close()
    except Exception:
        pass

def _list_backups():
    d = _backup_dir(); rows = []
    for p in sorted(d.glob('nemesis_backup_*.zip'), key=lambda x: x.stat().st_mtime, reverse=True):
        rows.append({'name': p.name, 'path': str(p), 'size_bytes': p.stat().st_size, 'size_mb': round(p.stat().st_size/1024/1024, 2), 'created_at': datetime.utcfromtimestamp(p.stat().st_mtime).isoformat()+'Z'})
    return rows

def _counts():
    db = _db_path(); out = {}
    if not db.exists():
        return out
    try:
        con = sqlite3.connect(str(db)); con.row_factory = sqlite3.Row
        for table in ('users','picks','fixtures','matches','telegram_users','telegram_delivery_logs','automation_runs_v178','notification_queue','backup_events_v180'):
            try:
                exists = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
                out[table] = int(con.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]) if exists else None
            except Exception:
                out[table] = None
        con.close()
    except Exception as exc:
        out['error'] = str(exc)
    return out

def create_backup(label='manual'):
    _init_db()
    db = _db_path(); d = _backup_dir()
    stamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    safe = ''.join(c for c in str(label or 'manual') if c.isalnum() or c in ('-','_'))[:32] or 'manual'
    out = d / f'nemesis_backup_v180_{safe}_{stamp}.zip'
    if not db.exists():
        _log('backup','error','No se encontró la base de datos',str(db),0)
        return {'ok': False, 'error': 'database_not_found', 'db_path': str(db)}
    try:
        with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            z.write(db, arcname=db.name)
            meta = {'version':'V180','created_at':_now(),'db_path':str(db),'label':safe,'counts':_counts()}
            z.writestr('backup_meta_v180.json', json.dumps(meta, ensure_ascii=False, indent=2))
        size = out.stat().st_size
        _log('backup','ok','Backup creado correctamente',str(out),size)
        return {'ok': True, 'backup': {'name': out.name, 'path': str(out), 'size_bytes': size, 'size_mb': round(size/1024/1024, 2)}}
    except Exception as exc:
        _log('backup','error',str(exc),str(out),0)
        return {'ok': False, 'error': str(exc)}

def build_status():
    db = _db_path(); backups = _list_backups()
    db_size = db.stat().st_size if db.exists() else 0
    return {
        'version': 'V180', 'generated_at': _now(),
        'database': {'path': str(db), 'exists': db.exists(), 'size_bytes': db_size, 'size_mb': round(db_size/1024/1024, 2)},
        'backup_dir': str(_backup_dir()), 'backups': backups[:12], 'backup_count': len(backups),
        'counts': _counts(),
        'production_hardening': {
            'persistent_disk': 'OK si DB_PATH/DATABASE_PATH apunta a /data/*.db',
            'backups': 'Activos con BACKUP_DIR, recomendado /data/backups',
            'secret_key': 'OK' if os.environ.get('SECRET_KEY') else 'Pendiente configurar SECRET_KEY real',
            'telegram_admin': 'OK' if os.environ.get('TELEGRAM_ADMIN_CHAT_ID') else 'Pendiente TELEGRAM_ADMIN_CHAT_ID',
            'automation_secret': 'OK' if os.environ.get('AUTOMATION_SECRET') else 'Pendiente AUTOMATION_SECRET',
        },
        'recommendations': [
            'Crear backup antes de cada deploy grande.',
            'Mantener BACKUP_DIR en disco persistente de Render.',
            'No subir backups al repo; se quedan en /data/backups.',
            'Configurar cron externo contra /api/v180/backup/create con X-Automation-Secret.',
        ]
    }

def _authorized():
    secret = os.environ.get('AUTOMATION_SECRET') or os.environ.get('BACKUP_SECRET')
    if not secret:
        return True
    supplied = request.headers.get('X-Automation-Secret') or request.args.get('secret') or request.form.get('secret')
    return supplied == secret

@backup_recovery_v180_bp.route('/admin/backup-recovery')
@backup_recovery_v180_bp.route('/admin/backups')
@backup_recovery_v180_bp.route('/admin/production-hardening')
def backup_page():
    return render_template('v180/backup_recovery.html', data=build_status())

@backup_recovery_v180_bp.route('/api/v180/backup/status')
def api_backup_status():
    return jsonify({'ok': True, 'data': build_status()})

@backup_recovery_v180_bp.route('/api/v180/backup/create', methods=['GET','POST'])
def api_backup_create():
    if not _authorized():
        return jsonify({'ok': False, 'error': 'unauthorized'}), 401
    return jsonify(create_backup(request.values.get('label') or 'manual'))

@backup_recovery_v180_bp.route('/api/v180/backup/list')
def api_backup_list():
    return jsonify({'ok': True, 'backups': _list_backups()})

@backup_recovery_v180_bp.route('/api/v180/backup/download-latest')
def api_backup_download_latest():
    backups = _list_backups()
    if not backups:
        return jsonify({'ok': False, 'error': 'no_backups'}), 404
    return send_file(backups[0]['path'], as_attachment=True, download_name=backups[0]['name'])

@backup_recovery_v180_bp.route('/api/v180/backup/cleanup', methods=['POST','GET'])
def api_backup_cleanup():
    if not _authorized():
        return jsonify({'ok': False, 'error': 'unauthorized'}), 401
    keep = int(request.values.get('keep') or 10)
    removed = []
    for b in _list_backups()[keep:]:
        try:
            Path(b['path']).unlink(missing_ok=True); removed.append(b['name'])
        except Exception:
            pass
    _log('cleanup','ok',f'Limpieza backups, eliminados {len(removed)}','',0)
    return jsonify({'ok': True, 'removed': removed, 'keep': keep})
