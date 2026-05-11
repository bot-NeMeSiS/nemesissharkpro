# NeMeSiS SHARK PRO V89.1 — Real Match Full Integration

Build limpia para GitHub + Render.

Soluciona el problema de que `/partidos` y `/picks` siguieran usando datos antiguos.

Rutas conectadas al motor real:
- `/partidos`
- `/picks`
- `/real-matches`

Checks:
- `/api/real-only-proof`
- `/admin/real-match-hard-reset`

Regla:
Si no hay datos reales, no se inventa nada.
