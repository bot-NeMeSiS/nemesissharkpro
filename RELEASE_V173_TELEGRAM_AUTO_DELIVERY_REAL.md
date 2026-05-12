# NeMeSiS SHARK PRO V173 — Telegram Auto Delivery REAL

## Nuevo
- Auto delivery real por membresía: FREE / PRO / ELITE / ADMIN.
- Admin recibe modo máximo si `TELEGRAM_ADMIN_CHAT_ID` o `TELEGRAM_CHAT_ID` está configurado.
- Anti-repetidos por chat/plan/señal con ventana configurable.
- Panel admin `/admin/telegram-auto-delivery`.
- API cron `/api/v173/telegram-auto/run?secret=TU_SECRET`.
- Descubrimiento de chat privado admin con getUpdates desde panel.
- Mantiene política no fake: si no hay picks/partidos reales cacheados, no inventa señales.

## Variables recomendadas Render
```env
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=-100...
TELEGRAM_ADMIN_CHAT_ID=...
TELEGRAM_CRON_SECRET=...
TELEGRAM_AUTO_DELIVERY_ENABLED=1
TELEGRAM_ANTI_REPEAT_HOURS=18
```

## Uso admin
1. Abre el bot en Telegram y manda `/start`.
2. Entra en `/admin/telegram-auto-delivery`.
3. Pulsa “Buscar chat_id admin”.
4. Copia el chat_id privado a Render como `TELEGRAM_ADMIN_CHAT_ID` si quieres recibirlo tú directo.
5. Usa “Lanzar auto delivery real” para prueba.
