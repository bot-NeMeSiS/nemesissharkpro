# V312 · LIVE ENGINE REAL MOMENTUM + SNAPSHOT PRO

Avance centrado en experiencia cliente live sin romper el core existente.

## Incluye

- Ruta nueva: `/cliente/live-engine-real` y `/cliente/momentum-live`.
- API interna: `/api/v312/live-engine/status`.
- Motor modular: `live_engine/v312_momentum_engine.py`.
- Momentum por partido basado en estado live, minuto, score, EV y salud de datos.
- Triggers: HOT, VALUE, TIMING, WATCH y LOW DATA.
- Snapshots ligeros preparados para histórico/ML.
- Pantalla premium de radar live con timeline accionable.
- Fix de ruta para la pantalla V310 Smart Daily Loop que existía pero no estaba conectada.

## Seguridad

- No llama APIs externas al abrir la pantalla.
- Usa datos cacheados/persistidos en SQLite.
- Si no hay datos, cae en modo LOW DATA sin romper la app.
