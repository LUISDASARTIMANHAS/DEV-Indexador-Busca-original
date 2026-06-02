from __future__ import annotations

import json
import hashlib
import re
import time
from datetime import date, datetime
from mimetypes import guess_type
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.adapters.document_adapter_registry import document_adapter_registry
from app.core.config import settings
from app.domain.document import Document
from app.domain.document_access_history import DocumentAccessHistory
from app.domain.document_embedding import DocumentEmbedding
from app.domain.document_category import DocumentCategory
from app.domain.document_history import DocumentHistory
from app.domain.document_metadata import DocumentMetadata
from app.domain.index_history import IndexHistory
from app.domain.ingestion_history import IngestionHistory
from app.domain.ingestion_status import IngestionStatus
from app.domain.invalid_document import InvalidDocument
from app.domain.user import User
from app.exceptions.document_exceptions import (
    DocumentNotFoundException,
    DocumentValidationException,
)
from app.repositories.document_repository import DocumentRepository
from app.services.administrative_history_service import administrative_history_service
from app.services.index_service import index_service


class DocumentService:
    def __init__(self, document_repository: DocumentRepository):
        self.document_repository = document_repository
        self.adapter_registry = document_adapter_registry
        self.allowed_extensions = {
            extension.lower() for extension in settings.DOCUMENT_ALLOWED_EXTENSIONS
        }
        self.max_size_bytes = settings.DOCUMENT_MAX_FILE_SIZE_MB * 1024 * 1024
        self.storage_dir = Path(settings.DOCUMENT_UPLOAD_DIR)

    def _read_file_payload(self, file: UploadFile) -> dict:
        content = file.file.read()
        filename = file.filename or ""
        content_type = file.content_type or ""
        file.file.close()
        return {
            "content": content,
            "filename": filename,
            "content_type": content_type,
        }

    def _upload_document_internal(
        self,
        db: Session,
        *,
        content: bytes,
        filename: str,
        content_type: str,
        category: str,
        uploaded_by: User,
        document_date: date | None = None,
        title: str | None = None,
        author: str | None = None,
        document_type: str | None = None,
    ) -> dict:
        started_at = time.perf_counter()
        normalized_category = category.strip()

        try:
            extension = self._extract_extension(filename)
            self._validate_extension(extension)
            adapter = self.adapter_registry.get(extension)
            if not normalized_category:
                raise DocumentValidationException("Informe uma categoria válida para o documento.")
            self._validate_size(content)
            adapter.validate_integrity(content)
            extracted_content = adapter.extract_text(content)
        except DocumentValidationException as exc:
            self._register_invalid_document(db, uploaded_by, filename, exc.detail)
            db.rollback()
            raise

        storage_path = self._store_file(content, extension)
        document_title = self._normalize_metadata_value(
            title,
            fallback=self._build_default_title(filename),
            max_length=255,
        )
        document_author = self._normalize_metadata_value(
            author,
            fallback=uploaded_by.nome,
            max_length=255,
        )
        metadata_document_type = self._normalize_metadata_value(
            document_type,
            fallback=extension.upper(),
            max_length=100,
        )
        original_file_name = self._normalize_metadata_value(
            filename,
            fallback=f"{document_title}.{extension}",
            max_length=255,
        )
        mime_type = self._normalize_metadata_value(
            content_type,
            fallback=adapter.mime_type,
            max_length=255,
        )
        file_hash = hashlib.sha256(content).hexdigest()
        category_row = self._get_or_create_category(db, normalized_category)
        processing_status = self._get_or_create_status(db, "processando")

        document = Document(
            cod_categoria=category_row.cod_categoria,
            titulo=document_title,
            tipo=extension.upper(),
            data_publicacao=self._coerce_document_datetime(document_date),
            ativo=True,
            cod_usuario_criador=uploaded_by.cod_usuario,
        )
        db.add(document)
        db.flush()

        metadata = DocumentMetadata(
            cod_documento=document.cod_documento,
            autor=document_author,
            tipo_documento=metadata_document_type,
            nome_arquivo_original=original_file_name,
            mime_type=mime_type,
            tamanho_bytes=len(content),
            hash_arquivo=file_hash,
        )
        db.add(metadata)
        db.flush()

        history_document = DocumentHistory(
            cod_documento=document.cod_documento,
            cod_usuario=uploaded_by.cod_usuario,
            numero_versao=1,
            caminho_arquivo=str(storage_path),
            nome_arquivo_original=original_file_name,
            mime_type=mime_type,
            tamanho_bytes=len(content),
            hash_arquivo=file_hash,
            texto_extraido=extracted_content,
            texto_processado=extracted_content,
            versao_ativa=True,
        )
        db.add(history_document)
        db.flush()

        ingestion_history = IngestionHistory(
            cod_usuario=uploaded_by.cod_usuario,
            cod_documento=document.cod_documento,
            cod_status_ingestao=processing_status.cod_status_ingestao,
            tipo_ingestao="manual",
            mensagem_erro=None,
            tempo_processamento_ms=0,
        )
        db.add(ingestion_history)
        db.flush()

        try:
            index_service.process_document(
                db,
                document_id=document.cod_documento,
                triggered_by=uploaded_by,
                trigger_label="Ingestão",
            )
            completed_status = self._get_or_create_status(db, "concluido")
            ingestion_history.cod_status_ingestao = completed_status.cod_status_ingestao
            ingestion_history.mensagem_erro = None
        except Exception as exc:
            failed_status = self._get_or_create_status(db, "falha")
            ingestion_history.cod_status_ingestao = failed_status.cod_status_ingestao
            ingestion_history.mensagem_erro = str(exc)[:255]
            ingestion_history.tempo_processamento_ms = int(
                (time.perf_counter() - started_at) * 1000
            )
            db.commit()
            raise

        ingestion_history.tempo_processamento_ms = int((time.perf_counter() - started_at) * 1000)
        db.commit()
        administrative_history_service.log_action(
            db,
            actor=uploaded_by,
            description=f"Upload do documento {document_title}.{extension} concluído.",
            action_type="Ingestão",
            entity_type="documento",
            entity_id=document.cod_documento,
        )

        return self.get_document_payload(db, document.cod_documento)

    def upload_document(
        self,
        db: Session,
        *,
        file: UploadFile,
        category: str,
        uploaded_by: User,
        document_date: date | None = None,
        title: str | None = None,
        author: str | None = None,
        document_type: str | None = None,
    ) -> dict:
        payload = self._read_file_payload(file)
        return self._upload_document_internal(
            db,
            content=payload["content"],
            filename=payload["filename"],
            content_type=payload["content_type"],
            category=category,
            uploaded_by=uploaded_by,
            document_date=document_date,
            title=title,
            author=author,
            document_type=document_type,
        )

    def update_document(
        self,
        db: Session,
        *,
        document_id: int,
        file: UploadFile,
        updated_by: User,
        category: str | None = None,
        document_date: date | None = None,
        title: str | None = None,
        author: str | None = None,
        document_type: str | None = None,
    ) -> dict:
        document = self._get_document_or_raise(db, document_id)
        metadata = self._get_or_create_metadata(db, document)
        filename = file.filename or ""

        try:
            extension = self._extract_extension(filename)
            self._validate_extension(extension)
            adapter = self.adapter_registry.get(extension)
            content = file.file.read()
            self._validate_size(content)
            adapter.validate_integrity(content)
            extracted_content = adapter.extract_text(content)
        except DocumentValidationException as exc:
            self._register_invalid_document(db, updated_by, filename, exc.detail)
            raise
        finally:
            file.file.close()

        storage_path = self._store_file(content, extension)
        file_hash = hashlib.sha256(content).hexdigest()
        new_version_number = self._get_next_version_number(db, document_id)
        current_history = (
            db.query(DocumentHistory)
            .filter(
                DocumentHistory.cod_documento == document_id,
                DocumentHistory.versao_ativa.is_(True),
            )
            .first()
        )
        if current_history is not None:
            self._fill_version_file_metadata(
                current_history,
                file_name=metadata.nome_arquivo_original,
                mime_type=metadata.mime_type,
                size_bytes=metadata.tamanho_bytes,
                file_hash=metadata.hash_arquivo,
            )

        if category and category.strip():
            category_row = self._get_or_create_category(db, category.strip())
            document.cod_categoria = category_row.cod_categoria
        document.titulo = self._normalize_metadata_value(
            title,
            fallback=document.titulo,
            max_length=255,
        )
        document.tipo = extension.upper()
        if document_date is not None:
            document.data_publicacao = self._coerce_document_datetime(document_date)

        metadata.autor = self._normalize_metadata_value(
            author,
            fallback=metadata.autor or updated_by.nome,
            max_length=255,
        )
        metadata.tipo_documento = self._normalize_metadata_value(
            document_type,
            fallback=metadata.tipo_documento or extension.upper(),
            max_length=100,
        )
        metadata.nome_arquivo_original = self._normalize_metadata_value(
            filename,
            fallback=metadata.nome_arquivo_original or f"{document.titulo}.{extension}",
            max_length=255,
        )
        metadata.mime_type = self._normalize_metadata_value(
            file.content_type,
            fallback=adapter.mime_type,
            max_length=255,
        )
        metadata.tamanho_bytes = len(content)
        metadata.hash_arquivo = file_hash

        db.query(DocumentHistory).filter(
            DocumentHistory.cod_documento == document_id,
            DocumentHistory.versao_ativa.is_(True),
        ).update({"versao_ativa": False}, synchronize_session=False)

        new_history = DocumentHistory(
            cod_documento=document_id,
            cod_usuario=updated_by.cod_usuario,
            numero_versao=new_version_number,
            caminho_arquivo=str(storage_path),
            nome_arquivo_original=metadata.nome_arquivo_original,
            mime_type=metadata.mime_type,
            tamanho_bytes=metadata.tamanho_bytes,
            hash_arquivo=metadata.hash_arquivo,
            texto_extraido=extracted_content,
            texto_processado=extracted_content,
            versao_ativa=True,
        )
        db.add(new_history)
        db.flush()

        index_service.reindex_document(
            db,
            document_id=document_id,
            triggered_by=updated_by,
        )

        administrative_history_service.log_action(
            db,
            actor=updated_by,
            description=(
                f"Documento {document.titulo} atualizado para versão "
                f"{new_version_number}."
            ),
            action_type="Atualização",
            entity_type="documento",
            entity_id=document_id,
        )
        return self.get_document_payload(db, document_id)


    def delete_document(
        self,
        db: Session,
        *,
        document_id: int,
        deleted_by: User,
    ) -> dict:
        document = self._get_document_or_raise(db, document_id)
        document.ativo = False
        db.flush()
        index_service.remove_document_from_index(db, document_id=document_id)
        db.commit()
        administrative_history_service.log_action(
            db,
            actor=deleted_by,
            description=f"Documento {document.titulo} removido logicamente.",
            action_type="Remoção",
            entity_type="documento",
            entity_id=document_id,
        )

        return {"message": "Documento removido logicamente com sucesso."}

    def purge_document(
        self,
        db: Session,
        *,
        document_id: int,
        deleted_by: User,
    ) -> dict:
        document = self._get_document_or_raise(db, document_id, active_only=False)
        document_title = document.titulo
        histories = (
            db.query(DocumentHistory)
            .filter(DocumentHistory.cod_documento == document_id)
            .order_by(DocumentHistory.numero_versao.asc())
            .all()
        )
        history_ids = [history.cod_historico_documento for history in histories]
        file_paths = self._collect_document_file_paths(histories)

        document.ativo = False
        db.flush()
        index_service.remove_document_from_index(db, document_id=document_id)

        if history_ids:
            db.query(IndexHistory).filter(
                IndexHistory.cod_historico_documento.in_(history_ids)
            ).delete(synchronize_session=False)

        db.query(IngestionHistory).filter(
            IngestionHistory.cod_documento == document_id
        ).delete(synchronize_session=False)
        db.query(DocumentAccessHistory).filter(
            DocumentAccessHistory.cod_documento == document_id
        ).delete(synchronize_session=False)
        db.query(DocumentEmbedding).filter(
            DocumentEmbedding.cod_documento == document_id
        ).delete(synchronize_session=False)
        db.query(DocumentMetadata).filter(
            DocumentMetadata.cod_documento == document_id
        ).delete(synchronize_session=False)
        db.query(DocumentHistory).filter(
            DocumentHistory.cod_documento == document_id
        ).delete(synchronize_session=False)
        db.query(Document).filter(
            Document.cod_documento == document_id
        ).delete(synchronize_session=False)
        db.flush()
        self._delete_stored_files(file_paths)
        db.commit()

        administrative_history_service.log_action(
            db,
            actor=deleted_by,
            description=f"Documento {document_title} removido fisicamente.",
            action_type="Remoção Física",
            entity_type="documento",
            entity_id=document_id,
        )
        return {"message": "Documento removido fisicamente com sucesso."}


    def list_versions(self, db: Session, document_id: int) -> list[dict]:
        self._get_document_or_raise(db, document_id, active_only=False)
        versions = (
            db.query(DocumentHistory)
            .filter(DocumentHistory.cod_documento == document_id)
            .order_by(DocumentHistory.numero_versao.desc())
            .all()
        )
        return [
            {
                "version": int(v.numero_versao),
                "createdAt": v.criado_em,
                "active": v.versao_ativa,
            }
            for v in versions
        ]

    def restore_version(
        self,
        db: Session,
        *,
        document_id: int,
        version_number: int,
        restored_by: User,
    ) -> dict:
        document = self._get_document_or_raise(db, document_id, active_only=False)
        target_version = (
            db.query(DocumentHistory)
            .filter(
                DocumentHistory.cod_documento == document_id,
                DocumentHistory.numero_versao == version_number,
            )
            .first()
        )
        if not target_version:
            raise DocumentNotFoundException("Versão não encontrada.")

        target_payload = self.get_document_payload(
            db,
            document_id,
            active_only=False,
            version_number=version_number,
        )
        self._fill_version_file_metadata(
            target_version,
            file_name=target_payload["file_name"],
            mime_type=target_payload["mime_type"],
            size_bytes=target_payload["size_bytes"],
            file_hash=target_payload["file_hash"],
        )

        db.query(DocumentHistory).filter(
            DocumentHistory.cod_documento == document_id,
            DocumentHistory.versao_ativa.is_(True),
        ).update({"versao_ativa": False}, synchronize_session=False)
        target_version.versao_ativa = True
        document.ativo = True
        db.flush()

        index_service.reindex_document(
            db,
            document_id=document_id,
            triggered_by=restored_by,
        )
        administrative_history_service.log_action(
            db,
            actor=restored_by,
            description=f"Documento restaurado para versão {version_number}.",
            action_type="Restauração",
            entity_type="documento",
            entity_id=document_id,
        )
        return self.get_document_payload(db, document_id)



    def upload_documents_batch(
        self,
        db: Session,
        *,
        files: list[UploadFile],
        category: str,
        uploaded_by: User,
        document_date: date | None = None,
        author: str | None = None,
        document_type: str | None = None,
    ) -> dict:
        items: list[dict] = []
        success_count = 0
        payloads: list[dict] = []

        for file in files:
            try:
                payloads.append(self._read_file_payload(file))
            except Exception:
                items.append(
                    {
                        "fileName": file.filename or "arquivo-sem-nome",
                        "status": "error",
                        "message": "Falha ao ler o arquivo para upload.",
                        "documentId": None,
                        "extractedCharacters": 0,
                        "sizeLabel": None,
                    }
                )

        for payload in payloads:
            filename = payload.get("filename") or "arquivo-sem-nome"
            try:
                document_payload = self._upload_document_internal(
                    db,
                    content=payload["content"],
                    filename=payload["filename"],
                    content_type=payload["content_type"],
                    category=category,
                    uploaded_by=uploaded_by,
                    document_date=document_date,
                    author=author,
                    document_type=document_type,
                )
                items.append(
                    {
                        "fileName": document_payload["file_name"],
                        "status": "indexed",
                        "message": "Documento validado, extraído e armazenado com sucesso.",
                        "documentId": document_payload["id"],
                        "extractedCharacters": len(document_payload["content"] or ""),
                        "sizeLabel": self._format_size(document_payload["size_bytes"]),
                    }
                )
                success_count += 1
            except DocumentValidationException as exc:
                items.append(
                    {
                        "fileName": filename,
                        "status": "error",
                        "message": exc.detail,
                        "documentId": None,
                        "extractedCharacters": 0,
                        "sizeLabel": None,
                    }
                )
            except Exception:
                self._register_invalid_document(
                    db,
                    uploaded_by,
                    filename,
                    "Falha inesperada no processamento em lote.",
                )
                items.append(
                    {
                        "fileName": filename,
                        "status": "error",
                        "message": "Falha inesperada no processamento do arquivo.",
                        "documentId": None,
                        "extractedCharacters": 0,
                        "sizeLabel": None,
                    }
                )

        total_files = len(files)
        if total_files > 0:
            administrative_history_service.log_action(
                db,
                actor=uploaded_by,
                description=(
                    f"Upload em lote processado: {success_count} sucesso(s), "
                    f"{total_files - success_count} falha(s)."
                ),
                action_type="Ingestão",
                entity_type="lote_documento",
                entity_id=total_files,
            )
        return {
            "totalFiles": total_files,
            "successCount": success_count,
            "failureCount": total_files - success_count,
            "items": items,
        }

    def get_document_payload(
        self,
        db: Session,
        document_id: int,
        *,
        active_only: bool = True,
        version_number: int | None = None,
    ) -> dict:
        payload = self.document_repository.get_document_payload(
            db,
            document_id,
            active_only=active_only,
            version_number=version_number,
        )
        if payload is None:
            if version_number is not None:
                raise DocumentNotFoundException("Versão não encontrada.")
            raise DocumentNotFoundException()
        return payload

    def get_document_file(
        self,
        db: Session,
        document_id: int,
        *,
        version_number: int | None = None,
    ) -> tuple[Path, str, str]:
        payload = self.get_document_payload(
            db,
            document_id,
            version_number=version_number,
        )
        file_path = Path(payload["file_path"])
        if not file_path.exists() or not file_path.is_file():
            raise DocumentNotFoundException("Arquivo físico do documento não encontrado.")

        file_name = payload["file_name"]
        media_type = payload["mime_type"] or guess_type(file_name)[0] or self._get_mime_type(payload["type"].lower())
        return file_path, file_name, media_type

    def export_document(
        self,
        db: Session,
        *,
        document_id: int,
        export_format: str,
        version_number: int | None = None,
    ) -> tuple[str, str, str]:
        payload = self.get_document_payload(
            db,
            document_id,
            version_number=version_number,
        )
        display_title = self._build_display_title(payload["title"], payload["file_name"])
        formatted_content = self._format_content_for_reading(payload["content"])
        preview_content = formatted_content or "Pré-visualização indisponível para este formato."
        safe_title = self._safe_export_filename(display_title)

        if export_format == "json":
            content = json.dumps(
                self.to_details_response(
                    payload,
                    version_specific=version_number is not None,
                ),
                ensure_ascii=False,
                indent=2,
            )
            return content, f"{safe_title}.json", "application/json; charset=utf-8"

        metadata = [
            f"Título: {display_title}",
            f"Categoria: {payload['category']}",
            f"Tipo documental: {payload['document_type']}",
            f"Formato: {payload['type']}",
            f"Autor: {payload['author_name']}",
            f"Enviado por: {payload['uploaded_by_name']}",
            f"Arquivo original: {payload['file_name']}",
            f"MIME: {payload['mime_type'] or self._get_mime_type(payload['type'].lower())}",
            f"Hash SHA-256: {payload['file_hash']}",
            f"Versão: {payload['version']}",
            f"Data do documento: {payload['document_date'] or payload['uploaded_at']}",
            "",
            "Conteúdo extraído:",
            preview_content,
        ]
        return "\n".join(metadata), f"{safe_title}.txt", "text/plain; charset=utf-8"

    def reindex_document(self, db: Session, *, document_id: int, triggered_by: User) -> dict:
        return index_service.reindex_document(
            db,
            document_id=document_id,
            triggered_by=triggered_by,
        )

    def list_ingestion_history(self, db: Session, limit: int = 20) -> list[dict]:
        return self.document_repository.list_ingestion_history(db, limit=limit)

    def list_ingestion_history_entries(self, db: Session, limit: int = 20) -> list[dict]:
        entries = [
            (payload["uploaded_at"], self.to_history_response(payload))
            for payload in self.list_ingestion_history(db, limit=limit)
        ]
        invalid_documents = (
            db.query(InvalidDocument)
            .order_by(
                InvalidDocument.criado_em.desc(),
                InvalidDocument.cod_documentos_invalidos.desc(),
            )
            .limit(limit)
            .all()
        )
        entries.extend(
            (
                row.criado_em,
                {
                    "date": row.criado_em.strftime("%Y-%m-%d %H:%M") if row.criado_em else "",
                    "file": row.nome_arquivo,
                    "type": "Rejeitado",
                    "result": "Falha",
                    "details": row.motivo_erro,
                },
            )
            for row in invalid_documents
        )
        entries.sort(key=lambda item: item[0] or datetime.min, reverse=True)
        return [entry for _, entry in entries[:limit]]

    def list_batch_files(self, db: Session, limit: int = 10) -> list[dict]:
        return self.document_repository.list_batch_files(db, limit=limit)

    def to_upload_response(self, payload: dict) -> dict:
        document_date = payload["document_date"].date() if payload["document_date"] else None
        extracted_characters = len(payload["content"] or "")
        file_path = Path(payload["file_path"])
        download_url = (
            f"/api/v1/documents/{payload['id']}/download"
            if file_path.exists() and file_path.is_file()
            else None
        )
        return {
            "id": payload["id"],
            "title": payload["title"],
            "fileName": payload["file_name"],
            "category": payload["category"],
            "type": payload["type"],
            "documentType": payload["document_type"],
            "author": payload["author_name"],
            "mimeType": payload["mime_type"] or self._get_mime_type(payload["type"].lower()),
            "sizeBytes": payload["size_bytes"],
            "sizeLabel": self._format_size(payload["size_bytes"]),
            "date": document_date,
            "uploadedAt": payload["uploaded_at"],
            "validated": True,
            "integrityOk": True,
            "hash": payload["file_hash"],
            "extracted": True,
            "extractedCharacters": extracted_characters,
        }

    def to_history_response(self, payload: dict) -> dict:
        created_at = payload["uploaded_at"]
        extracted_characters = len(payload["content"] or "")
        details = (
            f"Validado ({payload['type']}) • Extraído {extracted_characters} caracteres • "
            f"Status {payload['ingestion_status']}"
        )
        return {
            "date": created_at.strftime("%Y-%m-%d %H:%M") if created_at else "",
            "file": payload["file_name"],
            "type": "Individual",
            "result": "Sucesso" if payload["ingestion_status"] == "concluido" else "Falha",
            "details": details,
        }

    def to_batch_response(self, payload: dict) -> dict:
        status = "indexed" if payload["ingestion_status"] == "concluido" else "error"
        return {
            "name": payload["file_name"],
            "size": self._format_size(payload["size_bytes"]),
            "status": status,
        }

    def to_details_response(self, payload: dict, *, version_specific: bool = False) -> dict:
        document_date = (
            payload["document_date"].isoformat()
            if payload["document_date"]
            else payload["uploaded_at"].isoformat()
        )
        raw_content = payload["content"] or ""
        formatted_content = self._format_content_for_reading(raw_content)
        preview_content = raw_content or "Pré-visualização indisponível para este formato."
        readable_content = formatted_content or preview_content
        display_title = self._build_display_title(payload["title"], payload["file_name"])
        extracted_characters = len(raw_content)
        file_path = Path(payload["file_path"])
        download_path = (
            f"/api/v1/documents/{payload['id']}/versions/{int(payload['version'])}/download"
            if version_specific
            else f"/api/v1/documents/{payload['id']}/download"
        )
        download_url = (
            download_path
            if file_path.exists() and file_path.is_file()
            else None
        )
        return {
            "id": payload["id"],
            "title": payload["title"],
            "displayTitle": display_title,
            "fileName": payload["file_name"],
            "category": payload["category"],
            "type": payload["type"],
            "documentType": payload["document_type"],
            "date": document_date,
            "author": payload["author_name"],
            "uploadedBy": payload["uploaded_by_name"],
            "format": payload["type"],
            "mimeType": payload["mime_type"] or self._get_mime_type(payload["type"].lower()),
            "pages": 1,
            "version": int(payload["version"]),
            "indexedAt": payload["uploaded_at"].isoformat(),
            "sizeBytes": payload["size_bytes"],
            "size": self._format_size(payload["size_bytes"]),
            "hash": payload["file_hash"],
            "downloadUrl": download_url,
            "content": preview_content,
            "formattedContent": readable_content,
            "extractedCharacters": extracted_characters,
        }

    def to_metadata_response(self, payload: dict) -> dict:
        document_date = (
            payload["document_date"].isoformat()
            if payload["document_date"]
            else None
        )
        return {
            "id": payload["id"],
            "title": payload["title"],
            "author": payload["author_name"],
            "uploadedBy": payload["uploaded_by_name"],
            "category": payload["category"],
            "documentType": payload["document_type"],
            "fileFormat": payload["type"],
            "fileName": payload["file_name"],
            "mimeType": payload["mime_type"] or self._get_mime_type(payload["type"].lower()),
            "sizeBytes": payload["size_bytes"],
            "sizeLabel": self._format_size(payload["size_bytes"]),
            "hash": payload["file_hash"],
            "publicationDate": document_date,
            "uploadedAt": payload["uploaded_at"],
            "version": int(payload["version"]),
        }

    def _get_or_create_category(self, db: Session, category_name: str) -> DocumentCategory:
        category = (
            db.query(DocumentCategory)
            .filter(DocumentCategory.nome_categoria.ilike(category_name))
            .first()
        )
        if category is not None:
            return category

        category = DocumentCategory(nome_categoria=category_name)
        db.add(category)
        db.flush()
        return category

    def _get_or_create_status(self, db: Session, status_name: str) -> IngestionStatus:
        status = (
            db.query(IngestionStatus)
            .filter(IngestionStatus.estado_ingestao == status_name)
            .first()
        )
        if status is not None:
            return status

        status = IngestionStatus(estado_ingestao=status_name)
        db.add(status)
        db.flush()
        return status

    def _get_document_or_raise(
        self,
        db: Session,
        document_id: int,
        *,
        active_only: bool = True,
    ) -> Document:
        query = db.query(Document).filter(Document.cod_documento == document_id)
        if active_only:
            query = query.filter(Document.ativo.is_(True))
        document = query.first()
        if document is None:
            raise DocumentNotFoundException()
        return document

    def _get_or_create_metadata(self, db: Session, document: Document) -> DocumentMetadata:
        metadata = (
            db.query(DocumentMetadata)
            .filter(DocumentMetadata.cod_documento == document.cod_documento)
            .first()
        )
        if metadata is not None:
            return metadata

        metadata = DocumentMetadata(
            cod_documento=document.cod_documento,
            autor=None,
            tipo_documento=document.tipo,
            nome_arquivo_original=f"{document.titulo}.{document.tipo.lower()}",
            mime_type=self._get_mime_type(document.tipo.lower()),
            tamanho_bytes=0,
            hash_arquivo="",
        )
        db.add(metadata)
        db.flush()
        return metadata

    def _get_next_version_number(self, db: Session, document_id: int) -> int:
        last_version = (
            db.query(DocumentHistory)
            .filter(DocumentHistory.cod_documento == document_id)
            .order_by(DocumentHistory.numero_versao.desc())
            .first()
        )
        return int(last_version.numero_versao if last_version else 0) + 1

    @staticmethod
    def _fill_version_file_metadata(
        history: DocumentHistory,
        *,
        file_name: str,
        mime_type: str | None,
        size_bytes: int,
        file_hash: str,
    ) -> None:
        if not history.nome_arquivo_original:
            history.nome_arquivo_original = file_name
        if not history.mime_type:
            history.mime_type = mime_type
        if history.tamanho_bytes is None:
            history.tamanho_bytes = size_bytes
        if not history.hash_arquivo:
            history.hash_arquivo = file_hash

    def _register_invalid_document(
        self, db: Session, uploaded_by: User, filename: str, reason: str
    ) -> None:
        invalid_document = InvalidDocument(
            cod_usuario=uploaded_by.cod_usuario,
            nome_arquivo=filename or "arquivo-sem-nome",
            motivo_erro=reason[:255],
        )
        db.add(invalid_document)
        db.commit()

    def _coerce_document_datetime(self, value: date | None) -> datetime | None:
        if value is None:
            return None
        return datetime.combine(value, datetime.min.time())

    def _extract_extension(self, filename: str) -> str:
        extension = Path(filename).suffix.lower().lstrip(".")
        if not extension:
            raise DocumentValidationException("O arquivo enviado não possui extensão suportada.")
        return extension

    def _validate_extension(self, extension: str) -> None:
        if extension not in self.allowed_extensions:
            allowed = ", ".join(sorted(ext.upper() for ext in self.allowed_extensions))
            raise DocumentValidationException(
                f"Tipo de arquivo inválido. Formatos aceitos: {allowed}."
            )

    def _validate_size(self, content: bytes) -> None:
        if not content:
            raise DocumentValidationException("O arquivo enviado está vazio.")
        if len(content) > self.max_size_bytes:
            raise DocumentValidationException(
                f"Arquivo excede o tamanho máximo permitido de {settings.DOCUMENT_MAX_FILE_SIZE_MB} MB."
            )

    def _store_file(self, content: bytes, extension: str) -> Path:
        now = datetime.utcnow()
        target_dir = self.storage_dir / str(now.year) / f"{now.month:02d}" / extension.lower()
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{uuid4().hex}.{extension}"
        target.write_bytes(content)
        return target

    def _format_size(self, size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        return f"{size_bytes / (1024 * 1024):.1f} MB"

    def _get_mime_type(self, extension: str) -> str:
        return self.adapter_registry.get(extension).mime_type

    def _safe_export_filename(self, value: str) -> str:
        safe = "".join(char if char.isalnum() or char in ("-", "_") else "_" for char in value.strip())
        return safe.strip("_") or "documento"

    def _collect_document_file_paths(
        self,
        histories: list[DocumentHistory],
    ) -> list[Path]:
        paths: list[Path] = []
        for history in histories:
            if not history.caminho_arquivo:
                continue
            path = Path(history.caminho_arquivo)
            if path not in paths:
                paths.append(path)
        return paths

    def _delete_stored_files(self, file_paths: list[Path]) -> None:
        for path in file_paths:
            try:
                if path.exists() and path.is_file():
                    path.unlink()
                    self._cleanup_empty_storage_dirs(path.parent)
            except OSError as exc:
                raise DocumentValidationException(
                    "Falha ao remover arquivo físico do documento."
                ) from exc

    def _cleanup_empty_storage_dirs(self, directory: Path) -> None:
        current = directory
        storage_root = self.storage_dir.resolve()
        while current.exists():
            try:
                current_resolved = current.resolve()
            except OSError:
                break
            if current_resolved == storage_root.parent or storage_root not in current_resolved.parents and current_resolved != storage_root:
                break
            if current_resolved == storage_root:
                break
            if any(current.iterdir()):
                break
            current.rmdir()
            current = current.parent

    def _build_default_title(self, filename: str) -> str:
        stem = Path(filename).stem.strip()
        if not stem:
            stem = f"documento-{uuid4().hex[:8]}"
        return self._build_display_title(stem, filename)

    def _build_display_title(self, title: str | None, file_name: str | None = None) -> str:
        candidate = (title or "").strip()
        if not candidate and file_name:
            candidate = Path(file_name).stem.strip()
        if not candidate:
            return "Documento"

        normalized_stem = self._normalize_title_key(Path(file_name).stem) if file_name else ""
        should_humanize = "_" in candidate or (
            normalized_stem
            and normalized_stem == self._normalize_title_key(candidate)
            and candidate.count("-") >= 2
            and " " not in candidate
        )
        if not should_humanize:
            return candidate

        readable = candidate.replace("_", " ")
        if " " not in readable and readable.count("-") >= 2:
            readable = readable.replace("-", " ")
        readable = re.sub(r"\s+", " ", readable).strip()
        if readable and readable[0].islower():
            readable = readable[0].upper() + readable[1:]
        return readable or candidate

    def _normalize_title_key(self, value: str) -> str:
        return re.sub(r"[\W_]+", "", (value or "").casefold())

    def _format_content_for_reading(self, content: str | None) -> str:
        text = (content or "").replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ").strip()
        if not text:
            return ""

        text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n[ \t]+", "\n", text)
        text = re.sub(r"[ \t]{2,}", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        blocks: list[str] = []
        buffer = ""

        def flush_buffer() -> None:
            nonlocal buffer
            normalized = buffer.strip()
            if normalized:
                blocks.append(normalized)
            buffer = ""

        for raw_line in text.split("\n"):
            line = self._normalize_reading_line(raw_line)
            if not line:
                flush_buffer()
                continue
            if self._should_skip_reading_line(line):
                continue
            if self._is_heading_line(line):
                flush_buffer()
                blocks.append(line)
                continue
            if not buffer:
                buffer = line
                continue
            if self._is_block_start(line):
                flush_buffer()
                buffer = line
                continue
            if self._should_merge_reading_line(buffer, line):
                if buffer.endswith("-") and line[:1].islower():
                    buffer = f"{buffer[:-1]}{line}"
                else:
                    buffer = f"{buffer} {line}"
                continue
            flush_buffer()
            buffer = line

        flush_buffer()
        return "\n\n".join(blocks)

    def _normalize_reading_line(self, line: str) -> str:
        normalized = re.sub(r"\s+", " ", (line or "").strip())
        normalized = re.sub(r"\s+([,.;:!?])", r"\1", normalized)
        return normalized

    def _should_skip_reading_line(self, line: str) -> bool:
        if re.fullmatch(r"\d{1,3}", line):
            return True
        return bool(re.fullmatch(r"p[aá]gina\s+\d+(?:\s+de\s+\d+)?", line, flags=re.IGNORECASE))

    def _is_heading_line(self, line: str) -> bool:
        if not line:
            return False
        if self._is_block_start(line):
            return False
        if re.match(
            r"^(MINIST[ÉE]RIO|SECRETARIA|INSTITUTO|CAMPUS|CONSELHO|COMISS[ÃA]O|"
            r"PR[ÓO]-REITORIA|PROGRAMA|ANEXO|AP[ÊE]NDICE|CAP[ÍI]TULO|SE[ÇC][ÃA]O|"
            r"T[IÍ]TULO|CONSIDERANDO|RESOLVE)\b",
            line,
            flags=re.IGNORECASE,
        ):
            return True
        if len(line) > 90:
            return False
        if "," in line:
            return False

        words = re.findall(r"[A-Za-zÀ-ÿ0-9ºª]+", line)
        if not words or len(words) > 12:
            return False

        alpha_chars = [char for char in line if char.isalpha()]
        if alpha_chars:
            uppercase_ratio = sum(char.isupper() for char in alpha_chars) / len(alpha_chars)
            if uppercase_ratio >= 0.72:
                return True

        capitalized_words = sum(word[:1].isupper() for word in words if word[:1].isalpha())
        return capitalized_words >= max(2, int(len(words) * 0.6))

    def _is_block_start(self, line: str) -> bool:
        return bool(
            re.match(
                r"^(Art\.?\s*\d+[ºo°]?\b|Artigo\s+\d+\b|Par[aá]grafo\s+[úu]nico\b|"
                r"§+\s*\d*[ºo°]?\b|[IVXLCDM]+\s*-\s+|[a-z]\)\s+|\d+\)\s+|\d+\.\s+)",
                line,
                flags=re.IGNORECASE,
            )
        )

    def _should_merge_reading_line(self, current_block: str, next_line: str) -> bool:
        if not current_block or not next_line:
            return False
        if current_block.endswith(":"):
            return False
        return not bool(re.search(r"[.!?;]$", current_block))

    def _normalize_metadata_value(
        self,
        value: str | None,
        *,
        fallback: str,
        max_length: int,
    ) -> str:
        normalized = (value or "").strip() or fallback.strip()
        return normalized[:max_length]







document_service = DocumentService(DocumentRepository())
