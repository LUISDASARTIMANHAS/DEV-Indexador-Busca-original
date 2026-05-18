from datetime import date
from io import BytesIO
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.datastructures import UploadFile

from app.core.database import Base
from app.domain.user import User
from app.domain.user_role import UserRole
from app.services.document_service import document_service


def test_document_storage_persists_file_metadata_and_export(tmp_path: Path):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = session_local()
    original_storage_dir = document_service.storage_dir
    document_service.storage_dir = tmp_path / "documents"

    try:
        user = User(
            nome="Administrador",
            login="admin",
            email="admin@ifes.edu.br",
            senha_hash="hash",
            perfil=UserRole.ADMIN.value,
            ativo=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        upload = UploadFile(
            filename="resolucao.txt",
            file=BytesIO(b"Conteudo institucional completo do IFES para leitura e exportacao."),
        )
        upload.headers = {"content-type": "text/plain"}
        payload = document_service.upload_document(
            db,
            file=upload,
            category="administrativo",
            uploaded_by=user,
            document_date=date(2026, 4, 27),
            title="Resolucao de Teste",
            author="Conselho Superior",
            document_type="Resolucao",
        )

        file_path = Path(payload["file_path"])
        assert file_path.exists()
        assert payload["title"] == "Resolucao de Teste"
        assert payload["author_name"] == "Conselho Superior"
        assert payload["document_type"] == "Resolucao"
        assert payload["category"] == "administrativo"
        assert payload["type"] == "TXT"

        details = document_service.to_details_response(payload)
        metadata = document_service.to_metadata_response(payload)
        txt_content, txt_filename, txt_media_type = document_service.export_document(
            db,
            document_id=payload["id"],
            export_format="txt",
        )
        json_content, json_filename, json_media_type = document_service.export_document(
            db,
            document_id=payload["id"],
            export_format="json",
        )
        original_file, original_name, original_media_type = document_service.get_document_file(
            db,
            payload["id"],
        )

        assert details["downloadUrl"] == f"/api/v1/documents/{payload['id']}/download"
        assert details["displayTitle"] == "Resolucao de Teste"
        assert details["content"].startswith("Conteudo institucional completo")
        assert details["formattedContent"].startswith("Conteudo institucional completo")
        assert metadata["author"] == "Conselho Superior"
        assert metadata["documentType"] == "Resolucao"
        assert metadata["publicationDate"] == "2026-04-27T00:00:00"
        assert "Conteúdo extraído:" in txt_content
        assert "Conselho Superior" in txt_content
        assert txt_filename == "Resolucao_de_Teste.txt"
        assert txt_media_type == "text/plain; charset=utf-8"
        assert '"author": "Conselho Superior"' in json_content
        assert json_filename == "Resolucao_de_Teste.json"
        assert json_media_type == "application/json; charset=utf-8"
        assert original_file.exists()
        assert original_name == "resolucao.txt"
        assert original_media_type == "text/plain"
    finally:
        document_service.storage_dir = original_storage_dir
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_document_storage_formats_reading_content_and_humanizes_filename_title(tmp_path: Path):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = session_local()
    original_storage_dir = document_service.storage_dir
    document_service.storage_dir = tmp_path / "documents"

    try:
        user = User(
            nome="Administrador",
            login="admin",
            email="admin@ifes.edu.br",
            senha_hash="hash",
            perfil=UserRole.ADMIN.value,
            ativo=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        upload = UploadFile(
            filename="Resolucao_CS_72_2021_-_Programa_de_Estagio.txt",
            file=BytesIO(
                b"Ministerio da Educacao\n"
                b"Secretaria de Educacao Profissional e Tecnologica\n\n"
                b"Art. 1o Esta resolucao estabelece normas para o programa\n"
                b"de estagio docente.\n"
                b"I - primeira regra aplicavel\n"
                b"II - segunda regra aplicavel."
            ),
        )
        upload.headers = {"content-type": "text/plain"}
        payload = document_service.upload_document(
            db,
            file=upload,
            category="administrativo",
            uploaded_by=user,
            author="Secretaria",
            document_type="Resolucao",
        )

        details = document_service.to_details_response(payload)

        assert payload["title"] == "Resolucao CS 72 2021 - Programa de Estagio"
        assert details["displayTitle"] == "Resolucao CS 72 2021 - Programa de Estagio"
        assert details["content"] != details["formattedContent"]
        assert (
            "Art. 1o Esta resolucao estabelece normas para o programa de estagio docente."
            in details["formattedContent"]
        )
        assert "Ministerio da Educacao\n\nSecretaria de Educacao Profissional e Tecnologica" in details["formattedContent"]
    finally:
        document_service.storage_dir = original_storage_dir
        db.close()
        Base.metadata.drop_all(bind=engine)
