from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.bot.bot_service import bot_service
from app.bot.telegram_adapter import TelegramAdapter
from app.bot.whatsapp_adapter import WhatsAppAdapter
from app.core.database import get_db
from app.core.logging import logger
from app.schemas.bot_schema import BotResponse, BotTestRequest, BotWebhookResponse

router = APIRouter(prefix="/bot", tags=["Bot"])

telegram_adapter = TelegramAdapter()
whatsapp_adapter = WhatsAppAdapter()


@router.post("/test", response_model=BotResponse)
def test_bot_message(
    payload: BotTestRequest,
    db: Session = Depends(get_db),
):
    logger.info("Bot test message received channel=%s user=%s", payload.channel, payload.external_user_id)
    return bot_service.handle_message(
        db,
        channel=payload.channel,
        external_user_id=payload.external_user_id,
        message=payload.message,
    )


@router.post("/telegram/webhook", response_model=BotWebhookResponse)
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    if not telegram_adapter.is_valid_secret(x_telegram_bot_api_secret_token):
        raise HTTPException(status_code=403, detail="Token de webhook inválido.")

    payload = await request.json()
    incoming = telegram_adapter.parse_update(payload)
    if not incoming.external_user_id or not incoming.message:
        return BotWebhookResponse(ok=True, sent=False, response_text="Payload sem mensagem textual.")

    response = bot_service.handle_message(
        db,
        channel=incoming.channel,
        external_user_id=incoming.external_user_id,
        message=incoming.message,
    )
    send_result = telegram_adapter.send_message(
        incoming.reply_to or incoming.external_user_id,
        response["response_text"],
    )
    return BotWebhookResponse(
        ok=True,
        intent=response["intent"],
        response_text=response["response_text"],
        sent=bool(send_result.get("sent")),
    )


@router.get("/whatsapp/webhook", response_class=PlainTextResponse)
def verify_whatsapp_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
):
    challenge = whatsapp_adapter.verify_webhook(
        {
            "hub.mode": hub_mode,
            "hub.verify_token": hub_verify_token,
            "hub.challenge": hub_challenge,
        }
    )
    return PlainTextResponse(challenge)


@router.post("/whatsapp/webhook", response_model=BotWebhookResponse)
async def whatsapp_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    payload = await request.json()
    incoming = whatsapp_adapter.parse_message(payload)
    if not incoming.external_user_id or not incoming.message:
        return BotWebhookResponse(ok=True, sent=False, response_text="Payload sem mensagem textual.")

    response = bot_service.handle_message(
        db,
        channel=incoming.channel,
        external_user_id=incoming.external_user_id,
        message=incoming.message,
    )
    send_result = whatsapp_adapter.send_message(
        incoming.reply_to or incoming.external_user_id,
        response["response_text"],
    )
    return BotWebhookResponse(
        ok=True,
        intent=response["intent"],
        response_text=response["response_text"],
        sent=bool(send_result.get("sent")),
    )
