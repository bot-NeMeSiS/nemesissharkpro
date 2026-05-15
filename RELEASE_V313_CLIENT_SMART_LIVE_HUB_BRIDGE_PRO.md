# RELEASE V313 · CLIENT SMART LIVE HUB BRIDGE PRO

## Objetivo
Convertir el Live Engine Real V312 en una experiencia cliente más clara y premium, conectada con Smart Home y Match Center.

## Añadido
- Nueva ruta cliente: `/cliente/smart-live-hub`
- Nueva API: `/api/v313/client-live-hub`
- Nuevo motor: `live_engine/v313_client_live_hub_engine.py`
- Nueva pantalla premium: `templates/client_live_hub_smart_home_bridge_v313.html`
- Nuevos assets:
  - `static/css/v313_client_live_hub.css`
  - `static/js/v313_client_live_hub.js`

## Qué mejora
- Foco actual del cliente.
- Acciones inteligentes: HOT, VALUE, DATA, LOOP.
- Home cards con momentum, HOT, WATCH y salud de datos.
- Match Center por partido con decisión recomendada.
- Modo cache-first: no gasta API al abrir.
- Fallback seguro para no romper la app.

## Estado
Compilado OK con `python3 -m py_compile`.
