from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.adapters.ocr_adapter import OCRAdapter
from app.core.config import settings
from app.core.logging import logger
from app.domain.document import Document
from app.domain.document_history import DocumentHistory
from app.domain.ocr_history import OCRHistory
from app.domain.user import User
from app.exceptions.document_exceptions import DocumentNotFoundException, DocumentValidationException
from app.services.index_service import index_service


class OCRService:
    def __init__(self, adapter: OCRAdapter | None = None):
        self.adapter = adapter or OCRAdapter()

    def should_run_ocr(self, extracted_text: str | None) -> bool:
        if not settings.OCR_ENABLED:
            return False
        normalized_text = " ".join((extracted_text or "").split())
        return len(normalized_text) < settings.OCR_MIN_TEXT_LENGTH

    def run_ocr_for_file_if_needed(
        self,
        file_path: str,
        extracted_text: str | None,
        *,
        mime_type: str | None,
        extension: str,
        force: bool = False,
    ) -> dict[str, Any]:
        if not self._is_pdf(mime_type=mime_type, extension=extension, file_path=file_path):
            return self._skipped("OCR disponível apenas para PDF.", extracted_text)
        if not force and not self.should_run_ocr(extracted_text):
            return self._skipped("Documento já possui texto extraído suficiente.", extracted_text)
        if not settings.OCR_ENABLED:
            return self._skipped("OCR está desativado na configuração.", extracted_text)

        logger.info("OCR iniciado para arquivo %s", file_path)
        result = self.adapter.extract_text_from_pdf(
            file_path,
            language=settings.OCR_LANGUAGE,
            dpi=settings.OCR_DPI,
            max_pages=settings.OCR_MAX_PAGES,
            timeout_seconds=settings.OCR_TIMEOUT_SECONDS,
        )
        result["ocr_executed"] = True
        result["text_length"] = len(result.get("text") or "")
        result["message"] = (
            "OCR executado e texto extraído atualizado com sucesso."
            if result.get("success") and result.get("text")
            else "OCR executado, mas não retornou texto suficiente."
        )
        return result

    def run_ocr_for_document_version(
        self,
        db: Session,
        document_id: int,
        version_id: int | None = None,
        *,
        force: bool = False,
        triggered_by: User | None = None,
    ) -> dict[str, Any]:
        document = (
            db.query(Document)
            .filter(Document.cod_documento == document_id, Document.ativo.is_(True))
            .first()
        )
        if document is None:
            raise DocumentNotFoundException()

        history = self._get_history(db, document_id=document_id, version_id=version_id)
        if history is None:
            raise DocumentNotFoundException("Versão do documento não encontrada.")

        if not self._is_pdf(
            mime_type=history.mime_type,
            extension=(Path(history.nome_arquivo_original or history.caminho_arquivo).suffix or "").lstrip("."),
            file_path=history.caminho_arquivo,
        ):
            result = self._skipped("OCR disponível apenas para PDF.", history.texto_extraido)
            self._apply_ocr_result(db, history, result, status="skipped")
            db.commit()
            return self._response(document_id, history, result)

        if not force and not self.should_run_ocr(history.texto_extraido):
            result = self._skipped("Documento já possui texto extraído suficiente.", history.texto_extraido)
            self._apply_ocr_result(db, history, result, status="skipped")
            db.commit()
            return self._response(document_id, history, result)

        result = self.run_ocr_for_file_if_needed(
            history.caminho_arquivo,
            history.texto_extraido,
            mime_type=history.mime_type,
            extension=(Path(history.nome_arquivo_original or history.caminho_arquivo).suffix or "pdf").lstrip("."),
            force=True,
        )
        status = "success" if result.get("success") and result.get("text") else "failed"
        self._apply_ocr_result(db, history, result, status=status)
        db.flush()

        if status == "success" and history.versao_ativa and triggered_by is not None:
            index_service.reindex_document(db, document_id=document_id, triggered_by=triggered_by)
        else:
            db.commit()

        return self._response(document_id, history, result)

    def get_document_status(self, db: Session, document_id: int) -> dict[str, Any]:
        document = (
            db.query(Document)
            .filter(Document.cod_documento == document_id)
            .first()
        )
        if document is None:
            raise DocumentNotFoundException()
        versions = (
            db.query(DocumentHistory)
            .filter(DocumentHistory.cod_documento == document_id)
            .order_by(DocumentHistory.numero_versao.desc())
            .all()
        )
        return {
            "document_id": document_id,
            "versions": [self._status_for_history(history) for history in versions],
        }

    def reprocess_pending(
        self,
        db: Session,
        *,
        limit: int = 10,
        triggered_by: User | None = None,
    ) -> dict[str, Any]:
        candidates = (
            db.query(DocumentHistory)
            .join(Document, Document.cod_documento == DocumentHistory.cod_documento)
            .filter(Document.ativo.is_(True))
            .filter(
                or_(
                    DocumentHistory.texto_extraido.is_(None),
                    DocumentHistory.texto_extraido == "",
                    DocumentHistory.ocr_status == "failed",
                    DocumentHistory.ocr_executado.is_(False),
                )
            )
            .order_by(DocumentHistory.criado_em.asc())
            .limit(limit)
            .all()
        )
        results = []
        for history in candidates:
            if not self.should_run_ocr(history.texto_extraido) and history.ocr_status != "failed":
                continue
            try:
                results.append(
                    self.run_ocr_for_document_version(
                        db,
                        int(history.cod_documento),
                        int(history.numero_versao),
                        force=history.ocr_status == "failed",
                        triggered_by=triggered_by,
                    )
                )
            except Exception as exc:
                db.rollback()
                logger.warning("Falha ao reprocessar OCR pendente do documento %s: %s", history.cod_documento, exc)
                results.append(
                    {
                        "document_id": int(history.cod_documento),
                        "version_id": int(history.numero_versao),
                        "ocr_executed": True,
                        "success": False,
                        "message": "Falha ao reprocessar OCR pendente.",
                        "error": str(exc),
                    }
                )
        return {
            "processed": len(results),
            "successCount": sum(1 for item in results if item.get("success")),
            "failureCount": sum(1 for item in results if not item.get("success")),
            "items": results,
        }

    def _get_history(
        self,
        db: Session,
        *,
        document_id: int,
        version_id: int | None,
    ) -> DocumentHistory | None:
        query = db.query(DocumentHistory).filter(DocumentHistory.cod_documento == document_id)
        if version_id is None:
            query = query.filter(DocumentHistory.versao_ativa.is_(True)).order_by(DocumentHistory.numero_versao.desc())
        else:
            query = query.filter(DocumentHistory.numero_versao == version_id)
        return query.first()

    def _apply_ocr_result(
        self,
        db: Session,
        history: DocumentHistory,
        result: dict[str, Any],
        *,
        status: str,
    ) -> None:
        now = datetime.utcnow()
        extracted_text = result.get("text") or ""
        history.ocr_executado = bool(result.get("ocr_executed", status != "skipped"))
        history.ocr_status = status
        history.ocr_idioma = result.get("language") or settings.OCR_LANGUAGE
        history.ocr_paginas_processadas = int(result.get("pages_processed") or 0)
        history.ocr_tempo_ms = int(result.get("processing_time_ms") or 0)
        history.ocr_erro = result.get("error")
        history.ocr_executado_em = now
        if status == "success" and extracted_text:
            history.texto_extraido = extracted_text[:200000]
            history.texto_processado = history.texto_extraido

        db.add(
            OCRHistory(
                cod_documento=history.cod_documento,
                cod_historico_documento=history.cod_historico_documento,
                status=status,
                idioma=history.ocr_idioma,
                paginas_processadas=history.ocr_paginas_processadas,
                tamanho_texto=len(history.texto_extraido or ""),
                tempo_ms=history.ocr_tempo_ms,
                erro=history.ocr_erro,
                executado_em=now,
            )
        )

    def _status_for_history(self, history: DocumentHistory) -> dict[str, Any]:
        return {
            "version_id": int(history.numero_versao),
            "history_id": int(history.cod_historico_documento),
            "active": bool(history.versao_ativa),
            "ocr_executed": bool(history.ocr_executado),
            "ocr_status": history.ocr_status or "pending",
            "ocr_language": history.ocr_idioma,
            "pages_processed": history.ocr_paginas_processadas,
            "processing_time_ms": history.ocr_tempo_ms,
            "error": history.ocr_erro,
            "executed_at": history.ocr_executado_em.isoformat() if history.ocr_executado_em else None,
            "text_length": len(history.texto_extraido or ""),
        }

    def _response(
        self,
        document_id: int,
        history: DocumentHistory,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "document_id": document_id,
            "version_id": int(history.numero_versao),
            "ocr_executed": bool(result.get("ocr_executed")),
            "success": bool(result.get("success")),
            "pages_processed": int(result.get("pages_processed") or 0),
            "text_length": len(history.texto_extraido or ""),
            "processing_time_ms": int(result.get("processing_time_ms") or 0),
            "message": result.get("message"),
            "error": result.get("error"),
        }

    def _skipped(self, message: str, extracted_text: str | None) -> dict[str, Any]:
        return {
            "text": extracted_text or "",
            "pages_processed": 0,
            "language": settings.OCR_LANGUAGE,
            "dpi": settings.OCR_DPI,
            "success": True,
            "error": None,
            "processing_time_ms": 0,
            "ocr_executed": False,
            "text_length": len(extracted_text or ""),
            "message": message,
        }

    def _is_pdf(self, *, mime_type: str | None, extension: str | None, file_path: str | None) -> bool:
        normalized_extension = (extension or "").lower().lstrip(".")
        return (
            normalized_extension == "pdf"
            or (mime_type or "").lower() == "application/pdf"
            or (file_path or "").lower().endswith(".pdf")
        )


ocr_service = OCRService()
