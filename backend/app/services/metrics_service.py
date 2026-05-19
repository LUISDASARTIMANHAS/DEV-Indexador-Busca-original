from __future__ import annotations

from collections import Counter
from datetime import date, datetime, time as dt_time, timedelta

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.domain.document import Document
from app.domain.document_access_history import DocumentAccessHistory
from app.domain.document_category import DocumentCategory
from app.domain.metric_calculation import MetricCalculation
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
            "recentCalculations": self.list_calculations(db, limit=5),
        }

    def build_report(
        self,
        db: Session,
        *,
        date_from: date | str | None = None,
        date_to: date | str | None = None,
        include_stored_calculation: bool = False,
    ) -> dict:
        normalized_from = self._coerce_date_boundary(date_from, end_of_day=False)
        normalized_to = self._coerce_date_boundary(date_to, end_of_day=True)
        history_rows = self._load_search_history_rows(
            db,
            date_from=normalized_from,
            date_to=normalized_to,
        )
        frequent_queries, zero_result_queries = self._build_query_frequency_stats(history_rows)
        top_terms = self._build_top_terms(history_rows, limit=10)
        accessed_documents = self._build_accessed_documents(
            db,
            date_from=normalized_from,
            date_to=normalized_to,
            limit=10,
        )
        summary = self._build_report_summary(
            db,
            history_rows=history_rows,
            frequent_queries=frequent_queries,
            accessed_documents=accessed_documents,
            date_from=normalized_from,
            date_to=normalized_to,
        )
        stored_calculation = None
        if include_stored_calculation:
            stored_calculation = self.persist_calculation(
                db,
                date_from=date_from,
                date_to=date_to,
            )

        return {
            "summary": summary,
            "frequentQueries": frequent_queries,
            "zeroResultQueries": zero_result_queries,
            "topTerms": top_terms,
            "accessedDocuments": accessed_documents,
            "storedCalculation": stored_calculation,
        }

    def persist_calculation(
        self,
        db: Session,
        *,
        date_from: date | str | None = None,
        date_to: date | str | None = None,
    ) -> dict:
        report = self.build_report(
            db,
            date_from=date_from,
            date_to=date_to,
            include_stored_calculation=False,
        )
        normalized_from = self._coerce_date_boundary(date_from, end_of_day=False)
        normalized_to = self._coerce_date_boundary(date_to, end_of_day=True)
        period_start, period_end = self._resolve_report_period(
            history_rows=self._load_search_history_rows(
                db,
                date_from=normalized_from,
                date_to=normalized_to,
            ),
            date_from=normalized_from,
            date_to=normalized_to,
        )

        record = (
            db.query(MetricCalculation)
            .filter(
                MetricCalculation.periodo_inicio == period_start,
                MetricCalculation.periodo_fim == period_end,
            )
            .first()
        )
        if record is None:
            record = MetricCalculation(
                periodo_inicio=period_start,
                periodo_fim=period_end,
            )
            db.add(record)

        summary = report["summary"]
        record.total_consultas = summary["totalQueries"]
        record.tempo_medio_respostas = summary["averageResponseTimeMs"]
        record.media_resultados = int(round(float(summary["averageResults"] or 0)))
        record.consultas_sem_resultado = summary["queriesWithoutResults"]
        db.commit()
        db.refresh(record)
        return self._serialize_calculation(record)

    def list_calculations(self, db: Session, *, limit: int = 20) -> list[dict]:
        rows = (
            db.query(MetricCalculation)
            .order_by(
                MetricCalculation.calculado_em.desc(),
                MetricCalculation.cod_calculo_metricas.desc(),
            )
            .limit(limit)
            .all()
        )
        return [self._serialize_calculation(row) for row in rows]

    def export_report(
        self,
        db: Session,
        *,
        export_format: str,
        date_from: date | str | None = None,
        date_to: date | str | None = None,
    ) -> tuple[str, str, str]:
        report = self.build_report(
            db,
            date_from=date_from,
            date_to=date_to,
            include_stored_calculation=False,
        )
        file_stub = self._report_filename_stub(
            date_from=report["summary"]["periodStart"],
            date_to=report["summary"]["periodEnd"],
        )

        if export_format == "json":
            import json

            return (
                json.dumps(report, ensure_ascii=False, indent=2),
                f"{file_stub}.json",
                "application/json; charset=utf-8",
            )

        csv_lines = [
            "section,key,value,extra1,extra2,extra3,extra4",
            f'summary,totalQueries,{report["summary"]["totalQueries"]},,,,',
            f'summary,uniqueQueries,{report["summary"]["uniqueQueries"]},,,,',
            f'summary,averageResponseTimeMs,{report["summary"]["averageResponseTimeMs"]},,,,',
            f'summary,averageResults,{report["summary"]["averageResults"]},,,,',
            f'summary,queriesWithoutResults,{report["summary"]["queriesWithoutResults"]},,,,',
            f'summary,zeroResultsRate,{report["summary"]["zeroResultsRate"]},,,,',
            f'summary,indexedDocuments,{report["summary"]["indexedDocuments"]},,,,',
        ]

        for item in report["frequentQueries"]:
            csv_lines.append(
                self._csv_line(
                    "frequentQueries",
                    item["query"],
                    item["count"],
                    item["averageResponseTimeMs"],
                    item["averageResults"],
                )
            )
        for item in report["zeroResultQueries"]:
            csv_lines.append(
                self._csv_line(
                    "zeroResultQueries",
                    item["query"],
                    item["count"],
                    item["averageResponseTimeMs"],
                    item["averageResults"],
                )
            )
        for item in report["topTerms"]:
            csv_lines.append(self._csv_line("topTerms", item["name"], item["value"]))
        for item in report["accessedDocuments"]:
            csv_lines.append(
                self._csv_line(
                    "accessedDocuments",
                    item["title"],
                    item["accessCount"],
                    item["category"],
                    item["viewCount"],
                    item["downloadCount"],
                    item["exportCount"],
                )
            )

        return (
            "\n".join(csv_lines),
            f"{file_stub}.csv",
            "text/csv; charset=utf-8",
        )

    def register_document_access(
        self,
        db: Session,
        *,
        document_id: int,
        user_id: int,
        access_type: str,
        origin: str | None = None,
    ) -> bool:
        try:
            db.add(
                DocumentAccessHistory(
                    cod_documento=document_id,
                    cod_usuario=user_id,
                    tipo_acesso=access_type[:20],
                    origem=(origin or access_type)[:80],
                )
            )
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False

    def _format_duration(self, duration_ms: float | None) -> str:
        if duration_ms is None:
            return "0 ms"
        duration_ms = float(duration_ms)
        if duration_ms >= 1000:
            return f"{duration_ms / 1000:.2f}s"
        return f"{duration_ms:.0f} ms"

    def _load_search_history_rows(
        self,
        db: Session,
        *,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> list[SearchHistory]:
        query = db.query(SearchHistory)
        if date_from is not None:
            query = query.filter(SearchHistory.criado_em >= date_from)
        if date_to is not None:
            query = query.filter(SearchHistory.criado_em <= date_to)
        return query.order_by(SearchHistory.criado_em.asc()).all()

    def _build_query_frequency_stats(
        self,
        history_rows: list[SearchHistory],
        *,
        limit: int = 10,
    ) -> tuple[list[dict], list[dict]]:
        query_stats: dict[str, dict[str, int | str]] = {}
        zero_result_stats: dict[str, dict[str, int | str]] = {}

        for row in history_rows:
            query_text = (row.consulta_texto or "").strip()
            if not query_text:
                continue
            result_count = int(row.quantidade_resultados or 0)
            response_time_ms = int(row.tempo_resposta_ms or 0)

            stats = query_stats.setdefault(
                query_text,
                {
                    "query": query_text,
                    "count": 0,
                    "total_response_time_ms": 0,
                    "total_results": 0,
                },
            )
            stats["count"] += 1
            stats["total_response_time_ms"] += response_time_ms
            stats["total_results"] += result_count

            if result_count <= 0:
                zero_stats = zero_result_stats.setdefault(
                    query_text,
                    {
                        "query": query_text,
                        "count": 0,
                        "total_response_time_ms": 0,
                    },
                )
                zero_stats["count"] += 1
                zero_stats["total_response_time_ms"] += response_time_ms

        frequent_queries = sorted(
            (
                {
                    "query": stats["query"],
                    "count": int(stats["count"]),
                    "averageResponseTimeMs": self._average_int(
                        int(stats["total_response_time_ms"]),
                        int(stats["count"]),
                    ),
                    "averageResults": f"{(int(stats['total_results']) / int(stats['count'])):.1f}",
                }
                for stats in query_stats.values()
            ),
            key=lambda item: (-item["count"], item["query"]),
        )[:limit]
        zero_result_queries = sorted(
            (
                {
                    "query": stats["query"],
                    "count": int(stats["count"]),
                    "averageResponseTimeMs": self._average_int(
                        int(stats["total_response_time_ms"]),
                        int(stats["count"]),
                    ),
                    "averageResults": "0.0",
                }
                for stats in zero_result_stats.values()
            ),
            key=lambda item: (-item["count"], item["query"]),
        )[:limit]
        return frequent_queries, zero_result_queries

    def _build_top_terms(
        self,
        history_rows: list[SearchHistory],
        *,
        limit: int,
    ) -> list[dict]:
        term_counter: Counter[str] = Counter()
        for row in history_rows:
            for token in preprocess_for_indexing(row.consulta_texto or "")["tokens"]:
                term_counter[token] += 1
        return [
            {"name": term, "value": count}
            for term, count in term_counter.most_common(limit)
        ]

    def _build_accessed_documents(
        self,
        db: Session,
        *,
        date_from: datetime | None,
        date_to: datetime | None,
        limit: int,
    ) -> list[dict]:
        query = (
            db.query(
                Document.cod_documento.label("document_id"),
                Document.titulo.label("title"),
                DocumentCategory.nome_categoria.label("category"),
                func.count(DocumentAccessHistory.cod_acesso_documento).label("access_count"),
                func.sum(case((DocumentAccessHistory.tipo_acesso == "view", 1), else_=0)).label("view_count"),
                func.sum(case((DocumentAccessHistory.tipo_acesso == "download", 1), else_=0)).label("download_count"),
                func.sum(case((DocumentAccessHistory.tipo_acesso == "export", 1), else_=0)).label("export_count"),
                func.max(DocumentAccessHistory.criado_em).label("last_accessed_at"),
            )
            .join(Document, Document.cod_documento == DocumentAccessHistory.cod_documento)
            .join(DocumentCategory, DocumentCategory.cod_categoria == Document.cod_categoria)
            .group_by(
                Document.cod_documento,
                Document.titulo,
                DocumentCategory.nome_categoria,
            )
            .order_by(
                func.count(DocumentAccessHistory.cod_acesso_documento).desc(),
                Document.titulo.asc(),
            )
        )
        if date_from is not None:
            query = query.filter(DocumentAccessHistory.criado_em >= date_from)
        if date_to is not None:
            query = query.filter(DocumentAccessHistory.criado_em <= date_to)

        rows = query.limit(limit).all()
        return [
            {
                "id": int(row.document_id),
                "title": row.title,
                "category": row.category,
                "accessCount": int(row.access_count or 0),
                "viewCount": int(row.view_count or 0),
                "downloadCount": int(row.download_count or 0),
                "exportCount": int(row.export_count or 0),
                "lastAccessedAt": row.last_accessed_at.isoformat() if row.last_accessed_at else None,
            }
            for row in rows
        ]

    def _build_report_summary(
        self,
        db: Session,
        *,
        history_rows: list[SearchHistory],
        frequent_queries: list[dict],
        accessed_documents: list[dict],
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> dict:
        total_queries = len(history_rows)
        total_results = sum(int(row.quantidade_resultados or 0) for row in history_rows)
        total_response_time_ms = sum(int(row.tempo_resposta_ms or 0) for row in history_rows)
        queries_without_results = sum(
            1 for row in history_rows if int(row.quantidade_resultados or 0) <= 0
        )
        unique_queries = len({(row.consulta_texto or "").strip() for row in history_rows if (row.consulta_texto or "").strip()})
        average_response_time_ms = self._average_int(total_response_time_ms, total_queries)
        average_results = (
            f"{(total_results / total_queries):.1f}" if total_queries else "0.0"
        )
        zero_results_rate = (
            f"{(queries_without_results / total_queries) * 100:.1f}%"
            if total_queries
            else "0.0%"
        )
        period_start, period_end = self._resolve_report_period(
            history_rows=history_rows,
            date_from=date_from,
            date_to=date_to,
        )
        return {
            "periodStart": period_start.isoformat(),
            "periodEnd": period_end.isoformat(),
            "totalQueries": total_queries,
            "uniqueQueries": unique_queries,
            "averageResponseTimeMs": average_response_time_ms,
            "averageResults": average_results,
            "queriesWithoutResults": queries_without_results,
            "zeroResultsRate": zero_results_rate,
            "indexedDocuments": index_service.get_status_snapshot(db)["indexedDocuments"],
            "mostFrequentQuery": frequent_queries[0]["query"] if frequent_queries else None,
            "mostAccessedDocument": accessed_documents[0]["title"] if accessed_documents else None,
        }

    def _resolve_report_period(
        self,
        *,
        history_rows: list[SearchHistory],
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> tuple[datetime, datetime]:
        fallback_start = datetime.combine(date.today(), dt_time.min)
        fallback_end = datetime.combine(date.today(), dt_time.max)
        period_start = date_from or (
            history_rows[0].criado_em if history_rows and history_rows[0].criado_em else fallback_start
        )
        period_end = date_to or (
            history_rows[-1].criado_em if history_rows and history_rows[-1].criado_em else fallback_end
        )
        return period_start, period_end

    def _serialize_calculation(self, row: MetricCalculation) -> dict:
        return {
            "id": int(row.cod_calculo_metricas),
            "periodStart": row.periodo_inicio.isoformat(),
            "periodEnd": row.periodo_fim.isoformat(),
            "totalQueries": int(row.total_consultas or 0),
            "averageResponseTimeMs": int(float(row.tempo_medio_respostas or 0)),
            "averageResults": f"{float(row.media_resultados or 0):.1f}",
            "queriesWithoutResults": int(row.consultas_sem_resultado or 0),
            "calculatedAt": row.calculado_em.isoformat() if row.calculado_em else "",
        }

    def _report_filename_stub(self, *, date_from: str, date_to: str) -> str:
        safe_from = date_from.split("T", 1)[0].replace("-", "")
        safe_to = date_to.split("T", 1)[0].replace("-", "")
        return f"relatorio-busca-{safe_from}-{safe_to}"

    def _csv_line(
        self,
        section: str,
        key: str,
        value: int | str,
        extra1: int | str | None = None,
        extra2: int | str | None = None,
        extra3: int | str | None = None,
        extra4: int | str | None = None,
    ) -> str:
        values = [
            section,
            key,
            value,
            extra1 if extra1 is not None else "",
            extra2 if extra2 is not None else "",
            extra3 if extra3 is not None else "",
            extra4 if extra4 is not None else "",
        ]
        return ",".join(self._csv_escape(item) for item in values)

    def _csv_escape(self, value: int | str) -> str:
        return f'"{str(value).replace(chr(34), chr(34) * 2)}"'

    def _average_int(self, total: int, count: int) -> int:
        if count <= 0:
            return 0
        return int(round(total / count))

    def _coerce_date_boundary(
        self,
        value: date | str | None,
        *,
        end_of_day: bool,
    ) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, str):
            parsed_date = date.fromisoformat(value)
        else:
            parsed_date = value
        return datetime.combine(
            parsed_date,
            dt_time.max if end_of_day else dt_time.min,
        )


metrics_service = MetricsService()
