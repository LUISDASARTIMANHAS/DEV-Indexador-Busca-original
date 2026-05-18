# app/api/v1/auth_routes.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_session, get_current_user
from app.domain.user import User
from app.domain.user_session import UserSession
from app.schemas.auth_schema import (
    AuthenticatedUserResponse,
    LoginRequest,
    LogoutResponse,
    TokenResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    identifier = request.login or request.email
    return AuthService.login(db, identifier, request.password)


@router.get("/me", response_model=AuthenticatedUserResponse)
def me(user: User = Depends(get_current_user)):
    return {
        "id": user.cod_usuario,
        "name": user.nome,
        "login": user.login,
        "email": user.email,
        "role": AuthService._map_role(user.perfil),
        "active": user.ativo,
        "perfil": user.perfil,
    }


@router.post("/logout", response_model=LogoutResponse)
def logout(
    current_session: UserSession = Depends(get_current_session),
    db: Session = Depends(get_db),
):
    return AuthService.logout(
        db,
        session_id=current_session.identificador_sessao,
    )
