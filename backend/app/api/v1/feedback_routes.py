from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.domain.user import User
from app.schemas.feedback_schema import RelevanceFeedbackCreate, RelevanceFeedbackResponse
from app.services.feedback_service import feedback_service

router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.post("", response_model=RelevanceFeedbackResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=RelevanceFeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_relevance_feedback(
    payload: RelevanceFeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return feedback_service.submit(db, payload=payload, current_user=current_user)
