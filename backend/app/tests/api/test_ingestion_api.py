from collections.abc import Generator
from pathlib import Path

import app.main as main_module
import pytest
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


@pytest.fixture()
def client(tmp_path: Path) -> Generator[TestClient, None, None]:
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


def login(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@ifes.edu.br", "password": "admin123"},
    )
    assert response.status_code == 200
    return response.json()["token"]


def test_upload_document_persists_file_and_metadata(client: TestClient):
    token = login(client)
    files = {
        "file": ("resolucao.txt", b"conteudo institucional do IFES", "text/plain"),
    }
    data = {"category": "administrativo", "document_date": "2026-03-24"}

    response = client.post(
        "/api/v1/ingestion/upload",
        headers={"Authorization": f"Bearer {token}"},
        files=files,
        data=data,
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["fileName"] == "resolucao.txt"
    assert payload["category"] == "administrativo"
    assert payload["type"] == "TXT"
    assert payload["validated"] is True
    assert payload["integrityOk"] is True
    assert (document_service.storage_dir).exists()
    assert any((document_service.storage_dir).iterdir())


def test_upload_document_rejects_invalid_extension(client: TestClient):
    token = login(client)
    files = {
        "file": ("malware.exe", b"MZ-binary", "application/octet-stream"),
    }

    response = client.post(
        "/api/v1/ingestion/upload",
        headers={"Authorization": f"Bearer {token}"},
        files=files,
        data={"category": "administrativo"},
    )

    assert response.status_code == 400
    assert response.json()["message"] == "Tipo de arquivo inválido. Formatos aceitos: CSV, DOCX, PDF, TXT."

    history_response = client.get(
        "/api/v1/ingestion/history",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert history_response.status_code == 200
    assert history_response.json()[0]["file"] == "malware.exe"
    assert history_response.json()[0]["result"] == "Falha"


def test_upload_document_rejects_empty_category(client: TestClient):
    token = login(client)
    response = client.post(
        "/api/v1/ingestion/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("sem-categoria.txt", b"conteudo valido", "text/plain")},
        data={"category": "   "},
    )

    assert response.status_code == 400
    assert response.json()["message"] == "Informe uma categoria válida para o documento."


def test_ingestion_history_lists_uploaded_document(client: TestClient):
    token = login(client)
    upload_response = client.post(
        "/api/v1/ingestion/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("ata.csv", b"coluna\nvalor", "text/csv")},
        data={"category": "academico"},
    )
    assert upload_response.status_code == 201

    history_response = client.get(
        "/api/v1/ingestion/history",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert history_response.status_code == 200
    payload = history_response.json()
    assert len(payload) == 1
    assert payload[0]["file"] == "ata.csv"
    assert payload[0]["result"] == "Sucesso"


def test_batch_upload_processes_multiple_files(client: TestClient):
    token = login(client)

    response = client.post(
        "/api/v1/ingestion/upload-batch",
        headers={"Authorization": f"Bearer {token}"},
        files=[
            ("files", ("arquivo1.txt", b"conteudo um", "text/plain")),
            ("files", ("arquivo2.csv", b"coluna\nvalor", "text/csv")),
        ],
        data={"category": "pesquisa"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["totalFiles"] == 2
    assert payload["successCount"] == 2
    assert payload["failureCount"] == 0
    assert payload["items"][0]["status"] == "indexed"
