from __future__ import annotations

from sqlalchemy.orm import Session

from app.domain.document import Document
from app.domain.document_embedding import DocumentEmbedding
from app.domain.document_history import DocumentHistory


class EmbeddingRepository:
    def upsert_document_embedding(
        self,
        db: Session,
        *,
        document_id: int,
        version_number: int | None,
        model_name: str,
        embedding: list[float],
    ) -> DocumentEmbedding:
        row = (
            db.query(DocumentEmbedding)
            .filter(DocumentEmbedding.cod_documento == document_id)
            .filter(DocumentEmbedding.versao_documento == version_number)
            .filter(DocumentEmbedding.modelo_embedding == model_name)
            .first()
        )
        if row is None:
            row = DocumentEmbedding(
                cod_documento=document_id,
                versao_documento=version_number,
                modelo_embedding=model_name,
                embedding=embedding,
            )
            db.add(row)
        else:
            row.embedding = embedding
        db.flush()
        return row

    def list_active_embeddings(
        self,
        db: Session,
        *,
        model_name: str,
    ) -> list[DocumentEmbedding]:
        return (
            db.query(DocumentEmbedding)
            .join(Document, Document.cod_documento == DocumentEmbedding.cod_documento)
            .join(
                DocumentHistory,
                (DocumentHistory.cod_documento == DocumentEmbedding.cod_documento)
                & (DocumentHistory.numero_versao == DocumentEmbedding.versao_documento),
            )
            .filter(Document.ativo.is_(True))
            .filter(DocumentHistory.versao_ativa.is_(True))
            .filter(DocumentEmbedding.modelo_embedding == model_name)
            .all()
        )

    def list_active_embedding_keys(
        self,
        db: Session,
        *,
        model_name: str,
    ) -> set[tuple[int, int | None]]:
        rows = (
            db.query(
                DocumentEmbedding.cod_documento,
                DocumentEmbedding.versao_documento,
            )
            .join(Document, Document.cod_documento == DocumentEmbedding.cod_documento)
            .join(
                DocumentHistory,
                (DocumentHistory.cod_documento == DocumentEmbedding.cod_documento)
                & (DocumentHistory.numero_versao == DocumentEmbedding.versao_documento),
            )
            .filter(Document.ativo.is_(True))
            .filter(DocumentHistory.versao_ativa.is_(True))
            .filter(DocumentEmbedding.modelo_embedding == model_name)
            .all()
        )
        return {
            (
                int(row.cod_documento),
                int(row.versao_documento) if row.versao_documento is not None else None,
            )
            for row in rows
        }

    def delete_document_embeddings(self, db: Session, *, document_id: int) -> int:
        return (
            db.query(DocumentEmbedding)
            .filter(DocumentEmbedding.cod_documento == document_id)
            .delete(synchronize_session=False)
        )
