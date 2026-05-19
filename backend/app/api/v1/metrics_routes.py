from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.domain.user import User
from app.domain.user_role import UserRole
from app.schemas.metrics_schema import (
    MetricCalculationResponse,
    MetricsSnapshotResponse,
    SearchReportResponse,
)
from app.services.metrics_service import metrics_service

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("", response_model=MetricsSnapshotResponse)
def get_metrics_snapshot(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    return metrics_service.snapshot(db)


@router.get("/report", response_model=SearchReportResponse)
def get_search_report(
    dateFrom: date | None = Query(default=None),
    dateTo: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    return metrics_service.build_report(
        db,
        date_from=dateFrom,
        date_to=dateTo,
        include_stored_calculation=False,
    )


@router.get("/report/export")
def export_search_report(
    format: str = Query("csv", pattern="^(csv|json)$"),
    dateFrom: date | None = Query(default=None),
    dateTo: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    content, file_name, media_type = metrics_service.export_report(
        db,
        export_format=format,
        date_from=dateFrom,
        date_to=dateTo,
    )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )


@router.get("/calculations", response_model=list[MetricCalculationResponse])
def list_metric_calculations(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    return metrics_service.list_calculations(db, limit=limit)


@router.post("/calculations", response_model=MetricCalculationResponse)
def persist_metric_calculation(
    dateFrom: date | None = Query(default=None),
    dateTo: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    return metrics_service.persist_calculation(
        db,
        date_from=dateFrom,
        date_to=dateTo,
    )
