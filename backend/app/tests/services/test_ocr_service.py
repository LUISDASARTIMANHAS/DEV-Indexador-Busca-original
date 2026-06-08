import sys
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.main as main_module
from app.adapters.ocr_adapter import OCRAdapter
from app.core.database import Base, get_db
from app.core.security import hash_password
from app.domain.document import Document
from app.domain.document_category import DocumentCategory
from app.domain.document_history import DocumentHistory
from app.domain.ocr_history import OCRHistory
from app.domain.user import User
from app.domain.user_role import UserRole
from app.main import app
from app.services.ocr_service import OCRService, ocr_service


def test_should_run_ocr_when_text_is_empty():
    service = OCRService()
    assert service.should_run_ocr("") is True
    assert service.should_run_ocr("   ") is True


def test_should_not_run_ocr_when_text_is_sufficient():
    service = OCRService()
    assert service.should_run_ocr("texto suficiente " * 20) is False


def test_ocr_adapter_extracts_text_from_pages(monkeypatch, tmp_path: Path):
    pdf_path = tmp_path / "scan.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")

    monkeypatch.setitem(
        sys.modules,
        "pdf2image",
        SimpleNamespace(convert_from_path=lambda *args, **kwargs: ["page-1", "page-2"]),
    )
    monkeypatch.setitem(
        sys.modules,
        "pytesseract",
        SimpleNamespace(image_to_string=lambda image, **kwargs: f"texto {image}"),
    )

    result = OCRAdapter().extract_text_from_pdf(str(pdf_path), language="por", dpi=200, max_pages=2)

    assert result["success"] is True
    assert result["pages_processed"] == 2
    assert "--- Página 1 ---" in result["text"]
    assert "texto page-2" in result["text"]


def test_ocr_adapter_returns_structured_failure(monkeypatch, tmp_path: Path):
    pdf_path = tmp_path / "invalid.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")

    def fail_convert(*args, **kwargs):
        raise RuntimeError("poppler indisponível")

    monkeypatch.setitem(
        sys.modules,
        "pdf2image",
        SimpleNamespace(convert_from_path=fail_convert),
    )
    monkeypatch.setitem(
        sys.modules,
        "pytesseract",
        SimpleNamespace(image_to_string=lambda image, **kwargs: ""),
    )

    result = OCRAdapter().extract_text_from_pdf(str(pdf_path))

    assert result["success"] is False
    assert "poppler" in result["error"]


def _sqlite_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine, session_local


def _seed_document(db: Session, tmp_path: Path) -> tuple[User, DocumentHistory]:
    user = User(
        nome="Administrador",
        login="admin",
        email="admin@ifes.edu.br",
        senha_hash=hash_password("admin123"),
        perfil=UserRole.ADMIN.value,
        ativo=True,
    )
    category = DocumentCategory(nome_categoria="administrativo")
    db.add_all([user, category])
    db.commit()
    db.refresh(user)
    db.refresh(category)

    document = Document(
        titulo="Ata escaneada",
        tipo="PDF",
        cod_categoria=category.cod_categoria,
        cod_usuario_criador=user.cod_usuario,
        ativo=True,
    )
    db.add(document)
    db.flush()
    pdf_path = tmp_path / "ata.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")
    history = DocumentHistory(
        cod_documento=document.cod_documento,
        cod_usuario=user.cod_usuario,
        numero_versao=1,
        caminho_arquivo=str(pdf_path),
        nome_arquivo_original="ata.pdf",
        mime_type="application/pdf",
        tamanho_bytes=pdf_path.stat().st_size,
        hash_arquivo="hash",
        texto_extraido="",
        texto_processado="",
        versao_ativa=True,
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return user, history


def test_ocr_service_updates_document_version(monkeypatch, tmp_path: Path):
    engine, session_local = _sqlite_session()
    db: Session = session_local()
    try:
        _, history = _seed_document(db, tmp_path)
        service = OCRService()
        monkeypatch.setattr(
            service.adapter,
            "extract_text_from_pdf",
            lambda *args, **kwargs: {
                "text": "conteudo extraido por OCR sobre estagio supervisionado",
                "pages_processed": 2,
                "language": "por",
                "dpi": 200,
                "success": True,
                "error": None,
                "processing_time_ms": 1234,
            },
        )

        result = service.run_ocr_for_document_version(
            db,
            document_id=history.cod_documento,
            force=True,
        )

        db.refresh(history)
        assert result["ocr_executed"] is True
        assert result["success"] is True
        assert history.ocr_status == "success"
        assert "estagio supervisionado" in history.texto_extraido
        assert db.query(OCRHistory).count() == 1
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_ocr_endpoint_runs_manual_processing(monkeypatch, tmp_path: Path):
    engine, session_local = _sqlite_session()
    db: Session = session_local()
    user, history = _seed_document(db, tmp_path)
    user_email = user.email
    document_id = history.cod_documento
    db.close()

    original_engine = main_module.engine
    main_module.engine = engine

    def override_get_db():
        override_db = session_local()
        try:
            yield override_db
        finally:
            override_db.close()

    monkeypatch.setattr(
        ocr_service.adapter,
        "extract_text_from_pdf",
        lambda *args, **kwargs: {
            "text": "texto pesquisavel gerado por OCR",
            "pages_processed": 1,
            "language": "por",
            "dpi": 200,
            "success": True,
            "error": None,
            "processing_time_ms": 900,
        },
    )

    def fake_reindex(db, document_id, triggered_by):
        db.commit()
        return {"documentId": document_id, "termCount": 4, "tokenCount": 4}

    monkeypatch.setattr("app.services.ocr_service.index_service.reindex_document", fake_reindex)
    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            token = client.post(
                "/api/v1/auth/login",
                json={"email": user_email, "password": "admin123"},
            ).json()["token"]
            response = client.post(
                f"/api/v1/ocr/document/{document_id}",
                headers={"Authorization": f"Bearer {token}"},
                params={"force": True},
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["ocr_executed"] is True
        assert payload["success"] is True
        assert payload["pages_processed"] == 1
    finally:
        app.dependency_overrides.clear()
        main_module.engine = original_engine
        Base.metadata.drop_all(bind=engine)
