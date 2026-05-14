# V255 · HOT MATCH ALERTS ENGINE PRO

Avance sobre V254/V253 manteniendo REAL ONLY.

## Añadido
- Nueva ruta `/hot-match-alerts`.
- Rutas cliente/admin: `/cliente/hot-match-alerts`, `/admin/hot-match-alerts`.
- API: `/api/v255/hot-match-alerts/status`.
- Scoring real por partido según minuto, marcador, cuota, fuente, ID externo y escudos.
- Estados: HOT, WATCH, LOW DATA y PENDING REAL DATA.
- Fallback premium si faltan datos.

## Importante
No inventa presión, momentum, marcadores ni alertas. Si falta dato real, lo marca como pendiente.

## Siguiente paso recomendado
Conectar este motor a notificaciones Telegram/PWA con control de frecuencia y ahorro de API.
