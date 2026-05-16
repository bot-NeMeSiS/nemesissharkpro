# NeMeSiS SHARK PRO · V324 REAL

Base: V323 PWA Service Worker Fix estable.

Incluye:
- Smart Cache seguro en `cache_layer/smart_cache_v324.py`
- Live Performance payload en `live_engine/live_performance_v324.py`
- Vista cliente `/cliente/live-performance`
- API `/api/v324/live-performance`
- API `/api/v324/cache-status`

Notas:
- No sustituye `app.py` por un archivo pequeño.
- Conserva el `app.py` real de la base estable.
- No llama a APIs externas al abrir la vista.
- No cachea login, admin, Telegram ni webhooks.
