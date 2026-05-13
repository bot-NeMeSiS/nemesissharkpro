# NeMeSiS SHARK PRO V86 — Live/Data Real Engine

Fecha generación: 2026-05-11T00:39:05.924406+00:00

## Objetivo

Blindar la credibilidad de datos:

- fechas correctas
- hora limpia
- filtros hoy/live/próximos
- bloqueo de partidos viejos o demasiado futuros
- detección de datos demo
- quality score por partido

## Rutas

- `/admin/live-data-quality`
- `/live-data-quality`
- `/api/live-data-quality/status`
- `/api/live-data-quality/demo`

## Variables

```env
V86_LIVE_DATA_REAL_ENGINE_ENABLED=true
V86_HIDE_INVALID_MATCHES=true
V86_MIN_DATA_SCORE=55
V86_MAX_FUTURE_DAYS=30
V86_MAX_PAST_HOURS=12
V86_BLOCK_DEMO_TEAMS=true
V86_CLEAN_TIME_LABELS=true
```

## Render

Incluye `requirements.txt`, `runtime.txt` y `Procfile`.
