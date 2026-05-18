from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.domain.user import User
from app.domain.user_role import UserRole
from app.schemas.index_schema import (
    IndexStatusResponse,
    ReindexResponse,
)
from app.services.index_service import index_service

router = APIRouter(prefix="/index", tags=["Index"])


@router.get("/status", response_model=IndexStatusResponse)
def get_index_status(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    return index_service.get_status_snapshot(db)


@router.post("/reindex", response_model=ReindexResponse)
def reindex_all_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    return index_service.reindex_all_documents(db, triggered_by=current_user)
