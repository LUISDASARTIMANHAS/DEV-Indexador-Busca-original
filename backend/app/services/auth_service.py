from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.core.security import create_access_token, verify_password
from app.domain.user_session import UserSession
from app.domain.user_role import UserRole
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository


class AuthService:
    session_repository = SessionRepository()

    @staticmethod
    def _map_role(perfil: str) -> str:
        try:
            return UserRole(perfil).label
        except ValueError:
            return perfil

    @staticmethod
    def _unauthorized(detail: str = "Sessão inválida") -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )

    @staticmethod
    def authenticate_user(db: Session, identifier: str, password: str):
        logger.debug("Authenticating user identifier=%s", identifier)
        user = UserRepository.get_by_login_or_email(db, identifier)

        if not user:
            logger.warning("Authentication failed: user not found identifier=%s", identifier)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário ou senha inválidos",
            )

        if not verify_password(password, user.senha_hash):
            logger.warning("Authentication failed: invalid password for user_id=%s", user.cod_usuario)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário ou senha inválidos",
            )

        if not user.ativo:
            logger.warning("Authentication failed: inactive user_id=%s", user.cod_usuario)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário inativo",
            )

        logger.info("Authentication succeeded for user_id=%s", user.cod_usuario)
        return user

    @staticmethod
    def _create_session(db: Session, user_id: int) -> UserSession:
        now = datetime.utcnow()
        session = UserSession(
            identificador_sessao=uuid4().hex,
            cod_usuario=user_id,
            expira_em=now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            ultimo_acesso_em=now,
        )
        return AuthService.session_repository.create(db, session)

    @staticmethod
    def validate_session(db: Session, *, session_id: str, user_id: int) -> UserSession:
        session = AuthService.session_repository.get_by_identifier(db, session_id)
        if session is None or session.cod_usuario != user_id:
            raise AuthService._unauthorized()

        now = datetime.utcnow()
        if session.revogado_em is not None:
            raise AuthService._unauthorized("Sessão encerrada.")

        if session.expira_em <= now:
            session.revogado_em = now
            AuthService.session_repository.save(db, session)
            raise AuthService._unauthorized("Sessão expirada.")

        idle_timeout = timedelta(minutes=settings.SESSION_IDLE_EXPIRE_MINUTES)
        if session.ultimo_acesso_em + idle_timeout <= now:
            session.revogado_em = now
            AuthService.session_repository.save(db, session)
            raise AuthService._unauthorized("Sessão expirada por inatividade.")

        session.ultimo_acesso_em = now
        return AuthService.session_repository.save(db, session)

    @staticmethod
    def logout(db: Session, *, session_id: str) -> dict:
        logger.info("Logout requested for session=%s", session_id)
        session = AuthService.session_repository.get_by_identifier(db, session_id)
        if session is not None and session.revogado_em is None:
            session.revogado_em = datetime.utcnow()
            AuthService.session_repository.save(db, session)
        logger.info("Logout completed for session=%s", session_id)
        return {"message": "Sessão encerrada com sucesso."}

    @staticmethod
    def login(db: Session, identifier: str, password: str):
        logger.info("Login started for identifier=%s", identifier)
        user = AuthService.authenticate_user(db, identifier, password)
        session = AuthService._create_session(db, user.cod_usuario)
        token = create_access_token(
            data={
                "sub": str(user.cod_usuario),
                "login": user.login,
                "role": user.perfil,
                "sid": session.identificador_sessao,
            },
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        result = {
            "id": user.cod_usuario,
            "name": user.nome,
            "login": user.login,
            "email": user.email,
            "role": AuthService._map_role(user.perfil),
            "active": user.ativo,
            "token": token,
            "access_token": token,
            "token_type": "bearer",
            "expiresAt": session.expira_em.isoformat(),
        }
        logger.info("Login completed for user_id=%s session=%s", user.cod_usuario, session.identificador_sessao)
        return result
