from datetime import date

from fastapi import APIRouter, Depends, Query
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
    userId: int | None = Query(default=None, ge=1),
    dateFrom: date | None = Query(default=None),
    dateTo: date | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    logger.info("Administrative history requested userId=%s dateFrom=%s dateTo=%s", userId, dateFrom, dateTo)
    return administrative_history_service.list_history(
        db,
        limit=limit,
        user_id=userId,
        performed_from=dateFrom,
        performed_to=dateTo,
    )
