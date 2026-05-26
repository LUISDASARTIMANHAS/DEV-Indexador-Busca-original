import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.domain.search_history import SearchHistory
from app.domain.user import User
from app.services.metrics_service import metrics_service

# Setup in-memory database for testing
SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_metrics_snapshot_includes_top_queries(db):
    # Setup: Create some search history
    user = User(
        nome="Test User",
        login="testuser",
        email="test@example.com",
        senha_hash="hash",
        perfil="ADMIN",
    )
    db.add(user)
    db.commit()

    # Add multiple searches
    searches = [
        "python", "python", "python",
        "fastapi", "fastapi",
        "sql",
    ]
    for query in searches:
        history = SearchHistory(
            cod_usuario=user.cod_usuario,
            consulta_texto=query,
            quantidade_resultados=10,
            tempo_resposta_ms=100,
        )
        db.add(history)
    
    # Add a search with no results
    history_no_results = SearchHistory(
        cod_usuario=user.cod_usuario,
        consulta_texto="no results",
        quantidade_resultados=0,
        tempo_resposta_ms=50,
    )
    db.add(history_no_results)
    db.commit()

    # Execute
    snapshot = metrics_service.snapshot(db)

    # Verify
    assert "overview" in snapshot
    assert snapshot["overview"]["totalQueries"] == 7
    assert snapshot["overview"]["queriesWithoutResults"] == 1
    
    assert "topQueries" in snapshot
    top_queries = snapshot["topQueries"]
    assert len(top_queries) > 0
    assert top_queries[0]["name"] == "python"
    assert top_queries[0]["value"] == 3
    assert top_queries[1]["name"] == "fastapi"
    assert top_queries[1]["value"] == 2

def test_build_report_stats(db):
    # Setup: Create search history
    user = User(
        nome="Test User",
        login="testuser",
        email="test@example.com",
        senha_hash="hash",
        perfil="ADMIN",
    )
    db.add(user)
    db.commit()

    db.add(SearchHistory(
        cod_usuario=user.cod_usuario,
        consulta_texto="test query",
        quantidade_resultados=5,
        tempo_resposta_ms=200,
    ))
    db.commit()

    # Execute
    report = metrics_service.build_report(db)

    # Verify
    assert report["summary"]["totalQueries"] == 1
    assert report["summary"]["averageResponseTimeMs"] == 200
    assert len(report["frequentQueries"]) == 1
    assert report["frequentQueries"][0]["query"] == "test query"
    assert report["frequentQueries"][0]["count"] == 1

def test_persist_calculation(db):
    # Setup
    user = User(
        nome="Test User",
        login="testuser",
        email="test@example.com",
        senha_hash="hash",
        perfil="ADMIN",
    )
    db.add(user)
    db.commit()

    db.add(SearchHistory(
        cod_usuario=user.cod_usuario,
        consulta_texto="test query",
        quantidade_resultados=5,
        tempo_resposta_ms=200,
    ))
    db.commit()

    # Execute
    calculation = metrics_service.persist_calculation(db)

    # Verify
    assert calculation["totalQueries"] == 1
    assert calculation["averageResponseTimeMs"] == 200
    assert calculation["queriesWithoutResults"] == 0
    
    # Check if it was saved in DB
    from app.domain.metric_calculation import MetricCalculation
    record = db.query(MetricCalculation).first()
    assert record is not None
    assert record.total_consultas == 1
