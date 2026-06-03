from typing import Any

from pydantic import BaseModel, Field


class BotIncomingMessage(BaseModel):
    channel: str
    external_user_id: str
    message: str
    reply_to: str | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class BotTestRequest(BaseModel):
    channel: str = "test"
    external_user_id: str
    message: str


class BotResponse(BaseModel):
    channel: str
    external_user_id: str
    intent: str
    entities: dict[str, Any] = Field(default_factory=dict)
    response_text: str
    results: list[dict[str, Any]] = Field(default_factory=list)
    success: bool = True


class BotWebhookResponse(BaseModel):
    ok: bool = True
    intent: str | None = None
    response_text: str | None = None
    sent: bool = False
