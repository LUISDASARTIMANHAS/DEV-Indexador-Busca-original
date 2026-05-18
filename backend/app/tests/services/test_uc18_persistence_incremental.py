import math
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.domain.document import Document
from app.domain.document_category import DocumentCategory
from app.domain.document_history import DocumentHistory
from app.domain.term import Term
from app.domain.user import User
from app.domain.user_role import UserRole
from app.services.inverted_index_service import inverted_index_service
from app.services.index_service import index_service
from app.utils.text_processing import preprocess_for_indexing


def make_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine, session_local()


def create_document(db, *, user_id: int, category_id: int, title: str, text: str) -> DocumentHistory:
    document = Document(
        cod_categoria=category_id,
        titulo=title,
        tipo="TXT",
        ativo=True,
        cod_usuario_criador=user_id,
    )
    db.add(document)
    db.flush()

    history = DocumentHistory(
        cod_documento=document.cod_documento,
        cod_usuario=user_id,
        numero_versao=1,
        caminho_arquivo=f"/tmp/{title}.txt",
        texto_extraido=text,
        texto_processado=text,
        versao_ativa=True,
    )
    db.add(history)
    db.flush()
    return history


def index_text(db, history: DocumentHistory, text: str):
    payload = preprocess_for_indexing(text)
    return inverted_index_service.persist_document_terms(
        db,
        history=history,
        processed_text=payload["processed_text"],
        positions_by_term=payload["positions_by_term"],
    )


def test_incremental_update_and_global_refresh():
    engine, db = make_session()

    user = User(
        nome="Administrador",
        login="admin",
        email="admin@ifes.edu.br",
        senha_hash="hash",
        perfil=UserRole.ADMIN.value,
        ativo=True,
    )
    category = DocumentCategory(nome_categoria="administrativo")
    db.add_all([user, category])
    db.flush()

    # 1. Add first document
    history_one = create_document(db, user_id=user.cod_usuario, category_id=category.cod_categoria, title="Doc 1", text="termo1 termo2")
    index_text(db, history_one, "termo1 termo2")
    db.commit()

    term1 = db.query(Term).filter(Term.texto_termo == "termo1").one()
    # N=1, df=1 -> idf = log((1+1)/(1+1) + 1) = log(2) ~= 0.693 -> 693
    expected_idf_n1 = int(round(math.log(2) * 1000))
    assert term1.df == 1
    assert term1.idf == expected_idf_n1

    # 2. Add second document (Incremental update)
    history_two = create_document(db, user_id=user.cod_usuario, category_id=category.cod_categoria, title="Doc 2", text="termo1 termo3")
    index_text(db, history_two, "termo1 termo3")
    db.commit()

    db.refresh(term1)
    # term1 was affected, so it SHOULD be updated. 
    # N=2, df=2 -> idf = log((2+1)/(2+1) + 1) = log(2) ~= 0.693 -> 693
    assert term1.df == 2
    assert term1.idf == expected_idf_n1

    term2 = db.query(Term).filter(Term.texto_termo == "termo2").one()
    # term2 was NOT affected by Doc 2, so it stays with N=1 values (stale)
    assert term2.df == 1
    assert term2.idf == expected_idf_n1 # Still 693

    # Now refresh ALL to fix consistency
    inverted_index_service.refresh_all_term_statistics(db)
    db.refresh(term2)
    # N=2, df=1 -> idf = log((2+1)/(1+1) + 1) = log(2.5) ~= 0.916 -> 916
    expected_idf_term2_n2 = int(round(math.log(2.5) * 1000))
    assert term2.idf == expected_idf_term2_n2

    # 3. Test global refresh again with another document
    history_three = create_document(db, user_id=user.cod_usuario, category_id=category.cod_categoria, title="Doc 3", text="vazio")
    db.commit()
    
    # Refresh all via index_service
    index_service.optimize_index(db, triggered_by=user)
    db.refresh(term2)
    # N=3, df=1 -> idf = log((3+1)/(1+1) + 1) = log(3) ~= 1.098 -> 1098
    expected_idf_term2_n3 = int(round(math.log(3) * 1000))
    assert term2.idf == expected_idf_term2_n3

    db.close()
    Base.metadata.drop_all(bind=engine)
