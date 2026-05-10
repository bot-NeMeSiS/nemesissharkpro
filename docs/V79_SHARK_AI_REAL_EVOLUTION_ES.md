
# NeMeSiS SHARK PRO V79 — SHARK AI Real Evolution

Fecha de generación: 2026-05-10T20:02:42.581585+00:00

## Objetivo

Convertir SHARK AI en una pieza diferencial real del producto, no solo en una capa visual.

## Incluye

- Panel `/admin/shark-ai-v79`
- API `/api/shark-ai-v79/status`
- Predicción `/api/shark-ai-v79/predict`
- Rebuild patrones `/api/shark-ai-v79/rebuild-patterns`
- Snapshot `/api/shark-ai-v79/snapshot`
- Tabla `shark_ai_predictions`
- Tabla `shark_ai_pattern_memory`
- Tabla `shark_ai_model_snapshots`
- Tabla `shark_ai_rejected_signals`

## Motores V79

### Score adaptativo

Combina:

- score base
- value score
- riesgo por cuota
- ajuste histórico por patrón
- fiabilidad del mercado/liga/deporte

### Pattern Memory

Aprende de:

- deporte
- liga
- mercado
- ROI histórico
- win rate
- muestra

### Decision Engine

Clasifica picks como:

- APROBADO
- OBSERVAR
- RECHAZADO

### Explicación IA

Genera motivos legibles para admin/cliente:

- value detectado
- riesgo
- fiabilidad histórica
- score adaptativo
- confianza final

## Importante

No mete librerías pesadas tipo TensorFlow/PyTorch para no romper Render.
Esta versión deja la base lista para un futuro modelo ML real con datos propios.

## Siguiente paso recomendado

V80 — Enterprise Data Layer: PostgreSQL-ready, Redis-ready, worker-ready.
