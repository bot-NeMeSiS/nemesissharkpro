
import os
from datetime import datetime

def saas_status():
    stripe_public = bool(os.environ.get("STRIPE_PUBLIC_KEY"))
    stripe_secret = bool(os.environ.get("STRIPE_SECRET_KEY"))
    webhook = bool(os.environ.get("STRIPE_WEBHOOK_SECRET"))

    return {
        "version": "V125_SAAS_READY_SAFE_MODE",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "stripe": {
            "public_key": stripe_public,
            "secret_key": stripe_secret,
            "webhook_secret": webhook,
            "ready": stripe_public and stripe_secret and webhook,
            "mode": "SAFE_MODE_NO_CHARGES_UNLESS_KEYS_CONFIGURED"
        },
        "plans": ["FREE", "PRO", "ELITE"],
        "membership_rules_ready": True,
        "billing_deferred_safely": not (stripe_public and stripe_secret and webhook)
    }
