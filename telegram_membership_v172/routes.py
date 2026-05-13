from flask import Blueprint, jsonify, render_template, request, redirect, session
from datetime import datetime
from pathlib import Path
import os, sqlite3, html

try:
    import requests
except Exception:
    requests = None

telegram_membership_v172_bp = Blueprint('telegram_membership_v172_bp', __name__)
VERSION = 'V172_TELEGRAM_MEMBERSHIP_DELIVERY_PRO'

PLAN_RULES = {
    'FREE': {
        'label': 'FREE', 'emoji': '🔵', 'limit': 2, 'min_score': 82,
        'features': ['Partidos reales destacados', 'Resumen básico', 'Sin análisis premium completo'],
        'title': 'NeMeSiS FREE — resumen real'
    },
    'PRO': {
        'label': 'PRO', 'emoji': '🟢', 'limit': 5, 'min_score': 68,
        'features': ['Picks PRO', 'stake sugerido', 'riesgo', 'Match Center', 'favoritos'],
        'title': 'NeMeSiS PRO — señales premium'
    },
    'ELITE': {
        'label': 'ELITE', 'emoji': '🟡', 'limit': 8, 'min_score': 0,
        'features': ['Todo PRO', 'SHARK avanzado', 'top picks', 'alertas live', 'explicación completa'],
        'title': 'NeMeSiS ELITE — modo máximo'
    },
    'ADMIN': {
        'label': 'ADMIN', 'emoji': '👑', 'limit': 12, 'min_score': 0,
        'features': ['Todo el sistema', 'PRO + ELITE', 'errores', 'diagnóstico', 'partidos reales'],
        'title': 'NeMeSiS ADMIN — control total'
    },
}


def _is_admin():
    role = str(session.get('role') or session.get('user_role') or '').lower()
    user = str(session.get('username') or session.get('user') or session.get('admin') or '').lower()
    return bool(session.get('is_admin') or session.get('admin_logged_in') or role == 'admin' or user == 'admin')


def _db_path():
    for raw in [os.environ.get('DATABASE_PATH'), os.environ.get('DB_PATH'), '/data/app.db', '/data/database.db', 'app.db', 'database.db']:
        if raw and Path(raw).exists():
            return str(Path(raw))
    return None


def _connect():
    path = _db_path()
    if not path:
        return None, None
    try:
        con = sqlite3.connect(path)
        con.row_factory = sqlite3.Row
        return con, path
    except Exception:
        return None, path


def _table_exists(con, table):
    if not con:
        return False
    try:
        return bool(con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone())
    except Exception:
        return False


def _columns(con, table):
    try:
        return [r[1] for r in con.execute(f"PRAGMA table_info({table})").fetchall()]
    except Exception:
        return []


def _ensure_tables(con):
    if not con:
        return
    try:
        con.execute('''CREATE TABLE IF NOT EXISTS telegram_delivery_log_v172 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            target_chat_id TEXT,
            target_plan TEXT,
            target_user_id TEXT,
            mode TEXT,
            status TEXT,
            message_preview TEXT,
            telegram_response TEXT,
            error TEXT
        )''')
        con.execute('''CREATE TABLE IF NOT EXISTS telegram_delivery_state_v172 (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT NOT NULL
        )''')
        con.commit()
    except Exception:
        pass


def _scalar(con, sql, params=(), default=0):
    try:
        row = con.execute(sql, params).fetchone()
        return list(row)[0] if row else default
    except Exception:
        return default


def _normalize_plan(plan):
    p = str(plan or 'FREE').upper().strip()
    if p in ('VIP', 'PREMIUM'):
        p = 'PRO'
    if p not in ('FREE', 'PRO', 'ELITE', 'ADMIN'):
        p = 'FREE'
    return p


def _read_users(con):
    if not con or not _table_exists(con, 'users'):
        return []
    cols = _columns(con, 'users')
    select_cols = []
    for c in ['id','username','email','role','plan','membership','telegram_chat_id','telegram_username','telegram_alerts_enabled']:
        if c in cols:
            select_cols.append(c)
    if not select_cols:
        return []
    try:
        rows = con.execute(f"SELECT {','.join(select_cols)} FROM users ORDER BY id DESC LIMIT 1000").fetchall()
    except Exception:
        return []
    users = []
    for r in rows:
        d = dict(r)
        plan = d.get('plan') or d.get('membership') or d.get('role') or 'FREE'
        role = str(d.get('role') or '').upper()
        users.append({
            'id': d.get('id'),
            'username': d.get('username') or d.get('email') or f"user-{d.get('id')}",
            'plan': _normalize_plan('ADMIN' if role == 'ADMIN' else plan),
            'telegram_chat_id': str(d.get('telegram_chat_id') or '').strip(),
            'telegram_username': d.get('telegram_username') or '',
            'alerts_enabled': bool(d.get('telegram_alerts_enabled', 1)),
        })
    return users


