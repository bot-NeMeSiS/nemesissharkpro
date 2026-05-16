# V325 REAL · Smart Client Match Flow

Build completo sobre V324 REAL estable.

## Añadido
- Ruta cliente `/cliente/smart-match-flow`
- Alias `/cliente/flujo-inteligente` y `/cliente/v325`
- API `/api/v325/smart-match-flow`
- API `/api/v325/client-experience`
- Capa `client_experience/`
- Motor `live_engine/match_flow_engine_v325.py`
- Briefing `ai_engine/shark_client_briefing_v325.py`
- Servicio de resumen cliente V325
- CSS/JS premium para experiencia guiada

## Seguridad
- No llama APIs externas.
- No toca login/admin/Telegram/webhooks.
- Conserva `app.py` real.
