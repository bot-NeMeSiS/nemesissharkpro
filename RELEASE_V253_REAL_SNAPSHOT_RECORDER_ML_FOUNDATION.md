# V253 · REAL SNAPSHOT RECORDER + ML FOUNDATION PRO

Avance centrado en crear base histórica real para Machine Learning futuro.

## Añadido
- Ruta `/ml-snapshot-center`
- Alias `/real-snapshot-recorder`, `/cliente/ml-snapshot-center`, `/admin/ml-snapshot-center`
- API `/api/v253/ml-snapshot-center/status`
- API `/api/v253/ml-snapshot-center/capture`
- Tabla SQLite `match_real_snapshots`
- Captura real de partido, marcador, minuto, cuotas, fuente, ID externo y calidad de datos
- Antiduplicado suave por estado/hora
- UI premium en español

## REAL ONLY
No inventa partidos, cuotas, marcadores, minutos, fuentes ni eventos. Si falta un dato, se guarda vacío y se muestra fallback premium.