def _first_value(d, keys, default=''):
    for k in keys:
        if k in d and d.get(k) not in (None, ''):
            return d.get(k)
    return default


def _read_real_items(con, limit=30):
    if not con:
        return []
    tables = ['picks','value_picks','manual_picks','fixtures','real_fixtures','matches_cache','fixtures_cache','odds_cache']
    items = []
    for table in tables:
        if not _table_exists(con, table):
            continue
        cols = _columns(con, table)
        try:
            order = 'rowid DESC'
            for c in ['start_time','commence_time','date','created_at','updated_at']:
                if c in cols:
                    order = f"{c} DESC"
                    break
            rows = con.execute(f"SELECT * FROM {table} ORDER BY {order} LIMIT ?", (limit,)).fetchall()
        except Exception:
            continue
        for row in rows:
            d = dict(row)
            home = _first_value(d, ['home_team','home','team_home','local','home_name','team1','equipo_local'])
            away = _first_value(d, ['away_team','away','team_away','visitor','away_name','team2','equipo_visitante'])
            title = _first_value(d, ['title','name','event','match_name','fixture','pick_title'])
            if not title and (home or away):
                title = f"{home or 'Local'} vs {away or 'Visitante'}"
            if not title:
                continue
            market = _first_value(d, ['market','selection','pick','bet','recommendation','tip','prediction'], 'Mercado no especificado')
            league = _first_value(d, ['league','competition','sport_title','sport','liga'], 'Competición real')
            odds = _first_value(d, ['odds','price','quota','cuota','best_odd'], '')
            status = _first_value(d, ['status','state','match_status'], '')
            score_raw = _first_value(d, ['score','shark_score','confidence','value_score','rating'], 0)
            try:
                score = int(float(score_raw))
            except Exception:
                score = 0
            risk = _first_value(d, ['risk','riesgo'], 'Medio')
            stake = _first_value(d, ['stake','stake_pct','stake_percent'], '')
            start = _first_value(d, ['start_time','commence_time','date','match_date','created_at','updated_at'], '')
            item_id = _first_value(d, ['id','fixture_id','match_id','external_id'], '')
            items.append({
                'source': table, 'id': str(item_id), 'title': str(title)[:120], 'league': str(league)[:80],
                'market': str(market)[:120], 'odds': str(odds)[:20], 'status': str(status)[:30],
                'score': score, 'risk': str(risk)[:30], 'stake': str(stake)[:30], 'start': str(start)[:40],
                'match_url': f"/partido-pro/{item_id}" if item_id else '/match-center-pro'
            })
        if len(items) >= limit:
            break
    # dedupe by title+market
    seen, clean = set(), []
    for it in items:
        key = (it['title'].lower(), it['market'].lower())
        if key in seen:
            continue
        seen.add(key)
        clean.append(it)
    return clean[:limit]


def _filter_items_for_plan(items, plan):
    rule = PLAN_RULES[_normalize_plan(plan)]
    result = []
    for it in items:
        score = int(it.get('score') or 0)
        # si no hay score real, no bloqueamos; es dato real pero sin rating.
        if score and score < rule['min_score'] and plan != 'ADMIN':
            continue
        result.append(it)
        if len(result) >= rule['limit']:
            break
    return result


def _env_targets():
    return {
        'ADMIN': os.environ.get('TELEGRAM_ADMIN_CHAT_ID') or os.environ.get('TELEGRAM_OWNER_CHAT_ID') or os.environ.get('TELEGRAM_CHAT_ID') or '',
        'FREE': os.environ.get('TELEGRAM_FREE_CHAT_ID') or '',
        'PRO': os.environ.get('TELEGRAM_PRO_CHAT_ID') or os.environ.get('TELEGRAM_CHAT_ID') or '',
        'ELITE': os.environ.get('TELEGRAM_ELITE_CHAT_ID') or os.environ.get('TELEGRAM_CHAT_ID') or '',
    }


