# NeMeSiS SHARK PRO V178 - Automation Engine PRO

Incluye centro de automatizaciones para jobs internos: fixtures, Telegram admin, Telegram por membresía, Smart Live, health check y limpieza suave.

Rutas:
- /admin/automation-engine
- /admin/automation
- /admin/jobs

APIs:
- /api/v178/automation/status
- /api/v178/automation/run/<job_key>
- /api/v178/automation/run-due
- /api/v178/automation/toggle/<job_key>

No inventa datos: orquesta tareas sobre datos reales/cacheados y deja logs en SQLite.
