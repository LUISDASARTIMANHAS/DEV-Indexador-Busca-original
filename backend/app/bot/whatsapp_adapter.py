import json
from urllib import request

from fastapi import HTTPException

from app.core.config import settings
from app.schemas.bot_schema import BotIncomingMessage


class WhatsAppAdapter:
    def verify_webhook(self, params: dict) -> str:
        mode = params.get("hub.mode")
        token = params.get("hub.verify_token")
        challenge = params.get("hub.challenge")
        if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN and challenge:
            return str(challenge)
        raise HTTPException(status_code=403, detail="Token de verificação inválido.")

    def parse_message(self, payload: dict) -> BotIncomingMessage:
        value = self._first_value(payload)
        message = self._first_message(value)
        contact = self._first_contact(value)
        phone_number = str(message.get("from") or contact.get("wa_id") or "")
        text = ((message.get("text") or {}).get("body") or "").strip()
        return BotIncomingMessage(
            channel="whatsapp",
            external_user_id=phone_number,
            reply_to=phone_number,
            message=text,
            raw_payload=payload,
        )

    def send_message(self, phone_number: str, text: str) -> dict:
        if (
            not settings.BOT_ENABLE_WHATSAPP
            or not settings.WHATSAPP_ACCESS_TOKEN
            or not settings.WHATSAPP_PHONE_NUMBER_ID
        ):
            return {"sent": False, "mode": "mock", "reason": "WhatsApp desabilitado ou sem credenciais."}

        url = f"https://graph.facebook.com/v19.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        payload = json.dumps(
            {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "text",
                "text": {"body": text},
            }
        ).encode("utf-8")
        req = request.Request(
            url,
            data=payload,
            headers={
                "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=10) as response:
            return {"sent": response.status < 300, "status": response.status}

    def _first_value(self, payload: dict) -> dict:
        try:
            return payload["entry"][0]["changes"][0]["value"]
        except (KeyError, IndexError, TypeError):
            return {}

    def _first_message(self, value: dict) -> dict:
        messages = value.get("messages") or []
        return messages[0] if messages else {}

    def _first_contact(self, value: dict) -> dict:
        contacts = value.get("contacts") or []
        return contacts[0] if contacts else {}