def _build_message(plan, items, user=None, admin=False):
    plan = _normalize_plan(plan)
    rule = PLAN_RULES[plan]
    lines = []
    lines.append(f"{rule['emoji']} <b>{html.escape(rule['title'])}</b>")
    lines.append(f"Versión: {VERSION}")
    if user:
        lines.append(f"Usuario: {html.escape(str(user.get('username') or 'cliente'))} · Plan {plan}")
    lines.append('')
    if not items:
        lines.append('No hay picks/partidos reales disponibles ahora mismo.')
        lines.append('Política limpia: no se envían señales inventadas.')
    else:
        lines.append(f"Señales reales detectadas: <b>{len(items)}</b>")
        for idx, it in enumerate(items, start=1):
            odds = f" · cuota {html.escape(str(it.get('odds')))}" if it.get('odds') else ''
            score = f" · SHARK {it.get('score')}" if it.get('score') else ''
            stake = f" · stake {html.escape(str(it.get('stake')))}" if it.get('stake') else ''
            lines.append('')
            lines.append(f"<b>{idx}. {html.escape(it.get('title','Partido real'))}</b>")
            lines.append(f"{html.escape(it.get('league','Competición'))}")
            lines.append(f"Mercado: {html.escape(it.get('market',''))}{odds}{score}{stake}")
            if plan in ('PRO','ELITE','ADMIN'):
                lines.append(f"Riesgo: {html.escape(str(it.get('risk') or 'Medio'))} · Match Center: {html.escape(str(it.get('match_url') or '/match-center-pro'))}")
            if plan in ('ELITE','ADMIN'):
                lines.append('SHARK: revisar valor, riesgo y timing antes de entrar. Evitar forzar si el mercado cambia.')
    lines.append('')
    lines.append('Funciones del plan: ' + ', '.join(rule['features']))
    if admin:
        lines.append('')
        lines.append('Modo ADMIN: incluye visión máxima y control de entrega por membresía.')
    return '\n'.join(lines)[:3900]


def _send(chat_id, message, plan='ADMIN', user_id='', mode='manual'):
    token = os.environ.get('TELEGRAM_BOT_TOKEN') or os.environ.get('BOT_TOKEN') or ''
    now = datetime.utcnow().isoformat() + 'Z'
    status, response_text, error = 'skipped', '', ''
    if not token:
        error = 'Falta TELEGRAM_BOT_TOKEN'
    elif not chat_id:
        error = 'Falta chat_id destino'
    elif requests is None:
        error = 'requests no disponible'
    else:
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            res = requests.post(url, json={'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML', 'disable_web_page_preview': True}, timeout=12)
            response_text = res.text[:900]
            status = 'sent' if res.ok else 'failed'
            if not res.ok:
                error = response_text
        except Exception as exc:
            status = 'failed'
            error = str(exc)[:500]
    con, _ = _connect()
    try:
        if con:
            _ensure_tables(con)
            con.execute("INSERT INTO telegram_delivery_log_v172(created_at,target_chat_id,target_plan,target_user_id,mode,status,message_preview,telegram_response,error) VALUES(?,?,?,?,?,?,?,?,?)",
                        (now, str(chat_id or ''), plan, str(user_id or ''), mode, status, message[:300], response_text, error))
            con.commit()
            con.close()
    except Exception:
        pass
    return {'chat_id': str(chat_id or ''), 'plan': plan, 'user_id': user_id, 'status': status, 'ok': status == 'sent', 'error': error, 'response': response_text}


def _delivery_snapshot():
    con, path = _connect()
    try:
        _ensure_tables(con)
        users = _read_users(con)
        items = _read_real_items(con, 40)
        logs = []
        if con and _table_exists(con, 'telegram_delivery_log_v172'):
            rows = con.execute("SELECT * FROM telegram_delivery_log_v172 ORDER BY id DESC LIMIT 20").fetchall()
            logs = [dict(r) for r in rows]
    finally:
        try:
            if con: con.close()
        except Exception:
            pass
    targets = _env_targets()
    linked = [u for u in users if u.get('telegram_chat_id')]
    by_plan = {p: len([u for u in linked if u.get('plan') == p]) for p in ['FREE','PRO','ELITE','ADMIN']}
    previews = {p: _build_message(p, _filter_items_for_plan(items, p), admin=(p=='ADMIN')) for p in ['FREE','PRO','ELITE','ADMIN']}
    return {
        'ok': True, 'version': VERSION, 'generated_at': datetime.utcnow().isoformat() + 'Z',
        'database': {'detected': bool(path), 'path': path or 'NO_DETECTED'},
        'env': {
            'token': bool(os.environ.get('TELEGRAM_BOT_TOKEN') or os.environ.get('BOT_TOKEN')),
            'targets': {k: bool(v) for k, v in targets.items()},
            'cron_secret': bool(os.environ.get('TELEGRAM_CRON_SECRET')),
        },
        'users': {'total': len(users), 'linked': len(linked), 'by_plan': by_plan},
        'real_items': {'total': len(items), 'by_plan': {p: len(_filter_items_for_plan(items, p)) for p in ['FREE','PRO','ELITE','ADMIN']}},
        'rules': PLAN_RULES, 'previews': previews, 'logs': logs,
        'warnings': _warnings(path, targets, users, items)
    }


