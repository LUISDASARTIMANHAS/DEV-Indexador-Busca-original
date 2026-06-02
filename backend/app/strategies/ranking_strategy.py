from __future__ import annotations

from abc import ABC, abstractmethod
from collections import Counter
from typing import Any

from app.utils.text_processing import preprocess_for_indexing


class RankingStrategy(ABC):
    @abstractmethod
    def rank(
        self,
        query_terms: list[str],
        documents: list[dict[str, Any]],
        index_data: dict[str, Any] | None = None,
        options: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        pass

    def _document_id(self, document: dict[str, Any]) -> Any:
        return document.get("document_id", document.get("id"))

    def _document_terms(self, document: dict[str, Any]) -> dict[str, dict[str, Any]]:
        if document.get("terms"):
            return document["terms"]

        term_frequencies = document.get("term_frequencies")
        if term_frequencies:
            return {
                term: {"tf": frequency, "df": None, "positions": []}
                for term, frequency in term_frequencies.items()
            }

        text = " ".join(
            str(value)
            for value in (
                document.get("content"),
                document.get("text"),
                document.get("title"),
            )
            if value
        )
        tokens = preprocess_for_indexing(text)["tokens"]
        frequencies = Counter(tokens)
        return {
            term: {"tf": frequency, "df": None, "positions": []}
            for term, frequency in frequencies.items()
        }

    def _document_length(self, document: dict[str, Any]) -> int:
        if document.get("document_length") is not None:
            return int(document["document_length"])
        return sum(int(entry.get("tf") or 0) for entry in self._document_terms(document).values())

    def _matches_query(self, indexed_term: str, query_terms: set[str]) -> set[str]:
        return {
            query_term
            for query_term in query_terms
            if indexed_term == query_term or indexed_term.startswith(query_term)
        }

    def _fallback_document_frequencies(
        self,
        documents: list[dict[str, Any]],
    ) -> dict[str, int]:
        frequencies: dict[str, int] = {}
        for document in documents:
            for term in self._document_terms(document):
                frequencies[term] = frequencies.get(term, 0) + 1
        return frequencies

    def _result(
        self,
        document: dict[str, Any],
        *,
        score: float,
        matched_terms: set[str],
    ) -> dict[str, Any]:
        return {
            "document_id": self._document_id(document),
            "score": float(score),
            "textual_score": float(score),
            "semantic_score": 0.0,
            "final_score": float(score),
            "matched_terms": set(matched_terms),
            "document": document,
        }
