
import os
import requests

class TelegramService:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    @property
    def enabled(self):
        return bool(self.token and self.chat_id)

    def send_message(self, text):
        if not self.enabled:
            return {"ok": False, "reason": "telegram_not_configured"}

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML"
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            return response.json()
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
