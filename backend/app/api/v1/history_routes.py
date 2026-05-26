from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.core.logging import logger
from app.domain.user import User
from app.domain.user_role import UserRole
from app.schemas.history_schema import AdministrativeHistoryResponse
from app.services.administrative_history_service import administrative_history_service

router = APIRouter(prefix="/history", tags=["History"])


@router.get("/", response_model=list[AdministrativeHistoryResponse])
def list_history(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    logger.info("Administrative history requested")
    return administrative_history_service.list_history(db)
