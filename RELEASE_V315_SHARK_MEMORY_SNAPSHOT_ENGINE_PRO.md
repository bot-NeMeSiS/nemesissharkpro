# NeMeSiS SHARK PRO — V315 · SHARK MEMORY SNAPSHOT ENGINE PRO

## Qué añade

- Motor real `live_engine/v315_shark_memory_engine.py`.
- Memoria persistente ligera en `/data/shark_memory_snapshots_v315.json` cuando Render Persistent Disk está activo.
- Fallback local seguro si `/data` no está disponible.
- API `/api/v315/shark-memory`.
- API `/api/v315/live-history`.
- Pantalla cliente `/cliente/shark-memory`.
- Deltas de momentum, tendencias, memoria por partido y timeline de snapshots.
- Contexto preparado para SHARK AI y ML futuro.

## Importante

- No llama a The Odds API ni TheSportsDB al abrir la pantalla.
- Trabaja sobre datos cacheados y capas V312/V313/V314.
- Mantiene V314 estable y añade V315 encima.
- Build completo, no paquete mínimo.
