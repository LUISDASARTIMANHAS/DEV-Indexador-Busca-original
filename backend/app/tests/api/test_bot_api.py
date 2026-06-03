from collections.abc import Generator
from pathlib import Path

import app.main as main_module
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.domain.user import User
from app.domain.user_role import UserRole
from app.main import app
from app.services.document_service import document_service


def _login(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@ifes.edu.br", "password": "admin123"},
    )
    assert response.status_code == 200
    return response.json()["token"]


def _upload_with_metadata(
    client: TestClient,
    token: str,
    file_name: str,
    content: bytes,
    *,
    category: str,
    document_type: str,
    document_date: str,
):
    response = client.post(
        "/api/v1/ingestion/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (file_name, content, "text/plain")},
        data={
            "category": category,
            "document_type": document_type,
            "document_date": document_date,
        },
    )
    assert response.status_code == 201
    return response.json()


def _client_fixture(tmp_path: Path) -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db: Session = testing_session_local()
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
    original_storage_dir = document_service.storage_dir
    document_service.storage_dir = tmp_path / "documents"
    main_module.engine = engine

    def override_get_db() -> Generator[Session, None, None]:
        override_db = testing_session_local()
        try:
            yield override_db
        finally:
            override_db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    main_module.engine = original_engine
    document_service.storage_dir = original_storage_dir
    Base.metadata.drop_all(bind=engine)


def test_bot_test_endpoint_searches_documents_and_keeps_short_memory(tmp_path: Path):
    for client in _client_fixture(tmp_path):
        token = _login(client)
        uploaded = _upload_with_metadata(
            client,
            token,
            "relatorio-estagio-2025.txt",
            b"Relatorio de estagio supervisionado com orientacoes do IFES.",
            category="academico",
            document_type="Relatorio",
            document_date="2025-05-10",
        )

        search_response = client.post(
            "/api/v1/bot/test",
            json={
                "channel": "test",
                "external_user_id": "lucas",
                "message": "buscar documentos sobre estágio supervisionado",
            },
        )

        assert search_response.status_code == 200
        search_payload = search_response.json()
        assert search_payload["intent"] == "search_documents"
        assert search_payload["success"] is True
        assert search_payload["results"][0]["id"] == uploaded["id"]
        assert "Encontrei" in search_payload["response_text"]

        details_response = client.post(
            "/api/v1/bot/test",
            json={
                "channel": "test",
                "external_user_id": "lucas",
                "message": "detalhes 1",
            },
        )

        assert details_response.status_code == 200
        details_payload = details_response.json()
        assert details_payload["intent"] == "get_document_details"
        assert details_payload["success"] is True
        assert str(uploaded["id"]) in details_payload["response_text"]


def test_bot_test_endpoint_help_and_unknown_messages(tmp_path: Path):
    for client in _client_fixture(tmp_path):
        help_response = client.post(
            "/api/v1/bot/test",
            json={"channel": "test", "external_user_id": "u1", "message": "ajuda"},
        )
        unknown_response = client.post(
            "/api/v1/bot/test",
            json={"channel": "test", "external_user_id": "u1", "message": "banana azul"},
        )

        assert help_response.status_code == 200
        assert "buscar documentos" in help_response.json()["response_text"].lower()
        assert unknown_response.status_code == 200
        assert unknown_response.json()["intent"] == "unknown"
        assert unknown_response.json()["success"] is False


def test_bot_telegram_webhook_accepts_simulated_payload(tmp_path: Path):
    for client in _client_fixture(tmp_path):
        response = client.post(
            "/api/v1/bot/telegram/webhook",
            json={
                "message": {
                    "chat": {"id": 123456},
                    "text": "ajuda",
                }
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["intent"] == "help"
        assert payload["sent"] is False
        assert "buscar documentos" in payload["response_text"].lower()


def test_bot_whatsapp_webhook_accepts_simulated_payload(tmp_path: Path):
    for client in _client_fixture(tmp_path):
        response = client.post(
            "/api/v1/bot/whatsapp/webhook",
            json={
                "entry": [
                    {
                        "changes": [
                            {
                                "value": {
                                    "messages": [
                                        {
                                            "from": "559999999999",
                                            "text": {"body": "ajuda"},
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ]
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["intent"] == "help"
        assert payload["sent"] is False
        assert "buscar documentos" in payload["response_text"].lower()
