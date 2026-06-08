from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.core.logging import logger
from app.domain.user import User
from app.domain.user_role import UserRole
from app.schemas.ocr_schema import OcrReprocessResponse, OcrRunResponse, OcrStatusResponse
from app.services.ocr_service import ocr_service

router = APIRouter(prefix="/ocr", tags=["OCR"])


@router.post("/document/{document_id}", response_model=OcrRunResponse)
def run_document_ocr(
    document_id: int,
    version_id: int | None = Query(default=None),
    force: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    logger.info(
        "OCR manual solicitado para documento=%s versao=%s force=%s usuario=%s",
        document_id,
        version_id,
        force,
        current_user.email,
    )
    return ocr_service.run_ocr_for_document_version(
        db,
        document_id=document_id,
        version_id=version_id,
        force=force,
        triggered_by=current_user,
    )


@router.get("/document/{document_id}/status", response_model=OcrStatusResponse)
def get_document_ocr_status(
    document_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return ocr_service.get_document_status(db, document_id=document_id)


@router.post("/reprocess-pending", response_model=OcrReprocessResponse)
def reprocess_pending_ocr(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    logger.info("Reprocessamento OCR pendente solicitado por %s limit=%s", current_user.email, limit)
    return ocr_service.reprocess_pending(db, limit=limit, triggered_by=current_user)
