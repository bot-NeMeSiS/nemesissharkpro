# NeMeSiS SHARK PRO V91 — Real Core Engine

Fecha generación: 2026-05-11T20:32:20.360047+00:00

## Qué cambia

Esta versión convierte el proyecto en **single source of truth**:

- `/`
- `/inicio`
- `/dashboard`
- `/partidos`
- `/picks`
- `/hoy`
- `/en-directo`
- `/partido/<id>`
- `/pick/<id>`
- `/analisis/<id>`

leen del mismo núcleo:

```python
core.real_core_engine.RealCoreEngine
```

## Regla principal

Si no hay datos reales desde The Odds API:

- no se muestran demos
- no se muestran seeds
- no se inventan cuotas
- no se inventan fechas
- no se muestran partidos viejos

## Rutas nuevas

- `/admin/real-core`
- `/api/real-core/status`
- `/api/core-feed`
- `/api/core-purge`

## Render

Asegúrate de tener en Environment:

```env
ODDS_API_KEY=tu_clave_real
V91_REAL_CORE_ENGINE_ENABLED=true
V91_SINGLE_SOURCE_OF_TRUTH=true
```

## Nota

Si `/api/core-feed` devuelve 0 partidos, es correcto que la app quede vacía. Eso significa que no está inventando nada.
