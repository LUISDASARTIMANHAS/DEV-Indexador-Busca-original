import json
from urllib import request

from app.core.config import settings
from app.schemas.bot_schema import BotIncomingMessage


class TelegramAdapter:
    def parse_update(self, payload: dict) -> BotIncomingMessage:
        message = payload.get("message") or payload.get("edited_message") or {}
        chat = message.get("chat") or {}
        text = message.get("text") or ""
        chat_id = str(chat.get("id") or "")
        return BotIncomingMessage(
            channel="telegram",
            external_user_id=chat_id,
            reply_to=chat_id,
            message=text,
            raw_payload=payload,
        )

    def is_valid_secret(self, secret: str | None) -> bool:
        expected = settings.TELEGRAM_WEBHOOK_SECRET
        return not expected or secret == expected

    def send_message(self, chat_id: str, text: str) -> dict:
        if not settings.BOT_ENABLE_TELEGRAM or not settings.TELEGRAM_BOT_TOKEN:
            return {"sent": False, "mode": "mock", "reason": "Telegram desabilitado ou sem token."}

        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
        req = request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=10) as response:
            return {"sent": response.status < 300, "status": response.status}
