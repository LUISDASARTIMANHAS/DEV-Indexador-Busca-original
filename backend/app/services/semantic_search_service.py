from __future__ import annotations

from sqlalchemy.orm import Session

from app.adapters.embedding_adapter import EmbeddingAdapter, MockEmbeddingAdapter
from app.repositories.document_repository import DocumentRepository
from app.repositories.embedding_repository import EmbeddingRepository
from app.strategies.semantic_strategy import SemanticRankingStrategy


class SemanticSearchService:
    def __init__(
        self,
        embedding_repository: EmbeddingRepository,
        document_repository: DocumentRepository,
        embedding_adapter: EmbeddingAdapter | None = None,
    ):
        self.embedding_repository = embedding_repository
        self.document_repository = document_repository
        self.embedding_adapter = embedding_adapter or MockEmbeddingAdapter()
        self.ranking_strategy = SemanticRankingStrategy()

    @property
    def model_name(self) -> str:
        return self.embedding_adapter.model_name

    def persist_document_embedding(
        self,
        db: Session,
        *,
        document_id: int,
        version_number: int | None,
        text: str,
    ) -> dict:
        embedding = self.embedding_adapter.encode_text(text)
        row = self.embedding_repository.upsert_document_embedding(
            db,
            document_id=document_id,
            version_number=version_number,
            model_name=self.model_name,
            embedding=embedding,
        )
        return {
            "documentId": row.cod_documento,
            "version": row.versao_documento,
            "model": row.modelo_embedding,
        }

    def rebuild_embeddings(self, db: Session) -> dict:
        payloads = self.document_repository.list_active_document_payloads(db)
        success_count = 0
        for payload in payloads:
            self.persist_document_embedding(
                db,
                document_id=payload["id"],
                version_number=int(payload["version"]) if payload.get("version") is not None else None,
                text=self._semantic_text(payload),
            )
            success_count += 1
        db.commit()
        return {
            "processedDocuments": len(payloads),
            "successCount": success_count,
            "failureCount": 0,
            "model": self.model_name,
            "message": f"Embeddings reconstruidos para {success_count} documento(s).",
        }

    def search(
        self,
        db: Session,
        *,
        query: str,
        limit: int | None = None,
    ) -> list[dict]:
        self.ensure_embeddings_for_active_documents(db)
        query_embedding = self.embedding_adapter.encode_text(query)
        rows = self.embedding_repository.list_active_embeddings(
            db,
            model_name=self.model_name,
        )
        documents = [
            {
                "document_id": row.cod_documento,
                "embedding": row.embedding,
            }
            for row in rows
        ]
        ranked = self.ranking_strategy.rank(
            [],
            documents,
            index_data={"query_embedding": query_embedding},
        )
        if limit is not None:
            return ranked[:limit]
        return ranked

    def ensure_embeddings_for_active_documents(self, db: Session) -> int:
        payloads = self.document_repository.list_active_document_payloads(db)
        existing_keys = self.embedding_repository.list_active_embedding_keys(
            db,
            model_name=self.model_name,
        )
        created_count = 0
        for payload in payloads:
            version_number = int(payload["version"]) if payload.get("version") is not None else None
            if (payload["id"], version_number) in existing_keys:
                continue
            self.persist_document_embedding(
                db,
                document_id=payload["id"],
                version_number=version_number,
                text=self._semantic_text(payload),
            )
            created_count += 1
        if created_count:
            db.commit()
        return created_count

    def _semantic_text(self, payload: dict) -> str:
        values = [
            payload.get("title"),
            payload.get("document_type"),
            payload.get("category"),
            payload.get("author_name"),
            payload.get("file_name"),
            payload.get("content"),
        ]
        return "\n".join(str(value) for value in values if value)


semantic_search_service = SemanticSearchService(
    EmbeddingRepository(),
    DocumentRepository(),
)
