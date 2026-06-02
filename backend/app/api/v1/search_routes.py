from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.core.logging import logger
from app.domain.user import User
from app.domain.user_role import UserRole
from app.schemas.search_schema import (
    SearchHistoryItemResponse,
    SearchHistoryListResponse,
    SearchResponse,
)
from app.services.search_service import search_service
from app.services.semantic_search_service import semantic_search_service

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", response_model=SearchResponse)
@router.get("/", response_model=SearchResponse)
def search_documents(
    q: str = Query(..., min_length=1, description="Consulta de busca"),
    mode: str = Query("bm25", pattern="^(frequency|tfidf|bm25|semantic|hybrid)$"),
    category: str | None = Query(default=None),
    type_: str | None = Query(default=None, alias="type"),
    documentType: str | None = Query(default=None),
    document_type: str | None = Query(default=None, alias="document_type"),
    author: str | None = Query(default=None),
    dateFrom: date | None = Query(default=None),
    dateTo: date | None = Query(default=None),
    date_from: date | None = Query(default=None, alias="date_from"),
    date_to: date | None = Query(default=None, alias="date_to"),
    sortBy: str | None = Query(default=None),
    sort_by: str | None = Query(default=None, alias="sort_by"),
    textWeight: float | None = Query(default=None, ge=0, le=1),
    semanticWeight: float | None = Query(default=None, ge=0, le=1),
    text_weight: float | None = Query(default=None, alias="text_weight", ge=0, le=1),
    semantic_weight: float | None = Query(default=None, alias="semantic_weight", ge=0, le=1),
    limit: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resolved_document_type = documentType or document_type or type_
    resolved_date_from = dateFrom or date_from
    resolved_date_to = dateTo or date_to
    resolved_sort_by = sortBy or sort_by
    resolved_text_weight = text_weight if text_weight is not None else (textWeight if textWeight is not None else 0.6)
    resolved_semantic_weight = (
        semantic_weight
        if semantic_weight is not None
        else (semanticWeight if semanticWeight is not None else 0.4)
    )
    logger.info(
        "Search requested by user=%s query=%s mode=%s category=%s documentType=%s author=%s dateFrom=%s dateTo=%s sortBy=%s limit=%s page=%s",
        current_user.email,
        q,
        mode,
        category,
        resolved_document_type,
        author,
        resolved_date_from,
        resolved_date_to,
        resolved_sort_by,
        limit,
        page,
    )
    return search_service.search(
        db,
        query=q,
        user_id=current_user.cod_usuario,
        category=category,
        document_type=resolved_document_type,
        author=author,
        date_from=resolved_date_from,
        date_to=resolved_date_to,
        sort_by=resolved_sort_by,
        mode=mode,
        text_weight=resolved_text_weight,
        semantic_weight=resolved_semantic_weight,
        limit=limit,
        page=page,
    )


@router.post("/reindex")
def rebuild_semantic_index(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    logger.info(
        "Semantic search reindex requested by user=%s (%s)",
        current_user.email,
        current_user.cod_usuario,
    )
    return semantic_search_service.rebuild_embeddings(db)


@router.get("/history", response_model=list[SearchHistoryItemResponse])
def list_recent_searches(
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("Recent search history requested for user=%s limit=%s", current_user.email, limit)
    return search_service.list_recent_searches(
        db,
        user_id=current_user.cod_usuario,
        limit=limit,
    )


@router.get("/history/entries", response_model=SearchHistoryListResponse)
def list_search_history(
    q: str | None = Query(default=None),
    performedFrom: date | None = Query(default=None),
    performedTo: date | None = Query(default=None),
    limit: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info(
        "Search history requested for user=%s query=%s performedFrom=%s performedTo=%s limit=%s page=%s",
        current_user.email,
        q,
        performedFrom,
        performedTo,
        limit,
        page,
    )
    return search_service.list_search_history(
        db,
        current_user=current_user,
        query=q,
        performed_from=performedFrom,
        performed_to=performedTo,
        limit=limit,
        page=page,
    )
