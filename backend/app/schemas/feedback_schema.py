from datetime import datetime

from pydantic import BaseModel, Field


class RelevanceFeedbackCreate(BaseModel):
    searchId: int = Field(gt=0)
    documentId: int = Field(gt=0)
    rating: int = Field(ge=0, le=10)
    comment: str | None = Field(default=None, max_length=255)


class RelevanceFeedbackResponse(BaseModel):
    id: int
    searchId: int
    documentId: int
    rating: int
    comment: str | None = None
    createdAt: datetime
