from datetime import date, datetime, time as dt_time, timedelta
from io import BytesIO
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.datastructures import UploadFile

from app.core.database import Base
from app.domain.document_access_history import DocumentAccessHistory
from app.domain.search_history import SearchHistory
from app.domain.user import User
from app.domain.user_role import UserRole
from app.services.document_service import document_service
from app.services.metrics_service import metrics_service


def test_metrics_snapshot_calculates_search_performance_indicators(tmp_path: Path):
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

        first_upload = UploadFile(
            filename="portaria.txt",
            file=BytesIO(b"Portaria institucional do IFES para fluxos administrativos."),
        )
        first_upload.headers = {"content-type": "text/plain"}
        document_service.upload_document(
            db,
            file=first_upload,
            category="administrativo",
            uploaded_by=user,
            document_date=date(2026, 5, 10),
            title="Portaria Institucional",
            author="Secretaria",
            document_type="Portaria",
        )

        second_upload = UploadFile(
            filename="relatorio.txt",
            file=BytesIO(b"Relatorio de pesquisa institucional com resultados preliminares."),
        )
        second_upload.headers = {"content-type": "text/plain"}
        document_service.upload_document(
            db,
            file=second_upload,
            category="pesquisa",
            uploaded_by=user,
            document_date=date(2026, 5, 11),
            title="Relatorio de Pesquisa",
            author="Coordenacao",
            document_type="Relatorio",
        )

        today = date.today()
        search_events = [
            SearchHistory(
                cod_usuario=user.cod_usuario,
                consulta_texto="portaria ifes",
                filtros=None,
                quantidade_resultados=2,
                tempo_resposta_ms=120,
                criado_em=datetime.combine(today, dt_time(hour=10, minute=0)),
            ),
            SearchHistory(
                cod_usuario=user.cod_usuario,
                consulta_texto="relatorio pesquisa",
                filtros=None,
                quantidade_resultados=0,
                tempo_resposta_ms=300,
                criado_em=datetime.combine(today - timedelta(days=1), dt_time(hour=11, minute=30)),
            ),
            SearchHistory(
                cod_usuario=user.cod_usuario,
                consulta_texto="portaria interna",
                filtros=None,
                quantidade_resultados=1,
                tempo_resposta_ms=180,
                criado_em=datetime.combine(today - timedelta(days=6), dt_time(hour=9, minute=15)),
            ),
        ]
        db.add_all(search_events)
        db.commit()

        snapshot = metrics_service.snapshot(db)

        assert snapshot["overview"]["totalQueries"] == 3
        assert snapshot["overview"]["averageSearchTime"] == "200 ms"
        assert snapshot["overview"]["indexedDocuments"] == 2
        assert snapshot["overview"]["averageResults"] == "1.0"
        assert snapshot["overview"]["queriesToday"] == 1
        assert snapshot["overview"]["queriesWithoutResults"] == 1
        assert snapshot["overview"]["zeroResultsRate"] == "33.3%"
        assert len(snapshot["queriesByDay"]) == 7
        assert sum(point["consultas"] for point in snapshot["queriesByDay"]) == 3
        assert snapshot["queryOutcomeDistribution"] == [
            {"name": "Com resultados", "value": 2},
            {"name": "Sem resultados", "value": 1},
        ]
        assert snapshot["recentCalculations"] == []
        assert snapshot["topTerms"][0] == {"name": "portaria", "value": 2}
        assert any(term["name"] == "ifes" for term in snapshot["topTerms"])
        assert {item["name"] for item in snapshot["documentsByCategory"]} == {
            "administrativo",
            "pesquisa",
        }
    finally:
        document_service.storage_dir = original_storage_dir
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_metrics_report_persists_calculations_tracks_accesses_and_exports(tmp_path: Path):
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

        first_payload = document_service.upload_document(
            db,
            file=_upload_file(
                "portaria.txt",
                b"Portaria institucional com orientacoes para pesquisa aplicada.",
            ),
            category="administrativo",
            uploaded_by=user,
            document_date=date(2026, 5, 10),
            title="Portaria Institucional",
            author="Secretaria",
            document_type="Portaria",
        )
        second_payload = document_service.upload_document(
            db,
            file=_upload_file(
                "edital.txt",
                b"Edital institucional com regras de participacao em projeto.",
            ),
            category="pesquisa",
            uploaded_by=user,
            document_date=date(2026, 5, 11),
            title="Edital de Projeto",
            author="Proppi",
            document_type="Edital",
        )

        metrics_service.register_document_access(
            db,
            document_id=first_payload["id"],
            user_id=user.cod_usuario,
            access_type="view",
            origin="test-view",
        )
        metrics_service.register_document_access(
            db,
            document_id=first_payload["id"],
            user_id=user.cod_usuario,
            access_type="download",
            origin="test-download",
        )
        metrics_service.register_document_access(
            db,
            document_id=second_payload["id"],
            user_id=user.cod_usuario,
            access_type="view",
            origin="test-view",
        )
        access_rows = (
            db.query(DocumentAccessHistory)
            .order_by(DocumentAccessHistory.cod_acesso_documento.asc())
            .all()
        )
        access_rows[0].criado_em = datetime(2026, 5, 12, 8, 0, 0)
        access_rows[1].criado_em = datetime(2026, 5, 12, 8, 5, 0)
        access_rows[2].criado_em = datetime(2026, 5, 13, 8, 0, 0)
        db.commit()

        search_events = [
            SearchHistory(
                cod_usuario=user.cod_usuario,
                consulta_texto="portaria institucional",
                filtros=None,
                quantidade_resultados=2,
                tempo_resposta_ms=140,
                criado_em=datetime(2026, 5, 12, 10, 0, 0),
            ),
            SearchHistory(
                cod_usuario=user.cod_usuario,
                consulta_texto="portaria institucional",
                filtros=None,
                quantidade_resultados=1,
                tempo_resposta_ms=120,
                criado_em=datetime(2026, 5, 12, 11, 0, 0),
            ),
            SearchHistory(
                cod_usuario=user.cod_usuario,
                consulta_texto="projeto sem retorno",
                filtros=None,
                quantidade_resultados=0,
                tempo_resposta_ms=260,
                criado_em=datetime(2026, 5, 13, 9, 30, 0),
            ),
        ]
        db.add_all(search_events)
        db.commit()

        report = metrics_service.build_report(
            db,
            date_from=date(2026, 5, 12),
            date_to=date(2026, 5, 13),
            include_stored_calculation=False,
        )

        assert report["summary"]["totalQueries"] == 3
        assert report["summary"]["uniqueQueries"] == 2
        assert report["summary"]["averageResponseTimeMs"] == 173
        assert report["summary"]["queriesWithoutResults"] == 1
        assert report["summary"]["zeroResultsRate"] == "33.3%"
        assert report["summary"]["mostFrequentQuery"] == "portaria institucional"
        assert report["summary"]["mostAccessedDocument"] == "Portaria Institucional"
        assert report["frequentQueries"][0]["query"] == "portaria institucional"
        assert report["frequentQueries"][0]["count"] == 2
        assert report["zeroResultQueries"][0]["query"] == "projeto sem retorno"
        assert report["accessedDocuments"][0]["title"] == "Portaria Institucional"
        assert report["accessedDocuments"][0]["accessCount"] == 2
        assert report["accessedDocuments"][0]["downloadCount"] == 1
        assert any(term["name"] == "portaria" for term in report["topTerms"])

        calculation = metrics_service.persist_calculation(
            db,
            date_from=date(2026, 5, 12),
            date_to=date(2026, 5, 13),
        )
        assert calculation["totalQueries"] == 3
        assert calculation["averageResponseTimeMs"] == 173
        assert calculation["queriesWithoutResults"] == 1

        calculations = metrics_service.list_calculations(db, limit=5)
        assert len(calculations) == 1
        assert calculations[0]["id"] == calculation["id"]

        snapshot = metrics_service.snapshot(db)
        assert snapshot["recentCalculations"][0]["id"] == calculation["id"]

        csv_content, csv_filename, csv_media_type = metrics_service.export_report(
            db,
            export_format="csv",
            date_from=date(2026, 5, 12),
            date_to=date(2026, 5, 13),
        )
        assert "frequentQueries" in csv_content
        assert "portaria institucional" in csv_content
        assert csv_filename.endswith(".csv")
        assert csv_media_type == "text/csv; charset=utf-8"

        json_content, json_filename, json_media_type = metrics_service.export_report(
            db,
            export_format="json",
            date_from=date(2026, 5, 12),
            date_to=date(2026, 5, 13),
        )
        assert '"mostAccessedDocument": "Portaria Institucional"' in json_content
        assert json_filename.endswith(".json")
        assert json_media_type == "application/json; charset=utf-8"
    finally:
        document_service.storage_dir = original_storage_dir
        db.close()
        Base.metadata.drop_all(bind=engine)


def _upload_file(filename: str, content: bytes) -> UploadFile:
    upload = UploadFile(filename=filename, file=BytesIO(content))
    upload.headers = {"content-type": "text/plain"}
    return upload
