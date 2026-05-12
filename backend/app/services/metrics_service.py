from __future__ import annotations

from collections import Counter
from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.document import Document
from app.domain.document_category import DocumentCategory
from app.domain.search_history import SearchHistory
from app.services.index_service import index_service
from app.utils.text_processing import preprocess_for_indexing


class MetricsService:
    def snapshot(self, db: Session) -> dict:
        index_snapshot = index_service.get_status_snapshot(db)
        total_queries = db.query(func.count(SearchHistory.cod_historico_busca)).scalar() or 0
        average_search_time = db.query(func.avg(SearchHistory.tempo_resposta_ms)).scalar()
        average_results = db.query(func.avg(SearchHistory.quantidade_resultados)).scalar()
        queries_without_results = (
            db.query(func.count(SearchHistory.cod_historico_busca))
            .filter(SearchHistory.quantidade_resultados <= 0)
            .scalar()
            or 0
        )
        zero_results_rate = (
            (queries_without_results / total_queries) * 100
            if total_queries
            else 0
        )

        today = date.today()
        queries_today = (
            db.query(func.count(SearchHistory.cod_historico_busca))
            .filter(func.date(SearchHistory.criado_em) == today.isoformat())
            .scalar()
            or 0
        )

        queries_by_day = []
        for days_ago in range(6, -1, -1):
            current_day = today - timedelta(days=days_ago)
            count = (
                db.query(func.count(SearchHistory.cod_historico_busca))
                .filter(func.date(SearchHistory.criado_em) == current_day.isoformat())
                .scalar()
                or 0
            )
            queries_by_day.append(
                {
                    "day": current_day.strftime("%d/%m"),
                    "consultas": count,
                }
            )

        term_counter: Counter[str] = Counter()
        recent_queries = db.query(SearchHistory.consulta_texto).all()
        for row in recent_queries:
            for token in preprocess_for_indexing(row.consulta_texto or "")["tokens"]:
                term_counter[token] += 1

        top_terms = [
            {"name": term, "value": count}
            for term, count in term_counter.most_common(5)
        ]

        documents_by_category_rows = (
            db.query(
                DocumentCategory.nome_categoria,
                func.count(Document.cod_documento),
            )
            .join(Document, Document.cod_categoria == DocumentCategory.cod_categoria)
            .filter(Document.ativo.is_(True))
            .group_by(DocumentCategory.nome_categoria)
            .order_by(func.count(Document.cod_documento).desc())
            .all()
        )
        documents_by_category = [
            {"name": row[0], "value": row[1]}
            for row in documents_by_category_rows
        ]
        query_outcome_distribution = [
            {
                "name": "Com resultados",
                "value": max(total_queries - queries_without_results, 0),
            },
            {
                "name": "Sem resultados",
                "value": queries_without_results,
            },
        ]

        return {
            "overview": {
                "totalQueries": total_queries,
                "averageSearchTime": self._format_duration(average_search_time),
                "indexedDocuments": index_snapshot["indexedDocuments"],
                "successRate": index_snapshot["successRate"],
                "averageResults": f"{float(average_results or 0):.1f}",
                "queriesToday": queries_today,
                "queriesWithoutResults": queries_without_results,
                "zeroResultsRate": f"{zero_results_rate:.1f}%",
            },
            "queriesByDay": queries_by_day,
            "topTerms": top_terms,
            "documentsByCategory": documents_by_category,
            "queryOutcomeDistribution": query_outcome_distribution,
        }

    def _format_duration(self, duration_ms: float | None) -> str:
        if duration_ms is None:
            return "0 ms"
        duration_ms = float(duration_ms)
        if duration_ms >= 1000:
            return f"{duration_ms / 1000:.2f}s"
        return f"{duration_ms:.0f} ms"


metrics_service = MetricsService()
