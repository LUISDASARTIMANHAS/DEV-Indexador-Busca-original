from __future__ import annotations

import math
from typing import Any

from app.strategies.ranking_strategy import RankingStrategy


class TFIDFRankingStrategy(RankingStrategy):
    def rank(
        self,
        query_terms: list[str],
        documents: list[dict[str, Any]],
        index_data: dict[str, Any] | None = None,
        options: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        del options
        index_data = index_data or {}
        total_documents = int(index_data.get("total_documents") or len(documents) or 1)
        fallback_df = self._fallback_document_frequencies(documents)
        unique_query_terms = {term for term in query_terms if term}
        ranked: list[dict[str, Any]] = []

        for document in documents:
            score = 0.0
            matched_terms: set[str] = set()
            for indexed_term, entry in self._document_terms(document).items():
                matches = self._matches_query(indexed_term, unique_query_terms)
                if not matches:
                    continue

                tf = float(entry.get("tf") or 0)
                df = int(entry.get("df") or fallback_df.get(indexed_term) or 0)
                idf = math.log((total_documents + 1) / (df + 1)) + 1
                score += tf * idf * max(len(matches), 1)
                matched_terms.add(indexed_term)

            if score > 0:
                ranked.append(self._result(document, score=score, matched_terms=matched_terms))

        return sorted(ranked, key=lambda item: item["score"], reverse=True)
