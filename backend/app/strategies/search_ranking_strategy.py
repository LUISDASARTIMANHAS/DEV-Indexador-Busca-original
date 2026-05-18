from __future__ import annotations

import math
from datetime import datetime

from app.utils.text_processing import preprocess_for_indexing


class SearchRankingStrategy:
    FIELD_WEIGHTS = {
        "titulo": 5.5,
        "tipo_documento": 2.4,
        "autor": 2.0,
        "arquivo": 1.8,
        "categoria": 1.4,
        "conteudo": 1.0,
    }

    def rank(
        self,
        rows: list,
        query_terms: list[str],
        *,
        raw_query: str | None = None,
    ) -> list[dict]:
        unique_query_terms = set(query_terms)
        documents: dict[int, dict] = {}

        for row in rows:
            field_type = getattr(row, "field_type", "conteudo") or "conteudo"
            document = documents.setdefault(
                row.document_id,
                {
                    "document_id": row.document_id,
                    "score": 0.0,
                    "matched_terms": set(),
                    "matched_query_terms": set(),
                    "title": row.title or "",
                    "document_date": row.document_date,
                    "field_matches": {},
                    "field_positions": {},
                },
            )
            matched_query_terms = self._matched_query_terms(row.term, unique_query_terms)
            if not matched_query_terms:
                continue

            document["score"] += self._row_score(row, matched_query_terms)
            document["matched_terms"].add(row.term)
            document["matched_query_terms"].update(matched_query_terms)
            document["field_matches"].setdefault(field_type, set()).update(matched_query_terms)
            for matched_query_term in matched_query_terms:
                document["field_positions"].setdefault(field_type, {}).setdefault(
                    matched_query_term,
                    [],
                ).append(int(row.posicao_inicial or 0))

        for document in documents.values():
            document["score"] *= self._coverage_weight(
                document["matched_query_terms"],
                unique_query_terms,
            )
            document["score"] *= self._field_match_weight(document["field_matches"])
            document["score"] *= self._title_weight(
                document["title"],
                document["matched_query_terms"],
                unique_query_terms,
                raw_query=raw_query,
            )
            document["score"] *= self._proximity_weight(
                document["field_positions"],
                unique_query_terms,
            )
            document["score"] *= self._recency_weight(document["document_date"])

        return sorted(documents.values(), key=lambda item: item["score"], reverse=True)

    def _matched_query_terms(self, indexed_term: str, query_terms: set[str]) -> set[str]:
        return {
            query_term
            for query_term in query_terms
            if indexed_term == query_term or indexed_term.startswith(query_term)
        }

    def _row_score(self, row, matched_query_terms: set[str]) -> float:
        tf = float(row.tf or 0)
        idf = float(row.idf or 1)
        position = int(row.posicao_inicial or 0)
        field_type = getattr(row, "field_type", "conteudo") or "conteudo"
        field_weight = self.FIELD_WEIGHTS.get(field_type, 1.0)
        position_weight = 1.0 / math.sqrt(position + 1)
        tf_weight = 1.0 + math.log(tf) if tf > 0 else 0.0
        prefix_ratio = max(
            min(len(query_term) / max(len(row.term), 1), 1.0)
            for query_term in matched_query_terms
        )
        exact_match_bonus = 1.2 if row.term in matched_query_terms else 1.0
        prefix_weight = 0.55 + (prefix_ratio * 0.45)
        return tf_weight * idf * position_weight * field_weight * prefix_weight * exact_match_bonus

    def _coverage_weight(self, matched_terms: set[str], query_terms: set[str]) -> float:
        if not query_terms:
            return 1.0
        coverage = len(matched_terms) / len(query_terms)
        return 1.0 + (coverage * 0.8)

    def _field_match_weight(self, field_matches: dict[str, set[str]]) -> float:
        weight = 1.0
        title_matches = len(field_matches.get("titulo", set()))
        if title_matches:
            weight += min(title_matches * 0.18, 0.54)
        metadata_matches = sum(
            len(field_matches.get(field, set()))
            for field in ("tipo_documento", "autor", "arquivo", "categoria")
        )
        if metadata_matches:
            weight += min(metadata_matches * 0.05, 0.2)
        return weight

    def _title_weight(
        self,
        title: str,
        matched_terms: set[str],
        query_terms: set[str],
        *,
        raw_query: str | None,
    ) -> float:
        title_tokens = set(preprocess_for_indexing(title)["tokens"])
        if not title_tokens:
            return 1.0
        title_matches = len(
            {
                title_token
                for title_token in title_tokens
                for query_term in matched_terms
                if title_token == query_term or title_token.startswith(query_term)
            }
        )
        weight = 1.0 + min(title_matches * 0.18, 0.72)

        normalized_title = preprocess_for_indexing(title)["processed_text"]
        normalized_query = preprocess_for_indexing(raw_query or "")["processed_text"]
        if normalized_query and normalized_title:
            if normalized_title == normalized_query:
                weight *= 1.8
            elif normalized_query in normalized_title:
                weight *= 1.35
            elif query_terms and query_terms.issubset(title_tokens):
                weight *= 1.2
        return weight

    def _proximity_weight(
        self,
        field_positions: dict[str, dict[str, list[int]]],
        query_terms: set[str],
    ) -> float:
        if not query_terms:
            return 1.0

        best_weight = 1.0
        for positions_by_term in field_positions.values():
            matched_terms = query_terms.intersection(positions_by_term.keys())
            if not matched_terms:
                continue
            coverage = len(matched_terms) / len(query_terms)
            span_positions = [min(positions_by_term[term]) for term in matched_terms]
            span = max(span_positions) - min(span_positions) + 1
            proximity_bonus = min((1.0 / math.sqrt(max(span, 1))) * 0.35, 0.35)
            best_weight = max(best_weight, 1.0 + (coverage * 0.25) + proximity_bonus)
        return best_weight

    def _recency_weight(self, document_date) -> float:
        if document_date is None:
            return 1.0
        if isinstance(document_date, str):
            try:
                document_date = datetime.fromisoformat(document_date)
            except ValueError:
                return 1.0
        age_days = max((datetime.utcnow() - document_date.replace(tzinfo=None)).days, 0)
        if age_days <= 365:
            return 1.08
        if age_days <= 1095:
            return 1.03
        return 1.0
