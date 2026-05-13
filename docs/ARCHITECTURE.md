# Arquitectura — NeMeSiS SHARK PRO

## Objetivo V57

Reducir peso, evitar problemas al subir a GitHub y preparar la app para una arquitectura más profesional sin romper lo que ya funciona.

## Capas actuales

### 1. Frontend

- `templates/` para HTML.
- `static/app.css` para experiencia visual premium.
- `static/app.js` para interacciones, PWA, push y UX.
- `service-worker.js` para PWA/push.

### 2. Backend

- `app.py` contiene la app Flask principal.
- Mantiene login, usuarios, membresías, picks, ROI, Telegram, push, live, admin y estabilidad.

### 3. Datos

- SQLite persistente en Render mediante `DB_PATH`.
- En Render debe apuntar a `/data/database.db`.
- Las bases de datos locales NO se suben a GitHub.

### 4. Integraciones

- The Odds API: partidos/cuotas/picks.
- Telegram Bot API: alertas por membresía.
- Push Web: notificaciones PWA.
- OpenAI: SHARK AI.

## Próximo refactor recomendado

Para V58/V59 conviene separar `app.py` poco a poco en módulos:

- `services/telegram_service.py`
- `services/odds_service.py`
- `services/push_service.py`
- `services/roi_service.py`
- `services/membership_service.py`
- `blueprints/admin.py`
- `blueprints/client.py`
- `blueprints/api.py`

La V57 no rompe nada: limpia y prepara el terreno.
