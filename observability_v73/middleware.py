
"""
Middleware V73 para capturar timing y errores.
"""

import time
from flask import request, g
from .observability_engine import log_health_event, log_exception


def install_v73_observability(app):
    @app.before_request
    def v73_start_timer():
        g.v73_start = time.time()

    @app.after_request
    def v73_after_request(response):
        try:
            elapsed_ms = round((time.time() - g.v73_start) * 1000, 2)
            response.headers["X-NeMeSiS-Observability-Time"] = f"{elapsed_ms}ms"
            if request.path.startswith("/api/") or request.path.startswith("/admin/"):
                log_health_event(
                    event_type="REQUEST",
                    status=str(response.status_code),
                    message=f"{request.method} {request.path}",
                    response_time_ms=elapsed_ms,
                )
        except Exception:
            pass
        return response

    @app.errorhandler(Exception)
    def v73_unhandled_exception(exc):
        log_exception(exc, request=request, status_code=500)
        raise exc

    return app
