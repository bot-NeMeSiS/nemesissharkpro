# V59 Seguridad y arquitectura

- Rate limit básico en login y endpoints de SHARK AI.
- Cabeceras de seguridad HTTP.
- Centro `/admin/security` para revisar eventos.
- Backup manual SQLite desde admin.
- Endpoint `/api/security-status` para diagnóstico.
- Endpoint `/api/live-card-check` para revisar tablas usadas en tarjetas/live sin forzar APIs externas.

## Variables opcionales

```env
RATE_LIMIT_WINDOW_SECONDS=60
RATE_LIMIT_LOGIN_MAX=12
RATE_LIMIT_AI_MAX=30
SECURITY_LOG_MAX_ROWS=800
BACKUP_DIR=/data/backups
```
