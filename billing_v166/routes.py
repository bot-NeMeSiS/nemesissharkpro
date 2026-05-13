from flask import Blueprint, jsonify, request, session, redirect, render_template_string
from datetime import datetime
from pathlib import Path
import os, sqlite3, json

billing_v166_bp = Blueprint('billing_v166_bp', __name__)

PLANS = {
    'FREE': {'name': 'FREE', 'price': 0, 'currency': 'EUR', 'color': 'blue', 'features': ['Partidos reales', 'Estado vacío premium', 'Panel básico']},
    'PRO': {'name': 'PRO', 'price': 19.99, 'currency': 'EUR', 'color': 'turquoise', 'features': ['Picks PRO', 'Favoritos', 'Live Center', 'Telegram premium']},
    'ELITE': {'name': 'ELITE', 'price': 49.99, 'currency': 'EUR', 'color': 'gold', 'features': ['SHARK AI contextual', 'Match Center PRO', 'ROI avanzado', 'Alertas prioritarias']},
}

def _uid():
    return str(session.get('user_id') or session.get('id') or session.get('username') or session.get('user') or 'guest')

def _db_candidates():
    return [os.environ.get('DATABASE_PATH'), os.environ.get('DB_PATH'), '/data/app.db', '/data/database.db', 'app.db', 'database.db']

def _db_path():
    for item in _db_candidates():
        if item:
            p = Path(item)
            if p.exists() or str(p).startswith('/data/'):
                return str(p)
    return 'database.db'

def _connect():
    path = _db_path()
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    con = sqlite3.connect(path, timeout=10)
    con.row_factory = sqlite3.Row
    return con, path