def _warnings(path, targets, users, items):
    w = []
    if not os.environ.get('TELEGRAM_BOT_TOKEN') and not os.environ.get('BOT_TOKEN'):
        w.append('Falta TELEGRAM_BOT_TOKEN en Render.')
    if not targets.get('ADMIN'):
        w.append('Falta TELEGRAM_ADMIN_CHAT_ID o TELEGRAM_CHAT_ID para que el admin reciba todo.')
    if not path:
        w.append('No se detecta SQLite persistente; no se pueden leer clientes vinculados.')
    if not any(u.get('telegram_chat_id') for u in users):
        w.append('No hay clientes con telegram_chat_id vinculado todavía.')
    if not items:
        w.append('No hay picks/partidos reales cacheados ahora mismo; no se enviarán señales fake.')
    return w


def run_delivery(plan='ALL', mode='manual', send_admin=True, send_clients=True, send_plan_channels=True):
    con, path = _connect()
    try:
        _ensure_tables(con)
        users = _read_users(con)
        items = _read_real_items(con, 50)
    finally:
        try:
            if con: con.close()
        except Exception:
            pass
    targets = _env_targets()
    selected = ['FREE','PRO','ELITE'] if str(plan).upper() in ('ALL','TODOS','') else [_normalize_plan(plan)]
    results = []
    if send_admin:
        admin_items = _filter_items_for_plan(items, 'ADMIN')
        results.append(_send(targets.get('ADMIN'), _build_message('ADMIN', admin_items, admin=True), 'ADMIN', 'admin', mode))
    if send_plan_channels:
        for p in selected:
            chat = targets.get(p)
            if chat:
                results.append(_send(chat, _build_message(p, _filter_items_for_plan(items, p)), p, f'channel-{p}', mode))
    if send_clients:
        for u in users:
            up = _normalize_plan(u.get('plan'))
            if up not in selected:
                continue
            if not u.get('telegram_chat_id') or not u.get('alerts_enabled', True):
                continue
            results.append(_send(u.get('telegram_chat_id'), _build_message(up, _filter_items_for_plan(items, up), user=u), up, u.get('id'), mode))
    return {
        'ok': True, 'version': VERSION, 'mode': mode, 'plan': plan, 'database_detected': bool(path),
        'real_items_total': len(items), 'attempts': len(results),
        'sent': len([r for r in results if r.get('ok')]),
        'failed': len([r for r in results if not r.get('ok')]),
        'results': results[:100]
    }


@telegram_membership_v172_bp.route('/api/v172/telegram-membership/status')
def api_status():
    return jsonify(_delivery_snapshot())


@telegram_membership_v172_bp.route('/api/v172/telegram-membership/send', methods=['POST'])
def api_send():
    data = request.get_json(silent=True) or request.form or {}
    return jsonify(run_delivery(plan=data.get('plan','ALL'), mode='manual', send_admin=str(data.get('send_admin','1'))!='0', send_clients=str(data.get('send_clients','1'))!='0', send_plan_channels=str(data.get('send_plan_channels','1'))!='0'))


@telegram_membership_v172_bp.route('/api/v172/telegram-membership/auto-run', methods=['GET','POST'])
def api_auto_run():
    secret = os.environ.get('TELEGRAM_CRON_SECRET') or ''
    provided = request.args.get('secret') or request.headers.get('X-Telegram-Cron-Secret') or ''
    if secret and provided != secret:
        return jsonify({'ok': False, 'error': 'secret_invalid'}), 403
    return jsonify(run_delivery(plan=request.args.get('plan','ALL'), mode='auto-cron', send_admin=True, send_clients=True, send_plan_channels=True))


@telegram_membership_v172_bp.route('/admin/telegram-membership-delivery')
@telegram_membership_v172_bp.route('/admin/telegram-v172')
def admin_page():
    if not _is_admin():
        return redirect('/admin-login')
    return render_template('telegram_membership_delivery_v172.html', data=_delivery_snapshot(), admin=True)


@telegram_membership_v172_bp.route('/admin/telegram-v172/send', methods=['POST'])
def admin_send_page():
    if not _is_admin():
        return redirect('/admin-login')
    plan = request.form.get('plan') or 'ALL'
    run_delivery(plan=plan, mode='admin-panel', send_admin=bool(request.form.get('send_admin')), send_clients=bool(request.form.get('send_clients')), send_plan_channels=bool(request.form.get('send_plan_channels')))
    return redirect('/admin/telegram-membership-delivery')


@telegram_membership_v172_bp.route('/cliente/telegram-delivery')
def client_page():
    return render_template('telegram_membership_delivery_v172.html', data=_delivery_snapshot(), admin=False)
