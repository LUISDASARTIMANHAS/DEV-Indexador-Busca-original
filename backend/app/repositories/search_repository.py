from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.domain.document_category import DocumentCategory
from app.domain.document_field import DocumentField
from app.domain.field_type import FieldType
from app.domain.inverted_index import InvertedIndex
from app.domain.document import Document
from app.domain.document_history import DocumentHistory
from app.domain.document_metadata import DocumentMetadata
from app.domain.search_history import SearchHistory
from app.domain.term import Term


class SearchRepository:
    def search_terms(
        self,
        db: Session,
        *,
        terms: list[str],
    ):
        normalized_terms = sorted({term.strip() for term in terms if term and term.strip()})
        if not normalized_terms:
            return []

        term_conditions = [
            Term.texto_termo.like(f"{term}%")
            for term in normalized_terms
        ]
        query = (
            db.query(
                Document.cod_documento.label("document_id"),
                Document.titulo.label("title"),
                Document.tipo.label("document_type"),
                DocumentMetadata.tipo_documento.label("metadata_document_type"),
                Document.data_publicacao.label("document_date"),
                DocumentCategory.nome_categoria.label("category"),
                FieldType.tipo_campo.label("field_type"),
                Term.texto_termo.label("term"),
                Term.idf.label("idf"),
                InvertedIndex.tf.label("tf"),
                InvertedIndex.posicao_inicial.label("posicao_inicial"),
            )
            .select_from(InvertedIndex)
            .join(Term, Term.cod_termo == InvertedIndex.cod_termo)
            .join(
                DocumentField,
                DocumentField.cod_campo_documento == InvertedIndex.cod_campo_documento,
            )
            .join(
                FieldType,
                FieldType.cod_tipo_campo == DocumentField.cod_tipo_campo,
            )
            .join(
                DocumentHistory,
                DocumentHistory.cod_historico_documento == DocumentField.cod_historico_documento,
            )
            .join(Document, Document.cod_documento == DocumentHistory.cod_documento)
            .join(DocumentCategory, DocumentCategory.cod_categoria == Document.cod_categoria)
            .outerjoin(DocumentMetadata, DocumentMetadata.cod_documento == Document.cod_documento)
            .filter(or_(*term_conditions))
            .filter(Document.ativo.is_(True))
            .filter(DocumentHistory.versao_ativa.is_(True))
        )
        return query.all()

    def create_search_history(
        self,
        db: Session,
        *,
        user_id: int,
        query: str,
        filters: str | None,
        result_count: int,
        response_time_ms: int,
    ) -> SearchHistory:
        history = SearchHistory(
            cod_usuario=user_id,
            consulta_texto=query,
            filtros=filters,
            quantidade_resultados=result_count,
            tempo_resposta_ms=response_time_ms,
        )
        db.add(history)
        db.commit()
        db.refresh(history)
        return history

    def list_recent_searches(self, db: Session, *, user_id: int, limit: int = 10) -> list[SearchHistory]:
        return (
            db.query(SearchHistory)
            .filter(SearchHistory.cod_usuario == user_id)
            .order_by(
                SearchHistory.criado_em.desc(),
                SearchHistory.cod_historico_busca.desc(),
            )
            .limit(limit)
            .all()
        )

    def list_search_history(
        self,
        db: Session,
        *,
        user_id: int,
        query_text: str | None = None,
        performed_from: datetime | None = None,
        performed_to: datetime | None = None,
        limit: int = 20,
        page: int = 1,
    ) -> tuple[list[SearchHistory], int]:
        base_query = db.query(SearchHistory).filter(SearchHistory.cod_usuario == user_id)

        if query_text:
            base_query = base_query.filter(
                SearchHistory.consulta_texto.ilike(f"%{query_text.strip()}%")
            )
        if performed_from:
            base_query = base_query.filter(SearchHistory.criado_em >= performed_from)
        if performed_to:
            base_query = base_query.filter(SearchHistory.criado_em <= performed_to)

        total = base_query.count()
        rows = (
            base_query.order_by(
                SearchHistory.criado_em.desc(),
                SearchHistory.cod_historico_busca.desc(),
            )
            .offset(max(page - 1, 0) * limit)
            .limit(limit)
            .all()
        )
        return rows, total
