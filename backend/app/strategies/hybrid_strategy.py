from __future__ import annotations

from typing import Any

from app.strategies.ranking_strategy import RankingStrategy


class HybridRankingStrategy(RankingStrategy):
    def rank(
        self,
        query_terms: list[str],
        documents: list[dict[str, Any]],
        index_data: dict[str, Any] | None = None,
        options: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        del query_terms, documents
        index_data = index_data or {}
        options = options or {}
        text_weight = float(options.get("text_weight", 0.6))
        semantic_weight = float(options.get("semantic_weight", 0.4))
        total_weight = text_weight + semantic_weight
        if total_weight <= 0:
            text_weight = 0.6
            semantic_weight = 0.4
            total_weight = 1.0
        text_weight = text_weight / total_weight
        semantic_weight = semantic_weight / total_weight

        textual_scores = self._score_map(index_data.get("textual_scores") or {})
        semantic_scores = self._score_map(index_data.get("semantic_scores") or {})
        matched_terms = index_data.get("matched_terms") or {}
        candidate_ids = set(textual_scores) | set(semantic_scores)
        normalized_textual = self._normalize_scores(textual_scores)
        normalized_semantic = self._normalize_scores(semantic_scores)

        ranked = []
        for document_id in candidate_ids:
            textual_score = textual_scores.get(document_id, 0.0)
            semantic_score = semantic_scores.get(document_id, 0.0)
            final_score = (
                text_weight * normalized_textual.get(document_id, 0.0)
                + semantic_weight * normalized_semantic.get(document_id, 0.0)
            )
            ranked.append(
                {
                    "document_id": document_id,
                    "score": final_score,
                    "textual_score": textual_score,
                    "semantic_score": semantic_score,
                    "final_score": final_score,
                    "matched_terms": set(matched_terms.get(document_id, set())),
                }
            )

        return sorted(ranked, key=lambda item: item["final_score"], reverse=True)

    def _score_map(self, raw_scores: dict[Any, Any]) -> dict[Any, float]:
        scores: dict[Any, float] = {}
        for document_id, value in raw_scores.items():
            if isinstance(value, dict):
                value = value.get("score", value.get("final_score", 0.0))
            scores[document_id] = float(value or 0.0)
        return scores

    def _normalize_scores(self, scores: dict[Any, float]) -> dict[Any, float]:
        if not scores:
            return {}
        max_score = max(scores.values())
        if max_score <= 0:
            return {document_id: 0.0 for document_id in scores}
        return {document_id: score / max_score for document_id, score in scores.items()}
