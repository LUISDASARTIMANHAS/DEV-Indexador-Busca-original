from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base
from app.core.security import decode_token, hash_password
from app.domain.user import User
from app.domain.user_role import UserRole
from app.repositories.session_repository import SessionRepository
from app.services.auth_service import AuthService


def test_auth_service_creates_validates_and_revokes_sessions():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db: Session = session_local()

    try:
        user = User(
            nome="Administrador",
            login="admin",
            email="admin@ifes.edu.br",
            senha_hash=hash_password("admin123"),
            perfil=UserRole.ADMIN.value,
            ativo=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        session_payload = AuthService.login(db, "admin@ifes.edu.br", "admin123")
        token_payload = decode_token(session_payload["token"])
        assert token_payload is not None
        assert token_payload["sub"] == str(user.cod_usuario)
        assert token_payload["sid"]

        active_session = AuthService.validate_session(
            db,
            session_id=token_payload["sid"],
            user_id=user.cod_usuario,
        )
        assert active_session.cod_usuario == user.cod_usuario

        logout_payload = AuthService.logout(
            db,
            session_id=token_payload["sid"],
        )
        assert logout_payload["message"] == "Sessão encerrada com sucesso."

        with pytest.raises(Exception) as exc_info:
            AuthService.validate_session(
                db,
                session_id=token_payload["sid"],
                user_id=user.cod_usuario,
            )
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Sessão encerrada."
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_auth_service_expires_session_after_inactivity():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db: Session = session_local()

    try:
        user = User(
            nome="Administrador",
            login="admin",
            email="admin@ifes.edu.br",
            senha_hash=hash_password("admin123"),
            perfil=UserRole.ADMIN.value,
            ativo=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        session_payload = AuthService.login(db, "admin@ifes.edu.br", "admin123")
        token_payload = decode_token(session_payload["token"])
        assert token_payload is not None

        repository = SessionRepository()
        current_session = repository.get_by_identifier(db, token_payload["sid"])
        assert current_session is not None
        current_session.ultimo_acesso_em = datetime.utcnow() - timedelta(
            minutes=settings.SESSION_IDLE_EXPIRE_MINUTES + 1
        )
        repository.save(db, current_session)

        with pytest.raises(Exception) as exc_info:
            AuthService.validate_session(
                db,
                session_id=token_payload["sid"],
                user_id=user.cod_usuario,
            )
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Sessão expirada por inatividade."
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
