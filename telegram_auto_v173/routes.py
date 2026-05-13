from flask import Blueprint, jsonify, render_template, request, redirect, session
from datetime import datetime, timedelta
from pathlib import Path
import os, sqlite3, html, json, hashlib

try:
    import requests
except Exception:
    requests = None

telegram_auto_v173_bp = Blueprint('telegram_auto_v173_bp', __name__)
VERSION = 'V173_TELEGRAM_AUTO_DELIVERY_REAL'

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
        con.execute('''CREATE TABLE IF NOT EXISTS telegram_auto_state_v173 (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT NOT NULL
        )''')
        con.execute('''CREATE TABLE IF NOT EXISTS telegram_auto_dedupe_v173 (
            dedupe_key TEXT PRIMARY KEY,
            target_chat_id TEXT,
            target_plan TEXT,
            item_key TEXT,
            created_at TEXT NOT NULL
        )''')
        con.execute('''CREATE TABLE IF NOT EXISTS telegram_admin_contacts_v173 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT UNIQUE,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            source TEXT,
            created_at TEXT NOT NULL,
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



def _state_get(con, key, default=''):
    try:
        row = con.execute("SELECT value FROM telegram_auto_state_v173 WHERE key=?", (key,)).fetchone()
        return row[0] if row else default
    except Exception:
        return default


def _state_set(con, key, value):
    try:
        con.execute("INSERT OR REPLACE INTO telegram_auto_state_v173(key,value,updated_at) VALUES(?,?,?)", (key, str(value), datetime.utcnow().isoformat()+'Z'))
        con.commit()
    except Exception:
        pass


def _item_key(item):
    raw = '|'.join([str(item.get(k,'')).lower().strip() for k in ['source','id','title','market','start']])
    return hashlib.sha1(raw.encode('utf-8', 'ignore')).hexdigest()[:24]


def _dedupe_key(chat_id, plan, item):
    return hashlib.sha1(f"{chat_id}|{plan}|{_item_key(item)}".encode('utf-8')).hexdigest()


def _not_sent_recent(con, chat_id, plan, item, hours=18):
    if not con or not chat_id:
        return True
    try:
        key = _dedupe_key(chat_id, plan, item)
        row = con.execute("SELECT created_at FROM telegram_auto_dedupe_v173 WHERE dedupe_key=?", (key,)).fetchone()
        if not row:
            return True
        ts = str(row[0]).replace('Z','')
        sent_at = datetime.fromisoformat(ts)
        return datetime.utcnow() - sent_at > timedelta(hours=hours)
    except Exception:
        return True


def _mark_sent(con, chat_id, plan, item):
    if not con or not chat_id:
        return
    try:
        item_key = _item_key(item)
        con.execute("INSERT OR REPLACE INTO telegram_auto_dedupe_v173(dedupe_key,target_chat_id,target_plan,item_key,created_at) VALUES(?,?,?,?,?)",
                    (_dedupe_key(chat_id, plan, item), str(chat_id), str(plan), item_key, datetime.utcnow().isoformat()+'Z'))
        con.commit()
    except Exception:
        pass


def _filter_not_repeated(con, chat_id, plan, items, hours=18):
    return [it for it in items if _not_sent_recent(con, chat_id, plan, it, hours=hours)]


def _discover_admin_from_updates():
    """Detecta el último chat privado que haya escrito al bot para pruebas admin.
    No sustituye env vars, pero ayuda a copiar el chat_id correcto desde el panel.
    """
    token = os.environ.get('TELEGRAM_BOT_TOKEN') or os.environ.get('BOT_TOKEN') or ''
    if not token or requests is None:
        return {'ok': False, 'error': 'Falta TELEGRAM_BOT_TOKEN o requests'}
    try:
        res = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=12)
        data = res.json() if res.text else {}
        candidates = []
        for u in data.get('result', [])[-20:]:
            msg = u.get('message') or u.get('channel_post') or u.get('edited_message') or {}
            chat = msg.get('chat') or {}
            if not chat.get('id'):
                continue
            candidates.append({
                'chat_id': str(chat.get('id')), 'type': chat.get('type'), 'username': chat.get('username') or '',
                'first_name': chat.get('first_name') or '', 'last_name': chat.get('last_name') or '',
                'title': chat.get('title') or '', 'text': (msg.get('text') or '')[:80],
                'date': msg.get('date')
            })
        con, _ = _connect()
        try:
            if con:
                _ensure_tables(con)
                now = datetime.utcnow().isoformat()+'Z'
                for c in candidates:
                    if c.get('type') == 'private':
                        con.execute("INSERT OR REPLACE INTO telegram_admin_contacts_v173(chat_id,username,first_name,last_name,source,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                                    (c['chat_id'], c.get('username',''), c.get('first_name',''), c.get('last_name',''), 'getUpdates', now, now))
                con.commit()
                con.close()
        except Exception:
            pass
        return {'ok': True, 'candidates': candidates, 'private_candidates': [c for c in candidates if c.get('type') == 'private']}
    except Exception as exc:
        return {'ok': False, 'error': str(exc)[:500]}


def _auto_config():
    return {
        'enabled': str(os.environ.get('TELEGRAM_AUTO_DELIVERY_ENABLED','1')).lower() not in ('0','false','no','off'),
        'cron_secret': bool(os.environ.get('TELEGRAM_CRON_SECRET')),
        'anti_repeat_hours': int(os.environ.get('TELEGRAM_ANTI_REPEAT_HOURS') or 18),
        'admin_always': str(os.environ.get('TELEGRAM_ADMIN_ALWAYS','1')).lower() not in ('0','false','no','off'),
        'clients_enabled': str(os.environ.get('TELEGRAM_CLIENTS_ENABLED','1')).lower() not in ('0','false','no','off'),
        'plan_channels_enabled': str(os.environ.get('TELEGRAM_PLAN_CHANNELS_ENABLED','1')).lower() not in ('0','false','no','off'),
    }


def run_auto_delivery(plan='ALL', mode='auto-v173', force=False):
    cfg = _auto_config()
    if not cfg['enabled'] and not force:
        return {'ok': False, 'version': VERSION, 'error': 'TELEGRAM_AUTO_DELIVERY_ENABLED desactivado'}
    con, path = _connect()
    try:
        _ensure_tables(con)
        users = _read_users(con)
        items = _read_real_items(con, 80)
        targets = _env_targets()
        selected = ['FREE','PRO','ELITE'] if str(plan).upper() in ('ALL','TODOS','') else [_normalize_plan(plan)]
        results = []
        if cfg['admin_always']:
            admin_items = _filter_items_for_plan(items, 'ADMIN')
            if not force:
                admin_items = _filter_not_repeated(con, targets.get('ADMIN'), 'ADMIN', admin_items, cfg['anti_repeat_hours'])
            results.append(_send(targets.get('ADMIN'), _build_message('ADMIN', admin_items, admin=True), 'ADMIN', 'admin', mode))
            if results[-1].get('ok'):
                for it in admin_items: _mark_sent(con, targets.get('ADMIN'), 'ADMIN', it)
        if cfg['plan_channels_enabled']:
            for p in selected:
                chat = targets.get(p)
                if not chat: continue
                p_items = _filter_items_for_plan(items, p)
                if not force:
                    p_items = _filter_not_repeated(con, chat, p, p_items, cfg['anti_repeat_hours'])
                results.append(_send(chat, _build_message(p, p_items), p, f'channel-{p}', mode))
                if results[-1].get('ok'):
                    for it in p_items: _mark_sent(con, chat, p, it)
        if cfg['clients_enabled']:
            for u in users:
                up = _normalize_plan(u.get('plan'))
                if up not in selected: continue
                chat = u.get('telegram_chat_id')
                if not chat or not u.get('alerts_enabled', True): continue
                u_items = _filter_items_for_plan(items, up)
                if not force:
                    u_items = _filter_not_repeated(con, chat, up, u_items, cfg['anti_repeat_hours'])
                if not u_items and not force:
                    continue
                results.append(_send(chat, _build_message(up, u_items, user=u), up, u.get('id'), mode))
                if results[-1].get('ok'):
                    for it in u_items: _mark_sent(con, chat, up, it)
        _state_set(con, 'last_auto_run', datetime.utcnow().isoformat()+'Z')
        _state_set(con, 'last_auto_summary', json.dumps({'attempts':len(results),'sent':len([r for r in results if r.get('ok')]),'failed':len([r for r in results if not r.get('ok')])}))
    finally:
        try:
            if con: con.close()
        except Exception:
            pass
    return {
        'ok': True, 'version': VERSION, 'mode': mode, 'plan': plan, 'force': force,
        'database_detected': bool(path), 'real_items_total': len(items), 'attempts': len(results),
        'sent': len([r for r in results if r.get('ok')]), 'failed': len([r for r in results if not r.get('ok')]),
        'results': results[:120], 'config': cfg
    }


def _v173_snapshot():
    base = _delivery_snapshot()
    con, _ = _connect()
    auto = _auto_config()
    contacts = []
    last_auto_run = ''
    last_auto_summary = ''
    dedupe_count = 0
    try:
        if con:
            _ensure_tables(con)
            last_auto_run = _state_get(con, 'last_auto_run')
            last_auto_summary = _state_get(con, 'last_auto_summary')
            dedupe_count = _scalar(con, "SELECT COUNT(*) FROM telegram_auto_dedupe_v173", default=0)
            rows = con.execute("SELECT * FROM telegram_admin_contacts_v173 ORDER BY updated_at DESC LIMIT 10").fetchall()
            contacts = [dict(r) for r in rows]
    except Exception:
        pass
    finally:
        try:
            if con: con.close()
        except Exception:
            pass
    base['version'] = VERSION
    base['auto'] = auto
    base['last_auto_run'] = last_auto_run
    base['last_auto_summary'] = last_auto_summary
    base['dedupe_count'] = dedupe_count
    base['admin_contacts'] = contacts
    base['cron_urls'] = {
        'all': '/api/v173/telegram-auto/run?secret=TU_SECRET',
        'pro': '/api/v173/telegram-auto/run?plan=PRO&secret=TU_SECRET',
        'force_test': '/api/v173/telegram-auto/run?force=1&secret=TU_SECRET'
    }
    return base

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


@telegram_auto_v173_bp.route('/api/v172/telegram-membership/status')
def api_status():
    return jsonify(_delivery_snapshot())


@telegram_auto_v173_bp.route('/api/v172/telegram-membership/send', methods=['POST'])
def api_send():
    data = request.get_json(silent=True) or request.form or {}
    return jsonify(run_delivery(plan=data.get('plan','ALL'), mode='manual', send_admin=str(data.get('send_admin','1'))!='0', send_clients=str(data.get('send_clients','1'))!='0', send_plan_channels=str(data.get('send_plan_channels','1'))!='0'))


@telegram_auto_v173_bp.route('/api/v172/telegram-membership/auto-run', methods=['GET','POST'])
def api_auto_run():
    secret = os.environ.get('TELEGRAM_CRON_SECRET') or ''
    provided = request.args.get('secret') or request.headers.get('X-Telegram-Cron-Secret') or ''
    if secret and provided != secret:
        return jsonify({'ok': False, 'error': 'secret_invalid'}), 403
    return jsonify(run_delivery(plan=request.args.get('plan','ALL'), mode='auto-cron', send_admin=True, send_clients=True, send_plan_channels=True))


@telegram_auto_v173_bp.route('/admin/telegram-membership-delivery')
@telegram_auto_v173_bp.route('/admin/telegram-v172')
def admin_page():
    if not _is_admin():
        return redirect('/admin-login')
    return render_template('telegram_membership_delivery_v172.html', data=_delivery_snapshot(), admin=True)


@telegram_auto_v173_bp.route('/admin/telegram-v172/send', methods=['POST'])
def admin_send_page():
    if not _is_admin():
        return redirect('/admin-login')
    plan = request.form.get('plan') or 'ALL'
    run_delivery(plan=plan, mode='admin-panel', send_admin=bool(request.form.get('send_admin')), send_clients=bool(request.form.get('send_clients')), send_plan_channels=bool(request.form.get('send_plan_channels')))
    return redirect('/admin/telegram-membership-delivery')


@telegram_auto_v173_bp.route('/cliente/telegram-delivery')
def client_page():
    return render_template('telegram_membership_delivery_v172.html', data=_delivery_snapshot(), admin=False)


# --- V173 TELEGRAM AUTO DELIVERY REAL ---
@telegram_auto_v173_bp.route('/api/v173/telegram-auto/status')
def api_v173_status():
    return jsonify(_v173_snapshot())

@telegram_auto_v173_bp.route('/api/v173/telegram-auto/discover-admin', methods=['GET','POST'])
def api_v173_discover_admin():
    return jsonify(_discover_admin_from_updates())

@telegram_auto_v173_bp.route('/api/v173/telegram-auto/run', methods=['GET','POST'])
def api_v173_run():
    secret = os.environ.get('TELEGRAM_CRON_SECRET') or ''
    provided = request.args.get('secret') or request.headers.get('X-Telegram-Cron-Secret') or ''
    # Si hay secret configurado, se exige para ejecuciones externas. Desde panel admin se usa POST autenticado.
    if secret and provided != secret and not _is_admin():
        return jsonify({'ok': False, 'error': 'secret_invalid'}), 403
    force = str(request.args.get('force') or request.form.get('force') or '').lower() in ('1','true','yes','on')
    plan = request.args.get('plan') or request.form.get('plan') or 'ALL'
    return jsonify(run_auto_delivery(plan=plan, mode='auto-v173', force=force))

@telegram_auto_v173_bp.route('/admin/telegram-auto-delivery')
@telegram_auto_v173_bp.route('/admin/telegram-v173')
def admin_v173_page():
    if not _is_admin():
        return redirect('/admin-login')
    return render_template('telegram_auto_delivery_v173.html', data=_v173_snapshot(), admin=True)

@telegram_auto_v173_bp.route('/admin/telegram-v173/run', methods=['POST'])
def admin_v173_run_page():
    if not _is_admin():
        return redirect('/admin-login')
    plan = request.form.get('plan') or 'ALL'
    force = bool(request.form.get('force'))
    run_auto_delivery(plan=plan, mode='admin-auto-panel', force=force)
    return redirect('/admin/telegram-auto-delivery')

@telegram_auto_v173_bp.route('/admin/telegram-v173/discover', methods=['POST'])
def admin_v173_discover_page():
    if not _is_admin():
        return redirect('/admin-login')
    _discover_admin_from_updates()
    return redirect('/admin/telegram-auto-delivery')

@telegram_auto_v173_bp.route('/cliente/telegram-auto')
def client_v173_page():
    return render_template('telegram_auto_delivery_v173.html', data=_v173_snapshot(), admin=False)
