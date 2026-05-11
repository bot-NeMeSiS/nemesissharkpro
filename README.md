# NeMeSiS SHARK PRO

Plataforma premium de apuestas IA con The Odds API, SHARK AI, Telegram, Push, ROI, membresías, PWA y panel admin.

## Estado de esta versión

**V57.0 PROJECT CLEANUP + ARCHITECTURE FOUNDATION**

Esta versión limpia el repositorio para GitHub y deja la arquitectura preparada para seguir creciendo sin subir archivos basura, bases de datos locales ni caches pesadas.

## Inicio rápido en Render

1. Sube este repositorio limpio a GitHub.
2. Conecta Render al repositorio.
3. Usa `render.yaml`.
4. Añade tus variables de entorno desde `.env.example`.
5. Deploy.

## Comprobar antes de subir

```bash
python scripts/verify_project.py
python scripts/clean_before_github.py
```

## Archivos importantes

- `app.py` — aplicación Flask principal.
- `templates/` — pantallas HTML.
- `static/` — CSS, JS, iconos y escudos locales.
- `docs/ARCHITECTURE.md` — guía de arquitectura.
- `docs/DEPLOY_RENDER.md` — guía de despliegue.
- `.gitignore` — evita subir basura a GitHub.

## No subir nunca

- `.env`
- bases de datos locales
- logs
- `__pycache__`
- backups
- zips antiguos

## V58.0 — Modular Architecture + Tests

Esta versión mantiene el `app.py` estable para Render, pero añade una estructura modular segura (`app_core/`) y pruebas básicas (`tests/`) para empezar a subir arquitectura sin romper producción.

Comandos útiles:

```bash
python scripts/check_architecture.py
python scripts/run_tests.py
```


## V96 — Live Center PRO + SHARK AI Conversacional

- `/live-center-pro` panel live visual premium.
- `/shark-ai-pro` asistente SHARK conectado al Real Core.
- `/api/v96/live-center` feed live estructurado.
- `/api/v96/shark-ai` respuestas sobre picks reales.
- `/api/v96/match/<match_id>/reading` lectura PRO por partido.

Sigue la regla REAL CORE ONLY: no demos, no datos inventados.
