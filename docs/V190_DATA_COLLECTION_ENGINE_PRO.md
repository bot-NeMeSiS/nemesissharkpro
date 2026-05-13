# V190 Data Collection Engine PRO

Objetivo:
- Guardar histórico real de fixtures, picks, cuotas y resultados.
- Crear snapshots reutilizables para ML.
- Mantener ciclo de vida de picks.
- Exportar CSV para análisis externo.
- Preparar el valor de datos a largo plazo.

Rutas:
- `/data-collection-engine-pro`
- `/admin/data-collection`
- `/admin/data-engine`

APIs:
- `/api/v190/data-collection/status`
- `/api/v190/data-collection/run`
- `/api/v190/data/export/snapshots.csv`
- `/api/v190/data/export/picks.csv`

Política:
- No inventa datos deportivos.
- Si no hay tablas origen, muestra estado vacío y espera a que fixtures/picks reales entren.
