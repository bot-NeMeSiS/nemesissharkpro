# V101 — LIVE TRADING CENTER MODULE

## Instalación

Extrae este ZIP encima de tu app completa estable actual.

## Archivos añadidos

- backend/core/live_trading_engine.py
- backend/routes/live_trading_routes.py
- backend/services/live_trading_service.py
- frontend/pages/LiveTradingCenter.jsx
- frontend/components/LiveTradingCard.jsx

## Registrar Blueprint en Flask

En tu app principal, añade:

```python
from backend.routes.live_trading_routes import live_trading_bp
app.register_blueprint(live_trading_bp)
```

## Rutas nuevas

- GET /api/v101/live-trading/health
- POST /api/v101/live-trading/analyze
- POST /api/v101/live-trading/center

## Importante

No inventa datos.
Interpreta campos live que ya vengan desde Real Core/feed real.
