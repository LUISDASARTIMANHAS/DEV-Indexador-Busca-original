from __future__ import annotations

import math
from typing import Any

from app.strategies.ranking_strategy import RankingStrategy


class BM25RankingStrategy(RankingStrategy):
    def rank(
        self,
        query_terms: list[str],
        documents: list[dict[str, Any]],
        index_data: dict[str, Any] | None = None,
        options: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        index_data = index_data or {}
        options = options or {}
        total_documents = int(index_data.get("total_documents") or len(documents) or 1)
        k1 = float(options.get("k1", 1.5))
        b = float(options.get("b", 0.75))
        fallback_df = self._fallback_document_frequencies(documents)
        average_length = float(
            index_data.get("average_document_length")
            or self._average_document_length(documents)
            or 1.0
        )
        unique_query_terms = {term for term in query_terms if term}
        ranked: list[dict[str, Any]] = []

        for document in documents:
            document_length = max(self._document_length(document), 1)
            score = 0.0
            matched_terms: set[str] = set()

            for indexed_term, entry in self._document_terms(document).items():
                matches = self._matches_query(indexed_term, unique_query_terms)
                if not matches:
                    continue

                frequency = float(entry.get("tf") or 0)
                df = int(entry.get("df") or fallback_df.get(indexed_term) or 0)
                idf = math.log(((total_documents - df + 0.5) / (df + 0.5)) + 1)
                denominator = frequency + k1 * (
                    1 - b + b * (document_length / average_length)
                )
                if denominator:
                    score += idf * ((frequency * (k1 + 1)) / denominator) * max(len(matches), 1)
                    matched_terms.add(indexed_term)

            if score > 0:
                ranked.append(self._result(document, score=score, matched_terms=matched_terms))

        return sorted(ranked, key=lambda item: item["score"], reverse=True)

    def _average_document_length(self, documents: list[dict[str, Any]]) -> float:
        if not documents:
            return 0.0
        return sum(self._document_length(document) for document in documents) / len(documents)
