
# NeMeSiS SHARK PRO — V116 Real Data Synchronization

## Objetivo

Asegurar que cliente, live, picks y paneles usan datos reales/cache/Real Core.
No se muestran partidos inventados ni picks fake.

## Nuevas rutas

- `/admin/real-data-sync`
- `/admin/data-sync`
- `/api/v116/real-data/status`
- `/api/v116/real-data/client-feed`
- `/api/v116/real-data/cache`
- `/api/v116/real-data/cache/save`
- `/api/v116/real-data/logs`

## Política

- No fake matches
- No fake picks
- No demos visibles para cliente
- Si no hay datos reales: estado vacío premium
- Real Core primero
- Cache inteligente con TTL

## Instalación

1. Sustituye tu carpeta actual por esta.
2. `git add .`
3. `git commit -m "V116 real data synchronization"`
4. `git push`

Render hará deploy automático.
