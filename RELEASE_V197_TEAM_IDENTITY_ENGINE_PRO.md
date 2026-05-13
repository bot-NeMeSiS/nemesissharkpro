# V197 · TEAM IDENTITY ENGINE PRO

Avance visual premium para NeMeSiS SHARK PRO.

## Incluye
- Motor de identidad de equipos y competiciones.
- Escudos/logos reales cuando vienen del proveedor de datos.
- Fallback premium seguro cuando no existe logo real.
- Caché SQLite persistente `team_identity_cache_v197`.
- Auditoría `team_identity_audit_v197`.
- Rutas cliente/admin en español.
- API de sincronización y resolución.

## Filosofía
- No inventa escudos.
- No inventa equipos.
- No inventa competiciones.
- REAL ONLY: si no hay logo real, muestra fallback visual premium.

## Rutas
- `/cliente/team-identity`
- `/team-identity-pro`
- `/admin/team-identity`
- `/api/v197/team-identity/sync`
- `/api/v197/team-identity/resolve?kind=team&name=Equipo`
- `/api/v197/team-identity/matches`
