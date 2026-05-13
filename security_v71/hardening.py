
"""
NeMeSiS SHARK PRO V71
Security + Scale Hardening

Capa ligera y segura para Flask/Render.
No depende de librerías pesadas.
"""

import os
import time
from functools import wraps
from flask import request, jsonify, g


_REQUEST_BUCKET = {}


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return str(value).lower() in ("1", "true", "yes", "on")


def get_client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def simple_rate_limit(max_requests=80, window_seconds=60):
    """
    Rate limit en memoria. Suficiente como capa básica Render.
    Para escala grande, sustituir por Redis.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not env_bool("V71_RATE_LIMIT_ENABLED", True):
                return fn(*args, **kwargs)

            now = int(time.time())
            ip = get_client_ip()
            key = f"{ip}:{request.endpoint}"
            bucket = _REQUEST_BUCKET.get(key, [])
            bucket = [t for t in bucket if now - t < window_seconds]

            if len(bucket) >= max_requests:
                return jsonify({
                    "ok": False,
                    "error": "rate_limited",
                    "message": "Demasiadas solicitudes. Inténtalo de nuevo en unos segundos."
                }), 429

            bucket.append(now)
            _REQUEST_BUCKET[key] = bucket
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def install_security_headers(app):
    @app.after_request
    def add_security_headers(response):
        if env_bool("V71_SECURITY_HEADERS_ENABLED", True):
            response.headers.setdefault("X-Content-Type-Options", "nosniff")
            response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
            response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
            response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
            response.headers.setdefault("X-XSS-Protection", "0")
            if request.is_secure or os.getenv("RENDER"):
                response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response


def install_request_timer(app):
    @app.before_request
    def start_timer():
        g.v71_start_time = time.time()

    @app.after_request
    def add_timing_header(response):
        try:
            elapsed = time.time() - g.v71_start_time
            response.headers["X-NeMeSiS-Response-Time"] = f"{elapsed:.4f}s"
        except Exception:
            pass
        return response


def get_security_scale_status():
    required_env = [
        "SECRET_KEY",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "DATABASE_URL",
        "ENABLE_PRO_ALERTS",
        "STABILITY_HARD_MODE",
        "PERFORMANCE_SAFE_MODE",
    ]

    env_status = {}
    for key in required_env:
        value = os.getenv(key)
        env_status[key] = bool(value)

    missing = [k for k, ok in env_status.items() if not ok]

    checks = [
        {
            "area": "Security Headers",
            "status": "ACTIVO" if env_bool("V71_SECURITY_HEADERS_ENABLED", True) else "OFF",
            "description": "Headers defensivos contra sniffing, clickjacking y permisos innecesarios.",
        },
        {
            "area": "Rate Limit",
            "status": "ACTIVO" if env_bool("V71_RATE_LIMIT_ENABLED", True) else "OFF",
            "description": "Limitador básico por IP y endpoint para reducir abuso.",
        },
        {
            "area": "Request Timing",
            "status": "ACTIVO",
            "description": "Cabecera X-NeMeSiS-Response-Time para detectar endpoints lentos.",
        },
        {
            "area": "Render Safe Mode",
            "status": "ACTIVO" if os.getenv("PERFORMANCE_SAFE_MODE", "true").lower() == "true" else "REVISAR",
            "description": "Modo seguro para evitar procesos pesados y timeouts.",
        },
        {
            "area": "Variables críticas",
            "status": "OK" if not missing else "REVISAR",
            "description": f"Faltan: {', '.join(missing)}" if missing else "Variables críticas detectadas.",
        },
    ]

    score = 100
    if missing:
        score -= min(len(missing) * 7, 35)
    if not env_bool("V71_SECURITY_HEADERS_ENABLED", True):
        score -= 10
    if not env_bool("V71_RATE_LIMIT_ENABLED", True):
        score -= 10

    return {
        "status": "PRODUCTION HARDENED" if score >= 85 else "REVIEW REQUIRED",
        "security_score": max(score, 0),
        "missing_env": missing,
        "checks": checks,
        "recommendation": "Listo para QA final antes de Stripe." if score >= 85 else "Revisar variables y configuración antes de lanzar.",
    }


def install_v71_hardening(app):
    install_security_headers(app)
    install_request_timer(app)
    return app
