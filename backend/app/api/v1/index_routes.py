from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.core.logging import logger
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
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    logger.info(
        "Consulta status do índice solicitada por usuário %s (%s)",
        current_user.nome,
        current_user.cod_usuario,
    )
    result = index_service.get_status_snapshot(db)
    logger.debug("Status do índice retornado: %s", result)
    return result


@router.post("/reindex", response_model=ReindexResponse)
def reindex_all_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    logger.info(
        "Requisição de reindexação completa recebida por usuário %s (%s)",
        current_user.nome,
        current_user.cod_usuario,
    )
    result = index_service.reindex_all_documents(db, triggered_by=current_user)
    logger.info("Reindexação completa enviada para cliente: %s", result["message"])
    return result
