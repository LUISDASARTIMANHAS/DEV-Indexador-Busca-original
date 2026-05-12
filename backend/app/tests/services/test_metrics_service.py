from datetime import date, datetime, time as dt_time, timedelta
from io import BytesIO
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.datastructures import UploadFile

from app.core.database import Base
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
