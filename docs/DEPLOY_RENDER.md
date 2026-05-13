# Deploy en Render

## Variables mínimas

Consulta `.env.example` y rellena al menos:

```env
DB_PATH=/data/database.db
ENABLE_ODDS_API=true
ODDS_API_KEY=tu_clave
PERFORMANCE_SAFE_MODE=true
STABILITY_HARD_MODE=true
```

## Telegram

```env
ENABLE_PRO_ALERTS=true
TELEGRAM_BOT_TOKEN=tu_token
TELEGRAM_CHAT_ID=-100xxxxxxxxxx
TELEGRAM_SEND_TO_PLAN_CHANNELS=false
TELEGRAM_SEND_TO_CONNECTED_USERS=false
```

## Rendimiento recomendado

```env
PUBLIC_LIVE_REFRESH_COOLDOWN_SECONDS=900
ADMIN_REFRESH_COOLDOWN_SECONDS=240
MAX_SPORTS_PER_REFRESH=4
HTTP_TIMEOUT_SECONDS=6
BACKGROUND_JOBS_ENABLED=false
DB_ENABLE_WAL=true
```

## Comando Render

El proyecto usa `render.yaml` con Gunicorn optimizado.

## Si GitHub falla al subir

Ejecuta:

```bash
python scripts/clean_before_github.py
```

Luego vuelve a subir el proyecto limpio.