def _init_billing():
    con, path = _connect()
    try:
        con.execute("""CREATE TABLE IF NOT EXISTS billing_subscriptions_v166 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_ref TEXT,
            plan TEXT DEFAULT 'FREE',
            status TEXT DEFAULT 'inactive',
            provider TEXT DEFAULT 'stripe',
            stripe_customer_id TEXT,
            stripe_subscription_id TEXT,
            current_period_end TEXT,
            source TEXT DEFAULT 'system',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS billing_events_v166 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_ref TEXT,
            event_type TEXT,
            plan TEXT,
            status TEXT,
            payload TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        con.commit()
    finally:
        con.close()
    return path

def _env_ready():
    secret = bool(os.environ.get('STRIPE_SECRET_KEY'))
    webhook = bool(os.environ.get('STRIPE_WEBHOOK_SECRET'))
    price_pro = bool(os.environ.get('STRIPE_PRICE_PRO'))
    price_elite = bool(os.environ.get('STRIPE_PRICE_ELITE'))
    return {
        'stripe_secret_key': secret,
        'webhook_secret': webhook,
        'price_pro': price_pro,
        'price_elite': price_elite,
        'ready_for_checkout': bool(secret and price_pro and price_elite),
        'ready_for_webhooks': bool(secret and webhook),
    }

def _insert_event(user_ref, event_type, plan=None, status=None, payload=None):
    con, path = _connect()
    try:
        _init_billing()
        con.execute('INSERT INTO billing_events_v166(user_ref,event_type,plan,status,payload) VALUES(?,?,?,?,?)', (
            str(user_ref), event_type, plan, status, json.dumps(payload or {}, ensure_ascii=False)
        ))
        con.commit()
    finally:
        con.close()

def _get_current_plan(user_ref):
    con, path = _connect()
    try:
        _init_billing()
        row = con.execute('SELECT * FROM billing_subscriptions_v166 WHERE user_ref=? ORDER BY id DESC LIMIT 1', (str(user_ref),)).fetchone()
        if row:
            return dict(row)
    except Exception:
        pass
    finally:
        try: con.close()
        except Exception: pass
    return {'user_ref': str(user_ref), 'plan': session.get('membership') or session.get('plan') or 'FREE', 'status': 'local_session', 'source': 'session'}

def build_billing_status(user_ref=None):
    user_ref = user_ref or _uid()
    _init_billing()
    current = _get_current_plan(user_ref)
    env = _env_ready()
    return {
        'ok': True,
        'version': 'V166_BILLING_STRIPE_READY_FOUNDATION',
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'user_ref': str(user_ref),
        'current': current,
        'plans': PLANS,
        'stripe': env,
        'mode': 'stripe_ready' if env['ready_for_checkout'] else 'safe_no_keys_mode',
        'policy': {'no_fake_payments': True, 'no_fake_membership_upgrade': True, 'works_without_stripe_keys': True, 'render_safe': True},
        'next_actions': ['Configurar STRIPE_SECRET_KEY', 'Configurar STRIPE_PRICE_PRO y STRIPE_PRICE_ELITE', 'Configurar STRIPE_WEBHOOK_SECRET'] if not env['ready_for_checkout'] else ['Checkout Stripe listo para pruebas reales'],
    }

def _checkout_url(plan):
    env = _env_ready()
    plan = (plan or '').upper()
    if plan not in ('PRO', 'ELITE'):
        return None, 'Plan no válido para checkout.'
    if not env['ready_for_checkout']:
        return None, 'Stripe aún no está configurado: faltan claves o price IDs.'
    try:
        import stripe
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        price_id = os.environ.get('STRIPE_PRICE_PRO') if plan == 'PRO' else os.environ.get('STRIPE_PRICE_ELITE')
        domain = os.environ.get('PUBLIC_BASE_URL') or os.environ.get('RENDER_EXTERNAL_URL') or request.host_url.rstrip('/')
        checkout = stripe.checkout.Session.create(
            mode='subscription', line_items=[{'price': price_id, 'quantity': 1}],
            success_url=f'{domain}/billing/success?plan={plan}', cancel_url=f'{domain}/billing/cancel?plan={plan}',
            metadata={'user_ref': _uid(), 'plan': plan, 'app': 'NeMeSiS SHARK PRO'}, client_reference_id=_uid())
        _insert_event(_uid(), 'checkout_created', plan, 'pending', {'session_id': checkout.get('id')})
        return checkout.url, None
    except Exception as exc:
        return None, str(exc)

PAGE = """
<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Billing PRO · NeMeSiS SHARK</title><link rel="stylesheet" href="/static/app.css"><link rel="stylesheet" href="/static/css/v166_billing.css"></head>
<body class="v166-billing-body"><main class="v166-shell">
<section class="v166-hero"><div><span class="v166-kicker">V166 · Billing real foundation</span><h1>Planes y facturación premium</h1><p>Base comercial preparada para Stripe real, sin pagos fake y sin romper la app cuando faltan claves.</p></div><div class="v166-status {{ 'ready' if data.stripe.ready_for_checkout else 'pending' }}"><b>{{ 'Stripe listo' if data.stripe.ready_for_checkout else 'Modo seguro sin claves' }}</b><span>{{ data.mode }}</span></div></section>
<section class="v166-grid">{% for key, plan in data.plans.items() %}<article class="v166-card {{ key|lower }}"><div class="v166-plan-head"><h2>{{ plan.name }}</h2><strong>{% if plan.price == 0 %}Gratis{% else %}{{ plan.price }}€/mes{% endif %}</strong></div><ul>{% for f in plan.features %}<li>{{ f }}</li>{% endfor %}</ul>{% if key == 'FREE' %}<a class="v166-btn secondary" href="/cliente/pro">Entrar al panel</a>{% else %}<button class="v166-btn" onclick="startCheckout('{{ key }}')">Activar {{ key }}</button>{% endif %}</article>{% endfor %}</section>
<section class="v166-panel"><h2>Estado de facturación</h2><div class="v166-metrics"><div><span>Plan actual</span><b>{{ data.current.plan }}</b></div><div><span>Estado</span><b>{{ data.current.status }}</b></div><div><span>Checkout</span><b>{{ 'OK' if data.stripe.ready_for_checkout else 'Pendiente' }}</b></div><div><span>Webhooks</span><b>{{ 'OK' if data.stripe.ready_for_webhooks else 'Pendiente' }}</b></div></div><p class="v166-note">No se sube membresía por simulación. El upgrade real debe confirmarse por webhook o gestión admin.</p><pre id="billingResult" class="v166-result"></pre></section>
<nav class="v166-links"><a href="/">Landing</a><a href="/cliente/pro">Panel cliente</a><a href="/admin/business">Admin business</a><a href="/planes">Planes</a></nav>
</main><script src="/static/js/v166_billing.js"></script></body></html>
"""

@billing_v166_bp.route('/billing')
@billing_v166_bp.route('/billing-pro')
@billing_v166_bp.route('/cliente/billing')
@billing_v166_bp.route('/cliente/facturacion')
@billing_v166_bp.route('/planes/billing')
def billing_page():
    return render_template_string(PAGE, data=build_billing_status())

@billing_v166_bp.route('/billing/success')
def billing_success():
    _insert_event(_uid(), 'checkout_return_success', request.args.get('plan'), 'awaiting_webhook', dict(request.args))
    return redirect('/billing?checkout=success')

@billing_v166_bp.route('/billing/cancel')
def billing_cancel():
    _insert_event(_uid(), 'checkout_return_cancel', request.args.get('plan'), 'cancelled', dict(request.args))
    return redirect('/billing?checkout=cancel')

@billing_v166_bp.route('/admin/billing-center')
@billing_v166_bp.route('/admin/stripe-center')
def admin_billing_center():
    return render_template_string(PAGE, data=build_billing_status('admin'))

@billing_v166_bp.route('/api/v166/billing-status')
def api_billing_status():
    return jsonify(build_billing_status())

@billing_v166_bp.route('/api/v166/create-checkout-session', methods=['POST'])
def api_create_checkout():
    payload = request.get_json(silent=True) or request.form or {}
    plan = (payload.get('plan') or request.args.get('plan') or '').upper()
    url, error = _checkout_url(plan)
    if error:
        return jsonify({'ok': False, 'error': error, 'billing': build_billing_status()}), 400
    return jsonify({'ok': True, 'checkout_url': url, 'plan': plan})

@billing_v166_bp.route('/api/v166/billing-events')
def api_billing_events():
    _init_billing()
    con, path = _connect()
    try:
        rows = con.execute('SELECT * FROM billing_events_v166 ORDER BY id DESC LIMIT 30').fetchall()
        return jsonify({'ok': True, 'items': [dict(r) for r in rows], 'db_path': path})
    finally:
        con.close()

@billing_v166_bp.route('/stripe/webhook', methods=['POST'])
@billing_v166_bp.route('/api/v166/stripe-webhook', methods=['POST'])
def stripe_webhook():
    env = _env_ready()
    payload_text = request.get_data(as_text=True)
    if not env['ready_for_webhooks']:
        _insert_event('system', 'webhook_received_no_secret', None, 'ignored_safe', {'length': len(payload_text)})
        return jsonify({'ok': True, 'mode': 'safe_no_webhook_secret', 'message': 'Webhook recibido pero no procesado: falta STRIPE_WEBHOOK_SECRET.'})
    try:
        import stripe
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        sig = request.headers.get('Stripe-Signature', '')
        event = stripe.Webhook.construct_event(request.data, sig, os.environ.get('STRIPE_WEBHOOK_SECRET'))
        event_type = event.get('type')
        obj = event.get('data', {}).get('object', {})
        user_ref = obj.get('client_reference_id') or (obj.get('metadata') or {}).get('user_ref') or 'unknown'
        plan = (obj.get('metadata') or {}).get('plan')
        _insert_event(user_ref, event_type, plan, obj.get('status'), {'id': obj.get('id')})
        if event_type in ('checkout.session.completed', 'customer.subscription.updated', 'customer.subscription.created') and plan in ('PRO', 'ELITE'):
            con, path = _connect()
            try:
                _init_billing()
                con.execute('INSERT INTO billing_subscriptions_v166(user_ref,plan,status,stripe_customer_id,stripe_subscription_id,source,updated_at) VALUES(?,?,?,?,?,?,CURRENT_TIMESTAMP)', (str(user_ref), plan, 'active', obj.get('customer'), obj.get('subscription'), 'stripe_webhook'))
                con.commit()
            finally:
                con.close()
        return jsonify({'ok': True, 'event_type': event_type})
    except Exception as exc:
        _insert_event('system', 'webhook_error', None, 'error', {'error': str(exc)})
        return jsonify({'ok': False, 'error': str(exc)}), 400
