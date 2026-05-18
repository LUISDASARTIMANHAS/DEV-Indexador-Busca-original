from collections.abc import Generator
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.main as main_module
from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import decode_token, hash_password
from app.domain.user import User
from app.domain.user_role import UserRole
from app.domain.user_session import UserSession
from app.main import app


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)

    db: Session = TestingSessionLocal()
    admin = User(
        nome="Administrador",
        login="admin",
        email="admin@ifes.edu.br",
        senha_hash=hash_password("admin123"),
        perfil=UserRole.ADMIN.value,
        ativo=True,
    )
    db.add(admin)
    db.commit()
    db.close()

    original_engine = main_module.engine
    main_module.engine = engine

    def override_get_db() -> Generator[Session, None, None]:
        override_db = TestingSessionLocal()
        try:
            yield override_db
        finally:
            override_db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    main_module.engine = original_engine
    Base.metadata.drop_all(bind=engine)


def login(client: TestClient, email: str, password: str) -> dict:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()


def test_login_success_returns_session_and_token(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@ifes.edu.br", "password": "admin123"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["email"] == "admin@ifes.edu.br"
    assert payload["login"] == "admin"
    assert payload["role"] == "Administrador"
    assert payload["token"]
    assert payload["access_token"] == payload["token"]
    assert payload["token_type"] == "bearer"
    assert payload["expiresAt"]



def test_login_rejects_invalid_credentials(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@ifes.edu.br", "password": "senha-errada"},
    )

    assert response.status_code == 401
    assert response.json()["message"] == "Usuário ou senha inválidos"



def test_me_returns_authenticated_user_profile(client: TestClient):
    session = login(client, "admin@ifes.edu.br", "admin123")

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {session['token']}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["email"] == "admin@ifes.edu.br"
    assert payload["perfil"] == UserRole.ADMIN.value
    assert payload["role"] == "Administrador"


def test_logout_revokes_current_session(client: TestClient):
    session = login(client, "admin@ifes.edu.br", "admin123")

    logout_response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {session['token']}"},
    )

    assert logout_response.status_code == 200
    assert logout_response.json()["message"] == "Sessão encerrada com sucesso."

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {session['token']}"},
    )
    assert me_response.status_code == 401
    assert me_response.json()["message"] == "Sessão encerrada."


def test_session_expires_after_inactivity(client: TestClient):
    session = login(client, "admin@ifes.edu.br", "admin123")
    payload = decode_token(session["token"])
    assert payload is not None

    session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=main_module.engine,
    )
    db: Session = session_local()
    try:
        current_session = (
            db.query(UserSession)
            .filter(UserSession.identificador_sessao == payload["sid"])
            .first()
        )
        assert current_session is not None
        current_session.ultimo_acesso_em = datetime.utcnow() - timedelta(
            minutes=settings.SESSION_IDLE_EXPIRE_MINUTES + 1
        )
        db.commit()
    finally:
        db.close()

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {session['token']}"},
    )
    assert me_response.status_code == 401
    assert me_response.json()["message"] == "Sessão expirada por inatividade."



def test_admin_can_create_user_and_profile_is_associated(client: TestClient):
    session = login(client, "admin@ifes.edu.br", "admin123")

    response = client.post(
        "/api/v1/users/",
        headers={"Authorization": f"Bearer {session['token']}"},
        json={
            "nome": "Usuário Teste",
            "login": "usuario.teste",
            "email": "usuario.teste@ifes.edu.br",
            "perfil": UserRole.USER.value,
            "ativo": True,
            "senha": "teste1234",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["login"] == "usuario.teste"
    assert payload["email"] == "usuario.teste@ifes.edu.br"
    assert payload["perfil"] == UserRole.USER.value
    assert payload["ativo"] is True



def test_non_admin_cannot_access_admin_routes(client: TestClient):
    admin_session = login(client, "admin@ifes.edu.br", "admin123")
    create_response = client.post(
        "/api/v1/users/",
        headers={"Authorization": f"Bearer {admin_session['token']}"},
        json={
            "nome": "Usuário Comum",
            "login": "usuario.comum",
            "email": "usuario.comum@ifes.edu.br",
            "perfil": UserRole.USER.value,
            "ativo": True,
            "senha": "teste1234",
        },
    )
    assert create_response.status_code == 201

    user_session = login(client, "usuario.comum@ifes.edu.br", "teste1234")
    response = client.get(
        "/api/v1/users/",
        headers={"Authorization": f"Bearer {user_session['token']}"},
    )

    assert response.status_code == 403
    assert response.json()["message"] == "Operação não permitida para o perfil do usuário."


def test_admin_history_is_logged_and_protected(client: TestClient):
    admin_session = login(client, "admin@ifes.edu.br", "admin123")

    create_response = client.post(
        "/api/v1/users/",
        headers={"Authorization": f"Bearer {admin_session['token']}"},
        json={
            "nome": "Usuário Auditoria",
            "login": "usuario.auditoria",
            "email": "usuario.auditoria@ifes.edu.br",
            "perfil": UserRole.USER.value,
            "ativo": True,
            "senha": "teste1234",
        },
    )
    assert create_response.status_code == 201

    history_response = client.get(
        "/api/v1/history/",
        headers={"Authorization": f"Bearer {admin_session['token']}"},
    )
    assert history_response.status_code == 200
    history_payload = history_response.json()
    assert len(history_payload) >= 1
    assert history_payload[0]["action"] == "Criação de Usuário"

    user_session = login(client, "usuario.auditoria@ifes.edu.br", "teste1234")
    forbidden_response = client.get(
        "/api/v1/history/",
        headers={"Authorization": f"Bearer {user_session['token']}"},
    )
    assert forbidden_response.status_code == 403
