# V172 Telegram Membership Delivery PRO

Objetivo: envíos reales a Telegram según membresía.

- ADMIN: recibe todo en modo máximo.
- FREE: resumen básico y limitado.
- PRO: picks PRO con stake/riesgo/Match Center.
- ELITE: todo PRO + SHARK avanzado y señales top.

Rutas:

- `/admin/telegram-membership-delivery`
- `/api/v172/telegram-membership/status`
- `/api/v172/telegram-membership/send`
- `/api/v172/telegram-membership/auto-run?secret=TU_SECRET`

Variables recomendadas:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ADMIN_CHAT_ID`
- `TELEGRAM_FREE_CHAT_ID` opcional
- `TELEGRAM_PRO_CHAT_ID` opcional
- `TELEGRAM_ELITE_CHAT_ID` opcional
- `TELEGRAM_CRON_SECRET` opcional para cron

Política: no se inventan picks, scores ni partidos. Si no hay datos reales cacheados, se envía estado vacío limpio o se registra sin fake.
