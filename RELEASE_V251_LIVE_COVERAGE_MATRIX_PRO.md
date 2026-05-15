# V251 · LIVE COVERAGE MATRIX PRO

Avance centrado en control real de datos partido a partido.

## Añadido
- Nueva ruta `/live-coverage-matrix`.
- Alias cliente/admin: `/cliente/live-coverage-matrix` y `/admin/live-coverage-matrix`.
- API real `/api/v251/live-coverage-matrix/status`.
- Matriz visual para detectar datos faltantes por partido:
  - hora
  - marcador
  - minuto
  - cuota
  - fuente real
  - ID externo
  - escudos
- Cobertura general en porcentajes.
- Fallback premium limpio si no hay datos.

## Principio REAL ONLY
No inventa partidos, cuotas, marcadores, minutos ni escudos.
Si falta un dato, se muestra como pendiente.
