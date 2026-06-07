from __future__ import annotations

from typing import Any


class HybridPostgresSearchStrategy:
    def combine(
        self,
        *,
        postgres_items: list[dict[str, Any]],
        secondary_items: list[dict[str, Any]],
        postgres_weight: float = 0.7,
        secondary_weight: float = 0.3,
    ) -> list[dict[str, Any]]:
        total_weight = postgres_weight + secondary_weight
        if total_weight <= 0:
            postgres_weight = 0.7
            secondary_weight = 0.3
            total_weight = 1.0
        postgres_weight = postgres_weight / total_weight
        secondary_weight = secondary_weight / total_weight

        postgres_by_id = {int(item["document_id"]): item for item in postgres_items}
        secondary_by_id = {int(item["document_id"]): item for item in secondary_items}
        postgres_scores = self._normalize_scores(
            {document_id: float(item.get("postgres_score", item.get("score", 0.0)) or 0.0) for document_id, item in postgres_by_id.items()}
        )
        secondary_scores = self._normalize_scores(
            {document_id: float(item.get("final_score", item.get("score", 0.0)) or 0.0) for document_id, item in secondary_by_id.items()}
        )

        combined = []
        for document_id in set(postgres_by_id) | set(secondary_by_id):
            base = dict(postgres_by_id.get(document_id) or secondary_by_id[document_id])
            postgres_score = float((postgres_by_id.get(document_id) or {}).get("postgres_score", 0.0) or 0.0)
            secondary_score = float((secondary_by_id.get(document_id) or {}).get("final_score", (secondary_by_id.get(document_id) or {}).get("score", 0.0)) or 0.0)
            final_score = (
                postgres_weight * postgres_scores.get(document_id, 0.0)
                + secondary_weight * secondary_scores.get(document_id, 0.0)
            )
            matched_terms = set(base.get("matched_terms", set()))
            if document_id in secondary_by_id:
                matched_terms.update(secondary_by_id[document_id].get("matched_terms", set()))
            base.update(
                {
                    "score": final_score,
                    "postgres_score": postgres_score,
                    "secondary_score": secondary_score,
                    "final_score": final_score,
                    "textual_score": secondary_score,
                    "search_mode": "hybrid_postgres",
                    "matched_terms": matched_terms,
                }
            )
            combined.append(base)
        return sorted(combined, key=lambda item: item["final_score"], reverse=True)

    def _normalize_scores(self, scores: dict[int, float]) -> dict[int, float]:
        if not scores:
            return {}
        max_score = max(scores.values())
        if max_score <= 0:
            return {document_id: 0.0 for document_id in scores}
        return {document_id: score / max_score for document_id, score in scores.items()}
