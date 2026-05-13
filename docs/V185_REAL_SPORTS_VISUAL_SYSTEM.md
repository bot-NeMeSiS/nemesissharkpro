# V185 Real Sports Visual System

Objetivo:
- Recuperar y reforzar escudos/logos/banderas/ligas.
- Usar logos reales si vienen desde la API o caché.
- Si no hay logo real, mostrar fallback premium generado por equipo/liga.
- No inventar partidos, marcadores ni eventos.

Rutas:
- `/sports-visual-pro`
- `/cliente/sports-visual`
- `/admin/sports-visual`

APIs:
- `/api/v185/visual/matches`
- `/api/v185/visual/team?name=...`
- `/api/v185/visual/league?name=...`
- `/api/v185/visual/status`
- `/api/v185/visual/asset/<key>.svg`

Tablas:
- `sports_visual_assets_v185`
- `sports_visual_logs_v185`
