# V323 REAL · PWA SERVICE WORKER FIX

Corrección segura desde V321/V322 estable.

Incluye:
- `app.py` real conservado/restaurado.
- `service-worker.js` en raíz.
- `static/service-worker.js` como respaldo.
- Ruta `/service-worker.js` validada.
- Service worker seguro: no cachea APIs, login, admin, Telegram ni webhooks.
- Limpieza de cachés Python y basura.

Uso:
1. Sustituir el proyecto por este contenido.
2. Commit + push.
3. Redeploy en Render.
4. En Chrome: borrar datos del sitio si seguía cacheado el service worker viejo.
