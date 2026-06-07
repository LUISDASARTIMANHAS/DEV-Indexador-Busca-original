import html
import math
import re
import time
from datetime import date, datetime, time as dt_time

from sqlalchemy.orm import Session

from app.core.logging import logger
from app.repositories.document_repository import DocumentRepository
from app.repositories.postgres_search_repository import PostgresSearchRepository
from app.repositories.search_repository import SearchRepository
from app.domain.user import User
from app.schemas.query_schema import QueryAnalysisResult
from app.services.query_analyzer_service import query_analyzer
from app.services.semantic_search_service import semantic_search_service
from app.strategies.bm25_strategy import BM25RankingStrategy
from app.strategies.frequency_strategy import FrequencyRankingStrategy
from app.strategies.hybrid_postgres_strategy import HybridPostgresSearchStrategy
from app.strategies.hybrid_strategy import HybridRankingStrategy
from app.strategies.postgres_fts_strategy import PostgresFTSSearchStrategy
from app.strategies.tfidf_strategy import TFIDFRankingStrategy
from app.utils.text_processing import normalize_text


class SearchService:
    SNIPPET_MAX_LENGTH = 240
    SNIPPET_CONTEXT_BEFORE_MATCH = 72

    def __init__(self, repository: SearchRepository):
        self.repository = repository
        self.document_repository = DocumentRepository()
        self.semantic_search_service = semantic_search_service
        self.postgres_fts_strategy = PostgresFTSSearchStrategy(PostgresSearchRepository())
        self.textual_strategies = {
            "frequency": FrequencyRankingStrategy(),
            "tfidf": TFIDFRankingStrategy(),
            "bm25": BM25RankingStrategy(),
        }
        self.hybrid_strategy = HybridRankingStrategy()
        self.hybrid_postgres_strategy = HybridPostgresSearchStrategy()

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
        mode: str = "postgres_fts",
        text_weight: float = 0.6,
        semantic_weight: float = 0.4,
        debug_analysis: bool = False,
    ) -> dict:
        started_at = time.perf_counter()
        search_mode = self._normalize_mode(mode)
        analysis = query_analyzer.analyze(query)
        logger.info(
            "Search started user_id=%s query=%s mode=%s category=%s document_type=%s author=%s date_from=%s date_to=%s sort_by=%s limit=%s page=%s",
            user_id,
            query,
            search_mode,
            category,
            document_type,
            author,
            date_from,
            date_to,
            sort_by,
            limit,
            page,
        )
        if not analysis.is_valid:
            return self._empty_response(
                query=query,
                page=page,
                per_page=limit,
                response_time_ms=0,
                mode=search_mode,
                analysis=analysis if debug_analysis else None,
            )

        terms = self._terms_for_retrieval(analysis)
        if not terms and search_mode not in {"semantic", "hybrid", "postgres_fts", "hybrid_postgres"}:
            response_time_ms = self._elapsed_response_time_ms(started_at)
            response = self._empty_response(
                query=query,
                page=page,
                per_page=limit,
                response_time_ms=response_time_ms,
                mode=search_mode,
                analysis=analysis if debug_analysis else None,
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
                    search_mode,
                    text_weight,
                    semantic_weight,
                ),
                result_count=0,
                response_time_ms=response_time_ms,
            )
            return response

        category = category or analysis.filters.category
        document_type = document_type or analysis.filters.type
        author = author or analysis.filters.author
        date_from = date_from or analysis.filters.date_from or (
            f"{analysis.filters.year}-01-01" if analysis.filters.year else None
        )
        date_to = date_to or analysis.filters.date_to or (
            f"{analysis.filters.year}-12-31" if analysis.filters.year else None
        )
        normalized_date_from = self._coerce_date_boundary(date_from, end_of_day=False)
        normalized_date_to = self._coerce_date_boundary(date_to, end_of_day=True)
        ranked_payloads = self._ranked_payloads_by_mode(
            db,
            query=query,
            terms=terms,
            analysis=analysis,
            mode=search_mode,
            text_weight=text_weight,
            semantic_weight=semantic_weight,
            limit=max(page * limit, limit),
            category=category,
            document_type=document_type,
            author=author,
            date_from=normalized_date_from,
            date_to=normalized_date_to,
        )
        ranked_payloads = self._remove_excluded_or_phrase_mismatches(
            ranked_payloads,
            analysis=analysis,
        )
        ranked_payloads = self._sort_ranked_payloads(ranked_payloads, sort_by=sort_by)

        start = max((page - 1) * limit, 0)
        end = start + limit
        paginated = ranked_payloads[start:end]
        top_score = ranked_payloads[0]["final_score"] if ranked_payloads else 0
        items = []

        for item in paginated:
            payload = item["payload"]
            snippet_source = self._searchable_result_text(payload)
            textual_score = float(item.get("textual_score", 0.0) or 0.0)
            semantic_score = float(item.get("semantic_score", 0.0) or 0.0)
            final_score = float(item.get("final_score", item.get("score", 0.0)) or 0.0)
            matched_terms = sorted(item["matched_terms"])
            items.append(
                {
                    "id": payload["id"],
                    "documentId": payload["id"],
                    "document_id": payload["id"],
                    "title": payload["title"],
                    "snippet": self._build_snippet(
                        snippet_source,
                        matched_terms,
                    ) if not item.get("snippet") else item["snippet"],
                    "category": payload["category"],
                    "type": payload["type"],
                    "documentType": payload["document_type"],
                    "author": payload["author_name"],
                    "fileName": payload["file_name"],
                    "mimeType": payload["mime_type"] or "",
                    "size": self._format_size(payload["size_bytes"]),
                    "date": self._effective_document_date(payload).isoformat(),
                    "relevance": self._normalize_relevance(final_score, top_score),
                    "textualScore": textual_score,
                    "semanticScore": semantic_score,
                    "finalScore": final_score,
                    "postgresScore": item.get("postgres_score"),
                    "secondaryScore": item.get("secondary_score"),
                    "score": final_score,
                    "searchMode": search_mode,
                    "matchedTerms": matched_terms,
                    "scoreExplanation": self._score_explanation(search_mode),
                    "textual_score": textual_score,
                    "semantic_score": semantic_score,
                    "final_score": final_score,
                    "postgres_score": item.get("postgres_score"),
                    "secondary_score": item.get("secondary_score"),
                    "search_mode": search_mode,
                    "matched_terms": matched_terms,
                    "metadata": {
                        "type": payload["type"],
                        "category": payload["category"],
                        "author": payload["author_name"],
                        "date": self._effective_document_date(payload).isoformat(),
                    },
                }
            )

        response_time_ms = self._elapsed_response_time_ms(started_at)
        response = {
            "query": query,
            "mode": search_mode,
            "searchMode": search_mode,
            "total": len(ranked_payloads),
            "page": page,
            "perPage": limit,
            "totalPages": max(math.ceil(len(ranked_payloads) / limit), 1),
            "responseTimeMs": response_time_ms,
            "items": items,
            "results": items,
        }
        if debug_analysis:
            response["analysis"] = self._analysis_summary(analysis)
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
                search_mode,
                text_weight,
                semantic_weight,
            ),
            result_count=len(ranked_payloads),
            response_time_ms=response_time_ms,
        )
        logger.info(
            "Search completed user_id=%s query=%s mode=%s total=%s page=%s per_page=%s response_time_ms=%s",
            user_id,
            query,
            search_mode,
            len(ranked_payloads),
            page,
            limit,
            response_time_ms,
        )
        return response

    def analyze_query(self, query: str) -> QueryAnalysisResult:
        return query_analyzer.analyze(query)

    def compare_strategies(
        self,
        db: Session,
        *,
        query: str,
        user_id: int,
        modes: list[str] | None = None,
        limit: int = 5,
        category: str | None = None,
        document_type: str | None = None,
        author: str | None = None,
        date_from: date | str | None = None,
        date_to: date | str | None = None,
        year: int | None = None,
    ) -> dict:
        compared_modes = modes or ["frequency", "bm25", "postgres_fts", "hybrid_postgres"]
        supported_modes = set(self.textual_strategies) | {"semantic", "hybrid", "postgres_fts", "hybrid_postgres"}
        results_by_mode: dict[str, list | dict] = {}
        best_mode = None
        best_score = -1.0

        if year and not date_from and not date_to:
            date_from = f"{year}-01-01"
            date_to = f"{year}-12-31"

        for mode in compared_modes:
            normalized_mode = normalize_text(mode)
            if normalized_mode not in supported_modes:
                results_by_mode[mode] = {
                    "mode": mode,
                    "available": False,
                    "reason": "Estratégia não implementada neste ambiente.",
                }
                continue
            try:
                response = self.search(
                    db,
                    query=query,
                    user_id=user_id,
                    category=category,
                    document_type=document_type,
                    author=author,
                    date_from=date_from,
                    date_to=date_to,
                    mode=normalized_mode,
                    limit=limit,
                    page=1,
                    debug_analysis=False,
                )
                items = response.get("items", [])
                results_by_mode[normalized_mode] = items
                top_score = float(items[0].get("finalScore", items[0].get("score", 0.0)) or 0.0) if items else 0.0
                if top_score > best_score:
                    best_score = top_score
                    best_mode = normalized_mode
            except Exception as exc:
                logger.exception("Search compare failed mode=%s query=%s", normalized_mode, query)
                results_by_mode[normalized_mode] = {
                    "mode": normalized_mode,
                    "available": False,
                    "reason": str(exc),
                }

        return {
            "query": query,
            "analysis": self._analysis_summary(query_analyzer.analyze(query)),
            "compared_modes": compared_modes,
            "results_by_mode": results_by_mode,
            "summary": {
                "best_mode_by_top_score": best_mode,
                "notes": [
                    "frequency valoriza repetição simples de termos",
                    "bm25 considera frequência, raridade e tamanho do documento",
                    "postgres_fts usa índice GIN persistente e ranking nativo",
                    "hybrid_postgres combina sinais de relevância",
                ],
            },
        }

    def _terms_for_retrieval(self, analysis: QueryAnalysisResult) -> list[str]:
        phrase_terms = [
            token
            for phrase in analysis.phrases
            for token in phrase.split(" ")
            if token
        ]
        terms = sorted(set(analysis.terms + phrase_terms))
        if terms:
            return terms
        return sorted(
            {
                token
                for token in analysis.tokens
                if token
                and token != analysis.filters.type
                and not token.isdigit()
            }
        )

    def _rank_by_mode(
        self,
        db: Session,
        *,
        query: str,
        terms: list[str],
        mode: str,
        text_weight: float,
        semantic_weight: float,
    ) -> list[dict]:
        if mode == "semantic":
            return self.semantic_search_service.search(db, query=query)

        if mode == "hybrid":
            textual_items = self._rank_textual(db, terms=terms, mode="bm25") if terms else []
            semantic_items = self.semantic_search_service.search(db, query=query)
            return self.hybrid_strategy.rank(
                terms,
                [],
                index_data={
                    "textual_scores": self._score_map(textual_items, "textual_score"),
                    "semantic_scores": self._score_map(semantic_items, "semantic_score"),
                    "matched_terms": self._matched_terms_map(textual_items),
                },
                options={
                    "text_weight": text_weight,
                    "semantic_weight": semantic_weight,
                },
            )

        return self._rank_textual(db, terms=terms, mode=mode)

    def _ranked_payloads_by_mode(
        self,
        db: Session,
        *,
        query: str,
        terms: list[str],
        analysis: QueryAnalysisResult,
        mode: str,
        text_weight: float,
        semantic_weight: float,
        limit: int,
        category: str | None,
        document_type: str | None,
        author: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> list[dict]:
        if mode == "postgres_fts":
            filters = self._fts_filters(category, document_type, author, date_from, date_to, analysis)
            ranked_items = self.postgres_fts_strategy.search(
                db,
                query=query,
                analysis=analysis,
                filters=filters,
                limit=max(limit, 1),
            )
            return self._ranked_items_to_payloads(
                db,
                ranked_items,
                category=category,
                document_type=document_type,
                author=author,
                date_from=date_from,
                date_to=date_to,
            )

        if mode == "hybrid_postgres":
            filters = self._fts_filters(category, document_type, author, date_from, date_to, analysis)
            postgres_items = self.postgres_fts_strategy.search(
                db,
                query=query,
                analysis=analysis,
                filters=filters,
                limit=max(limit, 25),
            )
            secondary_items = self._rank_textual(db, terms=terms, mode="bm25") if terms else []
            ranked_items = self.hybrid_postgres_strategy.combine(
                postgres_items=postgres_items,
                secondary_items=secondary_items,
                postgres_weight=text_weight if text_weight is not None else 0.7,
                secondary_weight=semantic_weight if semantic_weight is not None else 0.3,
            )
            return self._ranked_items_to_payloads(
                db,
                ranked_items,
                category=category,
                document_type=document_type,
                author=author,
                date_from=date_from,
                date_to=date_to,
            )

        ranked_items = self._rank_by_mode(
            db,
            query=query,
            terms=terms,
            mode=mode,
            text_weight=text_weight,
            semantic_weight=semantic_weight,
        )
        return self._load_ranked_payloads(
            db,
            ranked_items,
            category=category,
            document_type=document_type,
            author=author,
            date_from=date_from,
            date_to=date_to,
        )

    def _ranked_items_to_payloads(
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
            payload = item.get("payload") or self.document_repository.get_document_payload(db, item["document_id"])
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
                    "score": item.get("score", item.get("final_score", 0.0)),
                    "textual_score": item.get("textual_score", 0.0),
                    "semantic_score": item.get("semantic_score", 0.0),
                    "postgres_score": item.get("postgres_score"),
                    "secondary_score": item.get("secondary_score"),
                    "final_score": item.get("final_score", item.get("score", 0.0)),
                    "matched_terms": set(item.get("matched_terms", set())),
                    "snippet": item.get("snippet"),
                    "payload": payload,
                }
            )
        return ranked_payloads

    def _fts_filters(
        self,
        category: str | None,
        document_type: str | None,
        author: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
        analysis: QueryAnalysisResult,
    ) -> dict:
        return {
            "category": category,
            "document_type": document_type,
            "author": author,
            "date_from": date_from,
            "date_to": date_to,
            "year": analysis.filters.year,
        }

    def _rank_textual(self, db: Session, *, terms: list[str], mode: str) -> list[dict]:
        if not terms:
            return []
        rows = self.repository.search_terms(db, terms=terms)
        documents = self._build_strategy_documents(rows)
        strategy = self.textual_strategies.get(mode) or self.textual_strategies["bm25"]
        return strategy.rank(
            terms,
            documents,
            index_data={
                "total_documents": self.repository.count_active_documents(db),
                "average_document_length": self._average_document_length(documents),
            },
        )

    def _build_strategy_documents(self, rows: list) -> list[dict]:
        documents: dict[int, dict] = {}
        seen_fields: set[tuple[int, int | str]] = set()

        for row in rows:
            document_id = int(row.document_id)
            document = documents.setdefault(
                document_id,
                {
                    "document_id": document_id,
                    "title": row.title or "",
                    "document_date": row.document_date,
                    "terms": {},
                    "document_length": 0,
                },
            )
            field_id = getattr(row, "field_id", None) or f"{getattr(row, 'field_type', 'conteudo')}-{row.term}"
            field_key = (document_id, field_id)
            if field_key not in seen_fields:
                field_content = getattr(row, "field_content", "") or ""
                document["document_length"] += len(field_content.split())
                seen_fields.add(field_key)

            term_entry = document["terms"].setdefault(
                row.term,
                {
                    "tf": 0,
                    "df": int(getattr(row, "df", 0) or 0),
                    "positions": [],
                    "field_types": set(),
                },
            )
            term_entry["tf"] += int(row.tf or 0)
            term_entry["df"] = max(term_entry["df"], int(getattr(row, "df", 0) or 0))
            term_entry["positions"].append(int(row.posicao_inicial or 0))
            term_entry["field_types"].add(getattr(row, "field_type", "conteudo") or "conteudo")

        for document in documents.values():
            if document["document_length"] <= 0:
                document["document_length"] = sum(
                    int(entry.get("tf") or 0)
                    for entry in document["terms"].values()
                )

        return list(documents.values())

    def _average_document_length(self, documents: list[dict]) -> float:
        if not documents:
            return 0.0
        return sum(int(document.get("document_length") or 0) for document in documents) / len(documents)

    def _score_map(self, ranked_items: list[dict], score_key: str) -> dict[int, float]:
        return {
            int(item["document_id"]): float(item.get(score_key, item.get("score", 0.0)) or 0.0)
            for item in ranked_items
        }

    def _matched_terms_map(self, ranked_items: list[dict]) -> dict[int, set[str]]:
        return {
            int(item["document_id"]): set(item.get("matched_terms", set()))
            for item in ranked_items
        }

    def _normalize_mode(self, mode: str | None) -> str:
        normalized_mode = normalize_text(mode or "postgres_fts")
        if normalized_mode in self.textual_strategies or normalized_mode in {"semantic", "hybrid", "postgres_fts", "hybrid_postgres"}:
            return normalized_mode
        return "postgres_fts"

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
                    "score": item.get("score", item.get("final_score", 0.0)),
                    "textual_score": item.get("textual_score", 0.0),
                    "semantic_score": item.get("semantic_score", 0.0),
                    "final_score": item.get("final_score", item.get("score", 0.0)),
                    "matched_terms": set(item.get("matched_terms", set())),
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

    def _remove_excluded_or_phrase_mismatches(
        self,
        ranked_payloads: list[dict],
        *,
        analysis: QueryAnalysisResult,
    ) -> list[dict]:
        if not analysis.excluded_terms and not analysis.phrases:
            return ranked_payloads

        filtered_payloads = []
        for item in ranked_payloads:
            searchable_text = normalize_text(self._searchable_result_text(item["payload"]))
            if any(term in searchable_text.split(" ") for term in analysis.excluded_terms):
                continue
            if analysis.phrases and not all(phrase in searchable_text for phrase in analysis.phrases):
                continue
            filtered_payloads.append(item)
        return filtered_payloads

    def _analysis_summary(self, analysis: QueryAnalysisResult) -> dict:
        return {
            "terms": analysis.terms,
            "filters": analysis.filters.model_dump(),
            "phrases": analysis.phrases,
            "excluded_terms": analysis.excluded_terms,
            "intent": analysis.intent,
            "warnings": analysis.warnings,
        }

    def _score_explanation(self, mode: str) -> str:
        explanations = {
            "postgres_fts": "Relevância calculada pelo PostgreSQL Full-Text Search com vetor textual indexado e ranking nativo.",
            "hybrid_postgres": "Score final combina PostgreSQL Full-Text Search com BM25 normalizado.",
            "bm25": "BM25 considera frequência dos termos, raridade e tamanho do documento.",
            "tfidf": "TF-IDF combina frequência do termo com raridade na coleção.",
            "frequency": "Frequência simples valoriza repetição dos termos buscados.",
            "semantic": "Busca semântica usa similaridade vetorial quando embeddings estão disponíveis.",
            "hybrid": "Busca híbrida combina sinais textuais e semânticos.",
        }
        return explanations.get(mode, "Relevância calculada pela estratégia de busca selecionada.")

    def _sort_ranked_payloads(self, ranked_payloads: list[dict], *, sort_by: str | None) -> list[dict]:
        if sort_by == "data-desc":
            return sorted(
                ranked_payloads,
                key=lambda item: (
                    self._effective_document_date(item["payload"]),
                    item["final_score"],
                ),
                reverse=True,
            )
        if sort_by == "data-asc":
            return sorted(
                ranked_payloads,
                key=lambda item: (
                    self._effective_document_date(item["payload"]),
                    -item["final_score"],
                ),
            )
        if sort_by == "titulo":
            return sorted(
                ranked_payloads,
                key=lambda item: (
                    self._normalize_filter_value(item["payload"]["title"]),
                    -item["final_score"],
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
        search_mode: str | None = None,
        text_weight: float | None = None,
        semantic_weight: float | None = None,
    ) -> str | None:
        filters = {
            "category": category,
            "documentType": document_type,
            "author": author,
            "dateFrom": self._stringify_date_filter(date_from),
            "dateTo": self._stringify_date_filter(date_to),
            "sortBy": sort_by,
            "searchMode": search_mode,
            "textWeight": text_weight,
            "semanticWeight": semantic_weight,
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
            "searchMode": None,
            "textWeight": None,
            "semanticWeight": None,
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
        mode: str,
        analysis: QueryAnalysisResult | None = None,
    ) -> dict:
        response = {
            "searchId": None,
            "query": query,
            "mode": mode,
            "searchMode": mode,
            "total": 0,
            "page": page,
            "perPage": per_page,
            "totalPages": 1,
            "responseTimeMs": response_time_ms,
            "items": [],
            "results": [],
        }
        if analysis is not None:
            response["analysis"] = self._analysis_summary(analysis)
        return response


search_service = SearchService(SearchRepository())
