from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.logging import logger
from app.domain.user import User
from app.schemas.search_schema import (
    SearchHistoryItemResponse,
    SearchHistoryListResponse,
    SearchResponse,
)
from app.services.search_service import search_service

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", response_model=SearchResponse)
@router.get("/", response_model=SearchResponse)
def search_documents(
    q: str = Query(..., min_length=1, description="Consulta de busca"),
    category: str | None = Query(default=None),
    documentType: str | None = Query(default=None),
    author: str | None = Query(default=None),
    dateFrom: date | None = Query(default=None),
    dateTo: date | None = Query(default=None),
    sortBy: str | None = Query(default=None),
    limit: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info(
        "Search requested by user=%s query=%s category=%s documentType=%s author=%s dateFrom=%s dateTo=%s sortBy=%s limit=%s page=%s",
        current_user.email,
        q,
        category,
        documentType,
        author,
        dateFrom,
        dateTo,
        sortBy,
        limit,
        page,
    )
    return search_service.search(
        db,
        query=q,
        user_id=current_user.cod_usuario,
        category=category,
        document_type=documentType,
        author=author,
        date_from=dateFrom,
        date_to=dateTo,
        sort_by=sortBy,
        limit=limit,
        page=page,
    )


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
