from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.core.logging import logger
from app.domain.user import User
from app.domain.user_role import UserRole
from app.schemas.notification_schema import (
    NotificationCreate,
    NotificationResponse,
    NotificationUnreadCountResponse,
)
from app.services.notification_service import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=list[NotificationResponse])
@router.get("/", response_model=list[NotificationResponse])
def list_notifications(
    limit: int = Query(default=20, ge=1, le=100),
    only_unread: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("List notifications for user=%s only_unread=%s limit=%s", current_user.email, only_unread, limit)
    return notification_service.list_for_user(
        db,
        current_user,
        limit=limit,
        only_unread=only_unread,
    )


@router.get("/unread-count", response_model=NotificationUnreadCountResponse)
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("Unread notifications count requested for user=%s", current_user.email)
    return {"unread": notification_service.unread_count(db, current_user)}


@router.post(
    "",
    response_model=list[NotificationResponse],
    status_code=status.HTTP_201_CREATED,
)
@router.post(
    "/",
    response_model=list[NotificationResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_notification(
    payload: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    logger.info("Create notification requested by admin=%s title=%s", current_user.email, payload.title)
    return notification_service.create_from_payload(
        db,
        payload,
        origin=f"admin:{current_user.email}",
    )


@router.patch("/read-all")
def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("Mark all notifications as read for user=%s", current_user.email)
    return notification_service.mark_all_read(db, current_user)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("Mark notification %s as read for user=%s", notification_id, current_user.email)
    return notification_service.mark_read(db, current_user, notification_id)
