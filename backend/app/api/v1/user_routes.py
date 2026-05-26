from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.core.logging import logger
from app.domain.user import User
from app.domain.user_role import UserRole
from app.schemas.user_schema import UserCreate, UserResponse, UserUpdate
from app.services.administrative_history_service import administrative_history_service
from app.services.user_service import user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    user_create: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    logger.info("Create user requested by admin=%s email=%s", current_user.email, user_create.email)
    created_user = user_service.create_user(db, user_create)
    administrative_history_service.log_action(
        db,
        actor=current_user,
        description=f"Usuário {created_user.email} criado.",
        action_type="Criação de Usuário",
        entity_type="usuario",
        entity_id=created_user.cod_usuario,
    )
    return created_user


@router.get(
    "/",
    response_model=List[UserResponse],
)
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    logger.info("Admin listing users with skip=%s limit=%s", skip, limit)
    """
    Retrieve all users. (Admin only)
    """
    return user_service.get_all_users(db, skip, limit)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    return user_service.get_user_by_id(db, user_id)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    logger.info("Update user requested by admin=%s user_id=%s", current_user.email, user_id)
    updated_user = user_service.update_user(db, user_id, user_update)
    administrative_history_service.log_action(
        db,
        actor=current_user,
        description=f"Usuário {updated_user.email} atualizado.",
        action_type="Ação Administrativa",
        entity_type="usuario",
        entity_id=updated_user.cod_usuario,
    )
    return updated_user


@router.delete(
    "/{user_id}",
    response_model=UserResponse,
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    logger.info("Delete user requested by admin=%s user_id=%s", current_user.email, user_id)
    deleted_user = user_service.delete_user(db, user_id)
    administrative_history_service.log_action(
        db,
        actor=current_user,
        description=f"Usuário {deleted_user.email} inativado.",
        action_type="Ação Administrativa",
        entity_type="usuario",
        entity_id=deleted_user.cod_usuario,
    )
    return deleted_user
