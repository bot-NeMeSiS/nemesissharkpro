# NeMeSiS SHARK PRO V96 — Live Center PRO + SHARK AI Conversacional

## Qué mejora

- Nuevo Live Center visual PRO conectado al Real Core.
- Nuevo SHARK AI conversacional para preguntar por mejores picks, live, riesgo y resumen del feed.
- Nueva lectura de partido por API.
- Sin demos, sin partidos inventados, sin fallback fake.
- Compatible con GitHub + Render Auto Deploy.

## Nuevas rutas visuales

- `/live-center-pro`
- `/v96/live-center`
- `/shark-ai-pro`
- `/v96/shark-ai`

## Nuevas APIs

- `/api/v96/live-center`
- `/api/v96/shark-ai?q=mejor pick`
- `/api/v96/match/<match_id>/reading`

## Reglas V96

- Todo lee de `core.real_core_engine.RealCoreEngine`.
- Si no hay feed real, muestra vacío seguro.
- No crea picks falsos.
- No necesita nuevas variables obligatorias.

## Siguiente paso recomendado

V97 — Admin PRO SaaS Center:

- estado de APIs
- health de Render
- monitor Telegram
- control de usuarios
- control de membresías
- botones de test real
- dashboard de negocio
