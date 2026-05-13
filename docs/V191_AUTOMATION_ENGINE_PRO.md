# V191 · AUTOMATION ENGINE PRO

Motor de automatización real para NeMeSiS SHARK PRO.

## Incluye

- Auto sync de fixtures reales cuando el conector/base URL está disponible.
- Auto snapshots históricos usando V190 Data Collection Engine.
- Auto cache warming de rutas premium para acelerar la app.
- Auto close picks con política segura: no cierra nada sin resultado real verificable.
- Auto Telegram dispatch para resumen admin real si hay token/chat configurados.
- Cron internal jobs con endpoints protegibles por `AUTOMATION_SECRET` o `CRON_SECRET`.
- Trazabilidad SQLite: jobs, runs, locks, warming y dispatch.

## Rutas nuevas

- `/automation-engine-pro`
- `/admin/automation-engine-pro`
- `/admin/automation-v191`
- `/api/v191/automation/status`
- `/api/v191/automation/run-due`
- `/api/v191/automation/run/<job_key>`
- `/api/v191/automation/toggle/<job_key>`

## Variables recomendadas

- `PUBLIC_BASE_URL` o `RENDER_EXTERNAL_URL` para llamadas internas.
- `AUTOMATION_SECRET` o `CRON_SECRET` para proteger cron endpoints.
- `TELEGRAM_BOT_TOKEN` o `BOT_TOKEN`.
- `TELEGRAM_ADMIN_CHAT_ID` o `ADMIN_CHAT_ID`.

## Filosofía

REAL ONLY: no genera partidos, picks, cuotas ni resultados falsos. Solo orquesta motores reales, cachés existentes y datos persistidos.
