from datetime import date
from io import BytesIO

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.datastructures import UploadFile

from app.core.database import Base
from app.domain.user import User
from app.domain.user_role import UserRole
from app.repositories.postgres_search_repository import PostgresSearchRepository
from app.services.document_service import document_service
from app.services.query_analyzer_service import QueryAnalyzer
from app.services.search_service import search_service
from app.strategies.hybrid_postgres_strategy import HybridPostgresSearchStrategy


def _db_with_document(tmp_path):
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
        filename="relatorio-estagio-2025.txt",
        file=BytesIO(b"Relatorio de estagio supervisionado com normas e acompanhamento."),
    )
    upload.headers = {"content-type": "text/plain"}
    document = document_service.upload_document(
        db,
        file=upload,
        category="academico",
        uploaded_by=user,
        document_date=date(2025, 5, 10),
        title="Relatorio de Estagio 2025",
        author="Coordenacao",
        document_type="Relatorio",
    )
    return engine, db, user, document, original_storage_dir


def test_postgres_fts_repository_fallback_returns_standardized_results(tmp_path):
    engine, db, _user, document, original_storage_dir = _db_with_document(tmp_path)
    try:
        rows = PostgresSearchRepository().search_full_text(
            db,
            query="estagio supervisionado",
            limit=5,
            filters={"year": 2025, "document_type": "txt", "category": "academico"},
        )

        assert rows
        assert rows[0]["document_id"] == document["id"]
        assert rows[0]["score"] > 0
        assert "<mark>" in rows[0]["snippet"]
    finally:
        document_service.storage_dir = original_storage_dir
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_search_service_uses_query_analyzer_with_postgres_fts(tmp_path):
    engine, db, user, document, original_storage_dir = _db_with_document(tmp_path)
    try:
        result = search_service.search(
            db,
            query="relatórios de estágio 2025 txt",
            user_id=user.cod_usuario,
            mode="postgres_fts",
            debug_analysis=True,
            limit=5,
            page=1,
        )

        assert result["mode"] == "postgres_fts"
        assert result["analysis"]["filters"]["year"] == 2025
        assert result["analysis"]["filters"]["type"] == "txt"
        assert result["items"][0]["id"] == document["id"]
        assert result["items"][0]["postgresScore"] is not None
        assert "<mark>" in result["items"][0]["snippet"]
    finally:
        document_service.storage_dir = original_storage_dir
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_hybrid_postgres_strategy_combines_scores_by_document_id():
    combined = HybridPostgresSearchStrategy().combine(
        postgres_items=[
            {"document_id": 1, "postgres_score": 0.8, "score": 0.8, "matched_terms": {"estagio"}},
            {"document_id": 2, "postgres_score": 0.4, "score": 0.4, "matched_terms": {"relatorio"}},
        ],
        secondary_items=[
            {"document_id": 2, "final_score": 3.0, "matched_terms": {"relatorio"}},
            {"document_id": 3, "final_score": 1.5, "matched_terms": {"manual"}},
        ],
        postgres_weight=0.7,
        secondary_weight=0.3,
    )

    assert combined[0]["document_id"] == 1
    assert combined[0]["search_mode"] == "hybrid_postgres"
    assert combined[1]["document_id"] == 2
    assert combined[1]["secondary_score"] == 3.0


def test_query_analyzer_recognizes_plural_file_type_aliases():
    analysis = QueryAnalyzer().analyze("mostrar PDFs de 2025 sobre estágio")

    assert analysis.filters.type == "pdf"
