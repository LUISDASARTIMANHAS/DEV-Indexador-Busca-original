from __future__ import annotations

from typing import Any

from app.strategies.ranking_strategy import RankingStrategy
from app.utils.vector_math import cosine_similarity


class SemanticRankingStrategy(RankingStrategy):
    def rank(
        self,
        query_terms: list[str],
        documents: list[dict[str, Any]],
        index_data: dict[str, Any] | None = None,
        options: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        del query_terms, options
        index_data = index_data or {}
        query_embedding = index_data.get("query_embedding") or []
        ranked: list[dict[str, Any]] = []

        for document in documents:
            embedding = document.get("embedding") or []
            score = cosine_similarity(query_embedding, embedding)
            if score <= 0:
                continue
            ranked.append(
                {
                    "document_id": self._document_id(document),
                    "score": float(score),
                    "textual_score": 0.0,
                    "semantic_score": float(score),
                    "final_score": float(score),
                    "matched_terms": set(),
                    "document": document,
                }
            )

        return sorted(ranked, key=lambda item: item["score"], reverse=True)
