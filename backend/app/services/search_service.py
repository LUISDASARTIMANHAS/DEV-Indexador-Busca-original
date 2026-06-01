import html
import math
import re
import time
from datetime import date, datetime, time as dt_time

from sqlalchemy.orm import Session

from app.core.logging import logger
from app.repositories.document_repository import DocumentRepository
from app.repositories.search_repository import SearchRepository
from app.domain.user import User
from app.strategies.search_ranking_strategy import SearchRankingStrategy
from app.utils.text_processing import normalize_text, preprocess_for_indexing


class SearchService:
    SNIPPET_MAX_LENGTH = 240
    SNIPPET_CONTEXT_BEFORE_MATCH = 72

    def __init__(self, repository: SearchRepository):
        self.repository = repository
        self.document_repository = DocumentRepository()
        self.ranking_strategy = SearchRankingStrategy()

    def search(
        self,
        db: Session,
        *,
        query: str,
        user_id: int,
        limit: int = 10,
        page: int = 1,
        category: str | None = None,
        document_type: str | None = None,
        author: str | None = None,
        date_from: date | str | None = None,
        date_to: date | str | None = None,
        sort_by: str | None = None,
    ) -> dict:
        started_at = time.perf_counter()
        logger.info(
            "Search started user_id=%s query=%s category=%s document_type=%s author=%s date_from=%s date_to=%s sort_by=%s limit=%s page=%s",
            user_id,
            query,
            category,
            document_type,
            author,
            date_from,
            date_to,
            sort_by,
            limit,
            page,
        )
        if not query or not query.strip():
            return self._empty_response(
                query=query,
                page=page,
                per_page=limit,
                response_time_ms=0,
            )

        terms = self._process_query(query)
        if not terms:
            response_time_ms = self._elapsed_response_time_ms(started_at)
            response = self._empty_response(
                query=query,
                page=page,
                per_page=limit,
                response_time_ms=response_time_ms,
            )
            response["searchId"] = self._register_search(
                db,
                user_id=user_id,
                query=query,
                filters=self._serialize_filters(
                    category,
                    document_type,
                    author,
                    date_from,
                    date_to,
                    sort_by,
                ),
                result_count=0,
                response_time_ms=response_time_ms,
            )
            return response

        normalized_date_from = self._coerce_date_boundary(date_from, end_of_day=False)
        normalized_date_to = self._coerce_date_boundary(date_to, end_of_day=True)
        rows = self.repository.search_terms(
            db,
            terms=terms,
        )

        ranked_items = self.ranking_strategy.rank(
            rows,
            terms,
            raw_query=query,
        )
        ranked_payloads = self._load_ranked_payloads(
            db,
            ranked_items,
            category=category,
            document_type=document_type,
            author=author,
            date_from=normalized_date_from,
            date_to=normalized_date_to,
        )
        ranked_payloads = self._sort_ranked_payloads(ranked_payloads, sort_by=sort_by)

        start = max((page - 1) * limit, 0)
        end = start + limit
        paginated = ranked_payloads[start:end]
        top_score = ranked_payloads[0]["score"] if ranked_payloads else 0
        items = []

        for item in paginated:
            payload = item["payload"]
            snippet_source = self._searchable_result_text(payload)
            items.append(
                {
                    "id": payload["id"],
                    "title": payload["title"],
                    "snippet": self._build_snippet(
                        snippet_source,
                        sorted(item["matched_terms"]),
                    ),
                    "category": payload["category"],
                    "type": payload["type"],
                    "documentType": payload["document_type"],
                    "author": payload["author_name"],
                    "fileName": payload["file_name"],
                    "mimeType": payload["mime_type"] or "",
                    "size": self._format_size(payload["size_bytes"]),
                    "date": self._effective_document_date(payload).isoformat(),
                    "relevance": self._normalize_relevance(item["score"], top_score),
                }
            )

        response_time_ms = self._elapsed_response_time_ms(started_at)
        response = {
            "query": query,
            "total": len(ranked_payloads),
            "page": page,
            "perPage": limit,
            "totalPages": max(math.ceil(len(ranked_payloads) / limit), 1),
            "responseTimeMs": response_time_ms,
            "items": items,
        }
        response["searchId"] = self._register_search(
            db,
            user_id=user_id,
            query=query,
            filters=self._serialize_filters(
                category,
                document_type,
                author,
                date_from,
                date_to,
                sort_by,
            ),
            result_count=len(ranked_payloads),
            response_time_ms=response_time_ms,
        )
        logger.info(
            "Search completed user_id=%s query=%s total=%s page=%s per_page=%s response_time_ms=%s",
            user_id,
            query,
            len(ranked_payloads),
            page,
            limit,
            response_time_ms,
        )
        return response

    def _process_query(self, query: str) -> list[str]:
        preprocessed = preprocess_for_indexing(query)
        if preprocessed["tokens"]:
            return preprocessed["tokens"]
        normalized_query = normalize_text(query)
        return [token for token in normalized_query.split(" ") if token]

    def list_recent_searches(self, db: Session, *, user_id: int, limit: int = 10) -> list[dict]:
        rows = self.repository.list_recent_searches(db, user_id=user_id, limit=limit)
        return [
            {
                "id": row.cod_historico_busca,
                "term": row.consulta_texto,
            }
            for row in rows
        ]

    def list_search_history(
        self,
        db: Session,
        *,
        current_user: User,
        limit: int = 20,
        page: int = 1,
        query: str | None = None,
        performed_from: date | str | None = None,
        performed_to: date | str | None = None,
    ) -> dict:
        normalized_from = self._coerce_date_boundary(performed_from, end_of_day=False)
        normalized_to = self._coerce_date_boundary(performed_to, end_of_day=True)
        rows, total = self.repository.list_search_history(
            db,
            user_id=current_user.cod_usuario,
            query_text=query,
            performed_from=normalized_from,
            performed_to=normalized_to,
            limit=limit,
            page=page,
        )

        items = [
            {
                "id": row.cod_historico_busca,
                "query": row.consulta_texto,
                "createdAt": row.criado_em.isoformat() if row.criado_em else "",
                "resultCount": int(row.quantidade_resultados or 0),
                "responseTimeMs": int(row.tempo_resposta_ms or 0),
                "user": current_user.email,
                "filters": self._deserialize_filters(row.filtros),
            }
            for row in rows
        ]
        return {
            "total": total,
            "page": page,
            "perPage": limit,
            "totalPages": max(math.ceil(total / limit), 1),
            "items": items,
        }

    def _build_snippet(self, content: str, matched_terms: list[str]) -> str:
        text = re.sub(r"\s+", " ", content or "").strip()
        if not text:
            return ""

        spans = self._highlight_spans(text, matched_terms)
        start = 0
        if spans:
            start = max(spans[0][0] - self.SNIPPET_CONTEXT_BEFORE_MATCH, 0)
            if start > 0:
                word_boundary = text.find(" ", start, spans[0][0])
                if word_boundary >= 0:
                    start = word_boundary + 1

        end = min(start + self.SNIPPET_MAX_LENGTH, len(text))
        if end < len(text):
            word_boundary = text.rfind(" ", start, end)
            if word_boundary > start:
                end = word_boundary

        excerpt_spans = [
            (span_start - start, span_end - start)
            for span_start, span_end in spans
            if span_start >= start and span_end <= end
        ]
        excerpt = text[start:end]
        highlighted = self._escape_and_mark(excerpt, excerpt_spans)
        prefix = "... " if start > 0 else ""
        suffix = " ..." if end < len(text) else ""
        return f"{prefix}{highlighted}{suffix}"

    def _searchable_result_text(self, payload: dict) -> str:
        values = [
            payload.get("content"),
            payload.get("title"),
            payload.get("author_name"),
            payload.get("category"),
            payload.get("document_type"),
            payload.get("file_name"),
        ]
        return "\n".join(str(value) for value in values if value)

    def _highlight_spans(self, text: str, matched_terms: list[str]) -> list[tuple[int, int]]:
        normalized_terms = {
            normalize_text(term)
            for term in matched_terms
            if normalize_text(term)
        }
        if not normalized_terms:
            return []

        spans: list[tuple[int, int]] = []
        for match in re.finditer(r"\w+", text, flags=re.UNICODE):
            token = normalize_text(match.group(0))
            if any(token == term or token.startswith(term) for term in normalized_terms):
                spans.append(match.span())
        return spans

    def _escape_and_mark(self, text: str, spans: list[tuple[int, int]]) -> str:
        fragments: list[str] = []
        position = 0
        for start, end in spans:
            fragments.append(html.escape(text[position:start]))
            fragments.append(f"<mark>{html.escape(text[start:end])}</mark>")
            position = end
        fragments.append(html.escape(text[position:]))
        return "".join(fragments)

    def _normalize_relevance(self, score: float, top_score: float) -> int:
        if top_score <= 0:
            return 0
        return min(max(int(round((score / top_score) * 100)), 1), 100)

    def _format_size(self, size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        return f"{size_bytes / (1024 * 1024):.1f} MB"

    def _load_ranked_payloads(
        self,
        db: Session,
        ranked_items: list[dict],
        *,
        category: str | None,
        document_type: str | None,
        author: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> list[dict]:
        ranked_payloads: list[dict] = []
        for item in ranked_items:
            payload = self.document_repository.get_document_payload(db, item["document_id"])
            if payload is None:
                continue
            if not self._matches_filters(
                payload,
                category=category,
                document_type=document_type,
                author=author,
                date_from=date_from,
                date_to=date_to,
            ):
                continue
            ranked_payloads.append(
                {
                    "document_id": item["document_id"],
                    "score": item["score"],
                    "matched_terms": item["matched_terms"],
                    "payload": payload,
                }
            )
        return ranked_payloads

    def _matches_filters(
        self,
        payload: dict,
        *,
        category: str | None,
        document_type: str | None,
        author: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> bool:
        if category and self._normalize_filter_value(payload.get("category")) != self._normalize_filter_value(category):
            return False

        if document_type and not self._matches_document_type_filter(payload, document_type):
            return False

        if author:
            author_value = self._normalize_filter_value(payload.get("author_name"))
            if self._normalize_filter_value(author) not in author_value:
                return False

        effective_date = self._effective_document_date(payload).replace(tzinfo=None)
        if date_from and effective_date < date_from.replace(tzinfo=None):
            return False
        if date_to and effective_date > date_to.replace(tzinfo=None):
            return False
        return True

    def _matches_document_type_filter(self, payload: dict, document_type: str) -> bool:
        normalized_filter = self._normalize_filter_value(document_type)
        document_type_value = self._normalize_filter_value(payload.get("document_type"))
        format_value = self._normalize_filter_value(payload.get("type"))
        file_name_value = self._normalize_filter_value(payload.get("file_name"))
        return any(
            normalized_filter
            and normalized_filter in value
            for value in (document_type_value, format_value, file_name_value)
        )

    def _sort_ranked_payloads(self, ranked_payloads: list[dict], *, sort_by: str | None) -> list[dict]:
        if sort_by == "data-desc":
            return sorted(
                ranked_payloads,
                key=lambda item: (
                    self._effective_document_date(item["payload"]),
                    item["score"],
                ),
                reverse=True,
            )
        if sort_by == "data-asc":
            return sorted(
                ranked_payloads,
                key=lambda item: (
                    self._effective_document_date(item["payload"]),
                    -item["score"],
                ),
            )
        if sort_by == "titulo":
            return sorted(
                ranked_payloads,
                key=lambda item: (
                    self._normalize_filter_value(item["payload"]["title"]),
                    -item["score"],
                ),
            )
        return ranked_payloads

    def _effective_document_date(self, payload: dict) -> datetime:
        return payload["document_date"] or payload["uploaded_at"]

    def _normalize_filter_value(self, value: str | None) -> str:
        return normalize_text(value or "")

    def _register_search(
        self,
        db: Session,
        *,
        user_id: int,
        query: str,
        filters: str | None,
        result_count: int,
        response_time_ms: int,
    ) -> int:
        history = self.repository.create_search_history(
            db,
            user_id=user_id,
            query=query,
            filters=filters,
            result_count=result_count,
            response_time_ms=response_time_ms,
        )
        return int(history.cod_historico_busca)

    def _elapsed_response_time_ms(self, started_at: float) -> int:
        return max(int((time.perf_counter() - started_at) * 1000), 0)

    def _serialize_filters(
        self,
        category: str | None,
        document_type: str | None,
        author: str | None,
        date_from: date | str | None,
        date_to: date | str | None,
        sort_by: str | None,
    ) -> str | None:
        filters = {
            "category": category,
            "documentType": document_type,
            "author": author,
            "dateFrom": self._stringify_date_filter(date_from),
            "dateTo": self._stringify_date_filter(date_to),
            "sortBy": sort_by,
        }
        filtered_items = [f"{key}={value}" for key, value in filters.items() if value]
        return ";".join(filtered_items) if filtered_items else None

    def _deserialize_filters(self, serialized_filters: str | None) -> dict:
        filters = {
            "category": None,
            "documentType": None,
            "author": None,
            "dateFrom": None,
            "dateTo": None,
            "sortBy": None,
        }
        if not serialized_filters:
            return filters

        for item in serialized_filters.split(";"):
            if "=" not in item:
                continue
            key, value = item.split("=", 1)
            if key in filters and value:
                filters[key] = value
        return filters

    def _coerce_date_boundary(
        self,
        value: date | str | None,
        *,
        end_of_day: bool,
    ) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            value = date.fromisoformat(value)
        boundary_time = dt_time.max if end_of_day else dt_time.min
        return datetime.combine(value, boundary_time)

    def _stringify_date_filter(self, value: date | str | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return value.isoformat()

    def _empty_response(
        self,
        *,
        query: str,
        page: int,
        per_page: int,
        response_time_ms: int,
    ) -> dict:
        return {
            "searchId": None,
            "query": query,
            "total": 0,
            "page": page,
            "perPage": per_page,
            "totalPages": 1,
            "responseTimeMs": response_time_ms,
            "items": [],
        }


search_service = SearchService(SearchRepository())
