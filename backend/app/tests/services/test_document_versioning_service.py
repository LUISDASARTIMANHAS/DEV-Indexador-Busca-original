from datetime import date
from io import BytesIO
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.datastructures import UploadFile

from app.core.database import Base
from app.domain.document import Document
from app.domain.user import User
from app.domain.user_role import UserRole
from app.domain.document_history import DocumentHistory
from app.domain.document_metadata import DocumentMetadata
from app.domain.index_history import IndexHistory
from app.domain.ingestion_history import IngestionHistory
from app.exceptions.document_exceptions import DocumentNotFoundException
from app.services.document_service import document_service
from app.services.index_service import index_service
from app.services.search_service import search_service


def test_document_versioning_soft_delete_and_restore_keep_index_consistent(tmp_path: Path):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db: Session = session_local()
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
            filename="portaria.txt",
            file=BytesIO(b"conteudo legado original ifes"),
        )
        upload.headers = {"content-type": "text/plain"}
        payload = document_service.upload_document(
            db,
            file=upload,
            category="administrativo",
            uploaded_by=user,
            document_date=date(2026, 4, 20),
            title="Portaria",
            author="Secretaria",
            document_type="Portaria",
        )

        first_search = search_service.search(
            db,
            query="legado original",
            user_id=user.cod_usuario,
        )
        assert first_search["total"] == 1
        assert first_search["items"][0]["id"] == payload["id"]

        update_upload = UploadFile(
            filename="portaria-v2.txt",
            file=BytesIO(b"conteudo atualizado revisado ifes"),
        )
        update_upload.headers = {"content-type": "text/plain"}
        updated_payload = document_service.update_document(
            db,
            document_id=payload["id"],
            file=update_upload,
            updated_by=user,
            title="Portaria Atualizada",
            author="Secretaria Geral",
            document_type="Portaria",
        )
        assert updated_payload["version"] == 2

        versions = document_service.list_versions(db, payload["id"])
        assert [item["version"] for item in versions] == [2, 1]
        assert versions[0]["active"] is True
        assert versions[1]["active"] is False

        old_search = search_service.search(
            db,
            query="legado original",
            user_id=user.cod_usuario,
        )
        assert old_search["total"] == 0

        new_search = search_service.search(
            db,
            query="atualizado revisado",
            user_id=user.cod_usuario,
        )
        assert new_search["total"] == 1
        assert new_search["items"][0]["id"] == payload["id"]

        update_status = index_service.get_status_snapshot(db)
        assert update_status["integrityOk"] is True
        assert update_status["consistency"]["orphanIndexEntries"] == 0
        assert update_status["consistency"]["staleTerms"] == 0

        delete_payload = document_service.delete_document(
            db,
            document_id=payload["id"],
            deleted_by=user,
        )
        assert delete_payload["message"] == "Documento removido logicamente com sucesso."

        deleted_search = search_service.search(
            db,
            query="atualizado revisado",
            user_id=user.cod_usuario,
        )
        assert deleted_search["total"] == 0

        delete_status = index_service.get_status_snapshot(db)
        assert delete_status["integrityOk"] is True
        assert delete_status["consistency"]["orphanIndexEntries"] == 0
        assert delete_status["consistency"]["staleTerms"] == 0

        restored_payload = document_service.restore_version(
            db,
            document_id=payload["id"],
            version_number=1,
            restored_by=user,
        )
        assert restored_payload["version"] == 1

        restored_search = search_service.search(
            db,
            query="legado original",
            user_id=user.cod_usuario,
        )
        assert restored_search["total"] == 1
        assert restored_search["items"][0]["id"] == payload["id"]

        restore_status = index_service.get_status_snapshot(db)
        assert restore_status["integrityOk"] is True
        assert restore_status["consistency"]["orphanIndexEntries"] == 0
        assert restore_status["consistency"]["staleTerms"] == 0
    finally:
        document_service.storage_dir = original_storage_dir
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_document_physical_delete_removes_storage_metadata_and_index(tmp_path: Path):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db: Session = session_local()
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
            file=BytesIO(b"conteudo fisico original do documento ifes"),
        )
        upload.headers = {"content-type": "text/plain"}
        payload = document_service.upload_document(
            db,
            file=upload,
            category="administrativo",
            uploaded_by=user,
            document_date=date(2026, 5, 1),
            title="Resolucao Administrativa",
            author="Secretaria",
            document_type="Resolucao",
        )

        update_upload = UploadFile(
            filename="resolucao-v2.txt",
            file=BytesIO(b"conteudo fisico atualizado do documento ifes"),
        )
        update_upload.headers = {"content-type": "text/plain"}
        document_service.update_document(
            db,
            document_id=payload["id"],
            file=update_upload,
            updated_by=user,
            title="Resolucao Administrativa Atualizada",
            author="Secretaria Geral",
            document_type="Resolucao",
        )

        histories = (
            db.query(DocumentHistory)
            .filter(DocumentHistory.cod_documento == payload["id"])
            .order_by(DocumentHistory.numero_versao.asc())
            .all()
        )
        history_ids = [history.cod_historico_documento for history in histories]
        stored_files = [Path(history.caminho_arquivo) for history in histories]

        assert len(histories) == 2
        assert all(file_path.exists() for file_path in stored_files)
        assert db.query(Document).filter(Document.cod_documento == payload["id"]).count() == 1
        assert (
            db.query(DocumentMetadata)
            .filter(DocumentMetadata.cod_documento == payload["id"])
            .count()
            == 1
        )
        assert (
            db.query(IngestionHistory)
            .filter(IngestionHistory.cod_documento == payload["id"])
            .count()
            == 1
        )
        assert (
            db.query(IndexHistory)
            .filter(IndexHistory.cod_historico_documento.in_(history_ids))
            .count()
            == 2
        )

        purge_payload = document_service.purge_document(
            db,
            document_id=payload["id"],
            deleted_by=user,
        )
        assert purge_payload["message"] == "Documento removido fisicamente com sucesso."
        assert all(not file_path.exists() for file_path in stored_files)
        assert db.query(Document).filter(Document.cod_documento == payload["id"]).count() == 0
        assert (
            db.query(DocumentMetadata)
            .filter(DocumentMetadata.cod_documento == payload["id"])
            .count()
            == 0
        )
        assert (
            db.query(DocumentHistory)
            .filter(DocumentHistory.cod_documento == payload["id"])
            .count()
            == 0
        )
        assert (
            db.query(IngestionHistory)
            .filter(IngestionHistory.cod_documento == payload["id"])
            .count()
            == 0
        )
        assert (
            db.query(IndexHistory)
            .filter(IndexHistory.cod_historico_documento.in_(history_ids))
            .count()
            == 0
        )

        search_after_purge = search_service.search(
            db,
            query="conteudo fisico atualizado",
            user_id=user.cod_usuario,
        )
        assert search_after_purge["total"] == 0

        status = index_service.get_status_snapshot(db)
        assert status["indexedDocuments"] == 0
        assert status["integrityOk"] is True
        assert status["consistency"]["documentsWithoutIndex"] == 0
        assert status["consistency"]["orphanIndexEntries"] == 0

        with pytest.raises(DocumentNotFoundException):
            document_service.get_document_payload(db, payload["id"], active_only=False)
    finally:
        document_service.storage_dir = original_storage_dir
        db.close()
        Base.metadata.drop_all(bind=engine)
