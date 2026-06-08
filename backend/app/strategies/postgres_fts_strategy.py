from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.repositories.postgres_search_repository import PostgresSearchRepository
from app.schemas.query_schema import QueryAnalysisResult


class PostgresFTSSearchStrategy:
    def __init__(self, repository: PostgresSearchRepository):
        self.repository = repository

    def search(
        self,
        db: Session,
        *,
        query: str,
        analysis: QueryAnalysisResult,
        filters: dict[str, Any],
        limit: int,
    ) -> list[dict[str, Any]]:
        terms = analysis.terms + analysis.phrases
        fts_query = " ".join(terms).strip() or query
        rows = self.repository.search_full_text(
            db,
            query=fts_query,
            limit=limit,
            filters=filters,
        )
        return [
            {
                "document_id": row["document_id"],
                "score": row["score"],
                "textual_score": row["score"],
                "semantic_score": 0.0,
                "postgres_score": row["score"],
                "secondary_score": 0.0,
                "final_score": row["score"],
                "matched_terms": set(row.get("matched_terms") or analysis.terms),
                "search_mode": "postgres_fts",
                "snippet": row.get("snippet", ""),
                "payload": self._payload_from_row(row),
            }
            for row in rows
        ]

    def _payload_from_row(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["document_id"],
            "title": row["title"],
            "type": row["type"],
            "document_type": row["document_type"],
            "category": row["category"],
            "document_date": row["document_date"],
            "uploaded_at": row["uploaded_at"],
            "version": row["version"],
            "file_name": row["file_name"],
            "mime_type": row["mime_type"],
            "size_bytes": row["size_bytes"],
            "content": row.get("content", ""),
            "ocr_executado": bool(row.get("ocr_executado")),
            "ocr_status": row.get("ocr_status"),
            "author_name": row["author_name"],
        }
