from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from os import cpu_count

from sqlalchemy import case, func
from sqlalchemy.orm import Session, sessionmaker

from app.core.logging import logger
from app.domain.document import Document
from app.domain.document_field import DocumentField
from app.domain.document_history import DocumentHistory
from app.domain.index_history import IndexHistory
from app.domain.ingestion_history import IngestionHistory
from app.domain.ingestion_status import IngestionStatus
from app.domain.inverted_index import InvertedIndex
from app.domain.term import Term
from app.domain.user import User
from app.exceptions.document_exceptions import DocumentNotFoundException
from app.pipeline.document_ingestion_pipeline import DocumentIngestionPipeline
from app.pipeline.stages import (
    RelationalIndexPersistStage,
    SemanticEmbeddingPersistStage,
    TextPreprocessStage,
    TextTokenizeStage,
)
from app.repositories.document_repository import DocumentRepository
from app.services.administrative_history_service import administrative_history_service
from app.services.inverted_index_service import inverted_index_service


class IndexService:
    def __init__(self):
        self.document_repository = DocumentRepository()
        self.pipeline = DocumentIngestionPipeline(
            [
                TextPreprocessStage(),
                TextTokenizeStage(),
                RelationalIndexPersistStage(),
                SemanticEmbeddingPersistStage(),
            ]
        )

    def process_document(
        self,
        db: Session,
        *,
        document_id: int,
        triggered_by: User,
        trigger_label: str = "Ingestão",
    ) -> dict:
        document = (
            db.query(Document)
            .filter(Document.cod_documento == document_id, Document.ativo.is_(True))
            .first()
        )
        if document is None:
            raise DocumentNotFoundException()

        document_history = (
            db.query(DocumentHistory)
            .filter(
                DocumentHistory.cod_documento == document_id,
                DocumentHistory.versao_ativa.is_(True),
            )
            .order_by(DocumentHistory.numero_versao.desc())
            .first()
        )
        if document_history is None:
            raise DocumentNotFoundException("Versão ativa do documento não encontrada.")

        logger.info(
            "Processando indexação do documento %s trigger=%s usuario=%s",
            document_id,
            trigger_label,
            triggered_by.nome,
        )
        started_at = time.perf_counter()
        payload = self.document_repository.get_document_payload(db, document_id)
        context = {
            "document_id": document.cod_documento,
            "document_history": document_history,
            "field_texts": self._build_search_fields(payload, document_history),
        }

        try:
            with db.begin_nested():
                result = self.pipeline.run(db, context)
                db.add(
                    IndexHistory(
                        cod_historico_documento=document_history.cod_historico_documento,
                        tempo_indexacao_ms=int((time.perf_counter() - started_at) * 1000),
                        mensagem_erro=None,
                    )
                )
            db.flush()
            db.commit()
            logger.info(
                "Indexação do documento %s concluída em %sms",
                document_id,
                int((time.perf_counter() - started_at) * 1000),
            )
        except Exception as exc:
            db.add(
                IndexHistory(
                    cod_historico_documento=document_history.cod_historico_documento,
                    tempo_indexacao_ms=int((time.perf_counter() - started_at) * 1000),
                    mensagem_erro=str(exc)[:255],
                )
            )
            db.commit()
            logger.exception(
                "Falha na indexação do documento %s depois de %sms",
                document_id,
                int((time.perf_counter() - started_at) * 1000),
            )
            raise

        administrative_history_service.log_action(
            db,
            actor=triggered_by,
            description=(
                f"{trigger_label} do documento {document.titulo} concluída com "
                f"{result['term_count']} termos indexados."
            ),
            action_type=trigger_label,
            entity_type="documento",
            entity_id=document.cod_documento,
        )
        return {
            "documentId": document.cod_documento,
            "termCount": result["term_count"],
            "tokenCount": result["token_count"],
        }

    def _build_search_fields(
        self,
        payload: dict | None,
        document_history: DocumentHistory,
    ) -> list[dict]:
        payload = payload or {}
        candidates = [
            ("titulo", payload.get("title")),
            ("autor", payload.get("author_name")),
            ("categoria", payload.get("category")),
            ("tipo_documento", payload.get("document_type")),
            ("arquivo", payload.get("file_name")),
            ("conteudo", document_history.texto_extraido or ""),
        ]
        return [
            {
                "field_type": field_type,
                "text": str(value),
            }
            for field_type, value in candidates
            if value
        ]

    def reindex_document(self, db: Session, *, document_id: int, triggered_by: User) -> dict:
        logger.info("Iniciando reindexação do documento %s", document_id)
        inverted_index_service.remove_document_terms(
            db,
            document_id=document_id,
            refresh_statistics=False,
        )
        return self.process_document(
            db,
            document_id=document_id,
            triggered_by=triggered_by,
            trigger_label="Reindexação",
        )

    def _reindex_document_in_new_session(
        self,
        bind,
        document_id: int,
        triggered_by_id: int,
    ) -> None:
        worker_session = sessionmaker(autocommit=False, autoflush=False, bind=bind)
        db = worker_session()
        try:
            triggered_by = (
                db.query(User)
                .filter(User.cod_usuario == triggered_by_id)
                .first()
            )
            if triggered_by is None:
                raise DocumentNotFoundException("Usuário responsável não encontrado.")
            self.reindex_document(db, document_id=document_id, triggered_by=triggered_by)
        finally:
            db.close()

    def remove_document_from_index(self, db: Session, *, document_id: int) -> dict:
        return inverted_index_service.remove_document_terms(
            db,
            document_id=document_id,
        )

    def reindex_all_documents(self, db: Session, *, triggered_by: User) -> dict:
        document_ids = [
            row.cod_documento
            for row in db.query(Document.cod_documento)
            .filter(Document.ativo.is_(True))
            .order_by(Document.cod_documento.asc())
            .all()
        ]

        logger.info(
            "Iniciando reindexação de todos os documentos: encontrado(s) %s documento(s)",
            len(document_ids),
        )
        success_count = 0
        failure_count = 0

        if db.get_bind().dialect.name == "sqlite":
            for document_id in document_ids:
                try:
                    self.reindex_document(db, document_id=document_id, triggered_by=triggered_by)
                    success_count += 1
                except Exception as exc:
                    db.rollback()
                    failure_count += 1
                    logger.warning(
                        "Falha na reindexação do documento %s: %s",
                        document_id,
                        exc,
                    )
        elif document_ids:
            max_workers = min(4, cpu_count() or 1, len(document_ids))
            bind = db.get_bind()
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_document = {
                    executor.submit(
                        self._reindex_document_in_new_session,
                        bind,
                        document_id,
                        triggered_by.cod_usuario,
                    ): document_id
                    for document_id in document_ids
                }

                for future in as_completed(future_to_document):
                    document_id = future_to_document[future]
                    try:
                        future.result()
                        success_count += 1
                        logger.debug("Reindexação bem-sucedida para documento %s", document_id)
                    except Exception as exc:
                        failure_count += 1
                        logger.warning(
                            "Falha na reindexação do documento %s: %s",
                            document_id,
                            exc,
                        )

        inverted_index_service.refresh_all_term_statistics(db)
        db.commit()
        logger.info(
            "Reindexação de todos os documentos concluída: %s sucesso(s), %s falha(s)",
            success_count,
            failure_count,
        )

        return {
            "processedDocuments": len(document_ids),
            "successCount": success_count,
            "failureCount": failure_count,
            "message": (
                f"Reindexação concluída: {success_count} sucesso(s), "
                f"{failure_count} falha(s)."
            ),
        }

    def optimize_index(self, db: Session, *, triggered_by: User) -> dict:
        """Otimiza o índice atualizando todas as estatísticas globais (DF/IDF).

        Args:
            db: Sessão do banco de dados.
            triggered_by: Usuário que disparou a ação.

        Returns:
            Dicionário com o resumo da otimização.
        """
        started_at = time.perf_counter()
        logger.info("Iniciando otimização do índice")
        term_count = inverted_index_service.refresh_all_term_statistics(db)
        db.commit()

        duration_ms = int((time.perf_counter() - started_at) * 1000)
        logger.info(
            "Otimização do índice concluída em %sms com %s termos atualizados",
            duration_ms,
            term_count,
        )
        administrative_history_service.log_action(
            db,
            actor=triggered_by,
            description=f"Otimização do índice concluída: {term_count} termos atualizados.",
            action_type="Otimização",
            entity_type="indice",
            entity_id=0,
        )

        return {
            "termCount": term_count,
            "durationMs": duration_ms,
            "message": f"Otimização concluída com sucesso. {term_count} termos atualizados.",
        }

    def get_status_snapshot(self, db: Session) -> dict:
        total_runs = db.query(func.count(IndexHistory.cod_historico_indexacao)).scalar() or 0
        success_runs = (
            db.query(func.count(IndexHistory.cod_historico_indexacao))
            .filter(IndexHistory.mensagem_erro.is_(None))
            .scalar()
            or 0
        )
        error_runs = total_runs - success_runs
        average_ms = (
            db.query(func.avg(IndexHistory.tempo_indexacao_ms))
            .filter(IndexHistory.mensagem_erro.is_(None))
            .scalar()
        )
        indexed_documents = (
            db.query(func.count(func.distinct(DocumentHistory.cod_documento)))
            .join(
                IndexHistory,
                IndexHistory.cod_historico_documento == DocumentHistory.cod_historico_documento,
            )
            .filter(DocumentHistory.versao_ativa.is_(True))
            .filter(IndexHistory.mensagem_erro.is_(None))
            .scalar()
            or 0
        )

        ingestion_summary = (
            db.query(
                func.sum(
                    case((IngestionStatus.estado_ingestao == "concluido", 1), else_=0)
                ).label("completed"),
                func.sum(
                    case((IngestionStatus.estado_ingestao == "processando", 1), else_=0)
                ).label("processing"),
                func.sum(
                    case((IngestionStatus.estado_ingestao == "falha", 1), else_=0)
                ).label("failed"),
            )
            .select_from(IngestionHistory)
            .join(
                IngestionStatus,
                IngestionStatus.cod_status_ingestao == IngestionHistory.cod_status_ingestao,
            )
            .first()
        )

        recent_logs = (
            db.query(
                IndexHistory.criado_em,
                IndexHistory.mensagem_erro,
                Document.titulo,
            )
            .join(
                DocumentHistory,
                DocumentHistory.cod_historico_documento == IndexHistory.cod_historico_documento,
            )
            .join(Document, Document.cod_documento == DocumentHistory.cod_documento)
            .order_by(
                IndexHistory.criado_em.desc(),
                IndexHistory.cod_historico_indexacao.desc(),
            )
            .limit(20)
            .all()
        )
        consistency = self._build_consistency_report(db)
        metrics = self._build_metrics_report(db)
        logs = [
            {
                "time": row.criado_em.strftime("%H:%M:%S") if row.criado_em else "",
                "message": (
                    f"{row.titulo} indexado com sucesso."
                    if row.mensagem_erro is None
                    else f"{row.titulo} falhou: {row.mensagem_erro}"
                ),
                "type": "success" if row.mensagem_erro is None else "error",
            }
            for row in recent_logs
        ]
        if not consistency["integrity_ok"]:
            logs.insert(
                0,
                {
                    "time": "",
                    "message": (
                        "Inconsistências detectadas no índice: "
                        f"{consistency['inconsistency_count']} ocorrência(s)."
                    ),
                    "type": "error",
                },
            )

        return {
            "indexedDocuments": indexed_documents,
            "averageTime": self._format_duration(average_ms),
            "successRate": f"{round((success_runs / total_runs) * 100, 1) if total_runs else 0:.1f}%",
            "errors": error_runs,
            "integrityOk": consistency["integrity_ok"],
            "inconsistencyCount": consistency["inconsistency_count"],
            "currentProgress": 100 if total_runs else 0,
            "remainingEstimate": "0 min",
            "summary": {
                "completed": int(ingestion_summary.completed or 0) if ingestion_summary else 0,
                "processing": int(ingestion_summary.processing or 0) if ingestion_summary else 0,
                "failed": int(ingestion_summary.failed or 0) if ingestion_summary else 0,
            },
            "consistency": {
                "documentsWithoutActiveVersion": consistency["documents_without_active_version"],
                "documentsWithoutIndex": consistency["documents_without_index"],
                "orphanIndexEntries": consistency["orphan_index_entries"],
                "staleTerms": consistency["stale_terms"],
            },
            "metrics": {
                "activeDocuments": metrics["active_documents"],
                "activeVersions": metrics["active_versions"],
                "totalTerms": metrics["total_terms"],
                "totalPostings": metrics["total_postings"],
                "averageTermsPerDocument": metrics["average_terms_per_document"],
                "lastIndexedAt": metrics["last_indexed_at"],
                "ocrDocuments": metrics["ocr_documents"],
                "ocrSuccess": metrics["ocr_success"],
                "ocrFailed": metrics["ocr_failed"],
                "averageOcrTimeMs": metrics["average_ocr_time_ms"],
            },
            "logs": logs,
        }

    def _format_duration(self, duration_ms: float | None) -> str:
        if duration_ms is None:
            return "0 ms"
        duration_ms = float(duration_ms)
        if duration_ms >= 1000:
            return f"{duration_ms / 1000:.2f}s"
        return f"{duration_ms:.0f} ms"

    def _build_consistency_report(self, db: Session) -> dict:
        active_documents = (
            db.query(func.count(Document.cod_documento))
            .filter(Document.ativo.is_(True))
            .scalar()
            or 0
        )
        documents_with_active_version = (
            db.query(func.count(func.distinct(DocumentHistory.cod_documento)))
            .join(Document, Document.cod_documento == DocumentHistory.cod_documento)
            .filter(Document.ativo.is_(True))
            .filter(DocumentHistory.versao_ativa.is_(True))
            .scalar()
            or 0
        )
        documents_with_index = (
            db.query(func.count(func.distinct(DocumentHistory.cod_documento)))
            .select_from(InvertedIndex)
            .join(
                DocumentField,
                DocumentField.cod_campo_documento == InvertedIndex.cod_campo_documento,
            )
            .join(
                DocumentHistory,
                DocumentHistory.cod_historico_documento == DocumentField.cod_historico_documento,
            )
            .join(Document, Document.cod_documento == DocumentHistory.cod_documento)
            .filter(Document.ativo.is_(True))
            .filter(DocumentHistory.versao_ativa.is_(True))
            .scalar()
            or 0
        )
        orphan_index_entries = (
            db.query(func.count(InvertedIndex.cod_indice_invertido))
            .select_from(InvertedIndex)
            .outerjoin(
                DocumentField,
                DocumentField.cod_campo_documento == InvertedIndex.cod_campo_documento,
            )
            .outerjoin(
                DocumentHistory,
                DocumentHistory.cod_historico_documento == DocumentField.cod_historico_documento,
            )
            .outerjoin(Document, Document.cod_documento == DocumentHistory.cod_documento)
            .filter(
                (DocumentField.cod_campo_documento.is_(None))
                | (DocumentHistory.cod_historico_documento.is_(None))
                | (Document.cod_documento.is_(None))
                | (Document.ativo.is_(False))
                | (DocumentHistory.versao_ativa.is_(False))
            )
            .scalar()
            or 0
        )
        actual_df_subquery = (
            db.query(
                InvertedIndex.cod_termo.label("cod_termo"),
                func.count(func.distinct(DocumentHistory.cod_documento)).label("actual_df"),
            )
            .select_from(InvertedIndex)
            .join(
                DocumentField,
                DocumentField.cod_campo_documento == InvertedIndex.cod_campo_documento,
            )
            .join(
                DocumentHistory,
                DocumentHistory.cod_historico_documento == DocumentField.cod_historico_documento,
            )
            .join(Document, Document.cod_documento == DocumentHistory.cod_documento)
            .filter(Document.ativo.is_(True))
            .filter(DocumentHistory.versao_ativa.is_(True))
            .group_by(InvertedIndex.cod_termo)
            .subquery()
        )
        stale_terms = (
            db.query(func.count(Term.cod_termo))
            .outerjoin(actual_df_subquery, actual_df_subquery.c.cod_termo == Term.cod_termo)
            .filter(
                func.coalesce(Term.df, 0) != func.coalesce(actual_df_subquery.c.actual_df, 0)
            )
            .scalar()
            or 0
        )

        documents_without_active_version = max(active_documents - documents_with_active_version, 0)
        documents_without_index = max(documents_with_active_version - documents_with_index, 0)
        inconsistency_count = (
            documents_without_active_version
            + documents_without_index
            + orphan_index_entries
            + stale_terms
        )
        return {
            "documents_without_active_version": documents_without_active_version,
            "documents_without_index": documents_without_index,
            "orphan_index_entries": orphan_index_entries,
            "stale_terms": stale_terms,
            "inconsistency_count": inconsistency_count,
            "integrity_ok": inconsistency_count == 0,
        }

    def _build_metrics_report(self, db: Session) -> dict:
        active_documents = (
            db.query(func.count(Document.cod_documento))
            .filter(Document.ativo.is_(True))
            .scalar()
            or 0
        )
        active_versions = (
            db.query(func.count(DocumentHistory.cod_historico_documento))
            .join(Document, Document.cod_documento == DocumentHistory.cod_documento)
            .filter(Document.ativo.is_(True))
            .filter(DocumentHistory.versao_ativa.is_(True))
            .scalar()
            or 0
        )
        total_terms = db.query(func.count(Term.cod_termo)).scalar() or 0
        total_postings = db.query(func.count(InvertedIndex.cod_indice_invertido)).scalar() or 0
        last_indexed_at = (
            db.query(func.max(IndexHistory.criado_em))
            .filter(IndexHistory.mensagem_erro.is_(None))
            .scalar()
        )
        average_terms_per_document = (
            f"{(total_postings / active_documents):.1f}" if active_documents else "0.0"
        )
        ocr_documents = (
            db.query(func.count(DocumentHistory.cod_historico_documento))
            .join(Document, Document.cod_documento == DocumentHistory.cod_documento)
            .filter(Document.ativo.is_(True))
            .filter(DocumentHistory.versao_ativa.is_(True))
            .filter(DocumentHistory.ocr_executado.is_(True))
            .scalar()
            or 0
        )
        ocr_success = (
            db.query(func.count(DocumentHistory.cod_historico_documento))
            .join(Document, Document.cod_documento == DocumentHistory.cod_documento)
            .filter(Document.ativo.is_(True))
            .filter(DocumentHistory.versao_ativa.is_(True))
            .filter(DocumentHistory.ocr_status == "success")
            .scalar()
            or 0
        )
        ocr_failed = (
            db.query(func.count(DocumentHistory.cod_historico_documento))
            .join(Document, Document.cod_documento == DocumentHistory.cod_documento)
            .filter(Document.ativo.is_(True))
            .filter(DocumentHistory.versao_ativa.is_(True))
            .filter(DocumentHistory.ocr_status == "failed")
            .scalar()
            or 0
        )
        average_ocr_time_ms = (
            db.query(func.avg(DocumentHistory.ocr_tempo_ms))
            .join(Document, Document.cod_documento == DocumentHistory.cod_documento)
            .filter(Document.ativo.is_(True))
            .filter(DocumentHistory.versao_ativa.is_(True))
            .filter(DocumentHistory.ocr_status == "success")
            .scalar()
        )

        return {
            "active_documents": active_documents,
            "active_versions": active_versions,
            "total_terms": total_terms,
            "total_postings": total_postings,
            "average_terms_per_document": average_terms_per_document,
            "last_indexed_at": last_indexed_at.isoformat() if last_indexed_at else None,
            "ocr_documents": ocr_documents,
            "ocr_success": ocr_success,
            "ocr_failed": ocr_failed,
            "average_ocr_time_ms": int(average_ocr_time_ms or 0),
        }


index_service = IndexService()
