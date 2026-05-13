# V102 — ANALYTICS PRO MODULE

## Instalación

Extrae este ZIP encima de tu app completa estable actual.

## Archivos añadidos

- backend/core/analytics_pro_engine.py
- backend/routes/analytics_pro_routes.py
- backend/services/analytics_pro_service.py
- frontend/pages/AnalyticsPro.jsx
- frontend/components/AnalyticsMetricCard.jsx
- frontend/components/AnalyticsTable.jsx

## Registrar Blueprint en Flask

En tu app principal, añade:

```python
from backend.routes.analytics_pro_routes import analytics_pro_bp
app.register_blueprint(analytics_pro_bp)
```

## Rutas nuevas

- GET /api/v102/analytics/health
- POST /api/v102/analytics/dashboard

## Ejemplo POST

```json
{
  "picks": [
    {
      "sport": "football",
      "league": "LaLiga",
      "pick": "Over 2.5",
      "stake": 2,
      "odds": 1.90,
      "result": "WIN"
    }
  ]
}
```

## Importante

No inventa datos.
Calcula estadísticas desde picks reales cerrados.
