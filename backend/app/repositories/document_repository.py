from pathlib import Path

from sqlalchemy.orm import Session

from app.domain.document import Document
from app.domain.document_category import DocumentCategory
from app.domain.document_history import DocumentHistory
from app.domain.document_metadata import DocumentMetadata
from app.domain.ingestion_history import IngestionHistory
from app.domain.ingestion_status import IngestionStatus
from app.domain.user import User


class DocumentRepository:
    @staticmethod
    def _active_history_query(db: Session, *, active_only: bool = True):
        query = (
            db.query(
                Document.cod_documento.label("id"),
                Document.titulo.label("title"),
                Document.tipo.label("type"),
                Document.data_publicacao.label("document_date"),
                Document.criado_em.label("uploaded_at"),
                DocumentCategory.nome_categoria.label("category"),
                DocumentHistory.numero_versao.label("version"),
                DocumentHistory.caminho_arquivo.label("file_path"),
                DocumentHistory.texto_extraido.label("content"),
                DocumentMetadata.autor.label("document_author"),
                DocumentMetadata.tipo_documento.label("document_type"),
                DocumentMetadata.nome_arquivo_original.label("original_file_name"),
                DocumentMetadata.mime_type.label("mime_type"),
                DocumentMetadata.tamanho_bytes.label("size_bytes"),
                DocumentMetadata.hash_arquivo.label("file_hash"),
                IngestionStatus.estado_ingestao.label("ingestion_status"),
                User.nome.label("uploader_name"),
            )
            .join(DocumentCategory, DocumentCategory.cod_categoria == Document.cod_categoria)
            .join(
                DocumentHistory,
                (DocumentHistory.cod_documento == Document.cod_documento)
                & (DocumentHistory.versao_ativa.is_(True)),
            )
            .join(User, User.cod_usuario == Document.cod_usuario_criador)
            .outerjoin(DocumentMetadata, DocumentMetadata.cod_documento == Document.cod_documento)
            .outerjoin(IngestionHistory, IngestionHistory.cod_documento == Document.cod_documento)
            .outerjoin(IngestionStatus, IngestionStatus.cod_status_ingestao == IngestionHistory.cod_status_ingestao)
        )
        if active_only:
            query = query.filter(Document.ativo.is_(True))
        return query

    @classmethod
    def get_document_payload(
        cls,
        db: Session,
        document_id: int,
        *,
        active_only: bool = True,
    ) -> dict | None:
        row = (
            cls._active_history_query(db, active_only=active_only)
            .filter(Document.cod_documento == document_id)
            .order_by(IngestionHistory.criado_em.desc(), DocumentHistory.numero_versao.desc())
            .first()
        )
        return cls._row_to_payload(row) if row is not None else None

    @classmethod
    def list_ingestion_history(cls, db: Session, limit: int = 20) -> list[dict]:
        rows = (
            cls._active_history_query(db, active_only=False)
            .order_by(IngestionHistory.criado_em.desc(), Document.cod_documento.desc())
            .limit(limit)
            .all()
        )
        return [cls._row_to_payload(row) for row in rows]

    @classmethod
    def list_batch_files(cls, db: Session, limit: int = 10) -> list[dict]:
        rows = (
            cls._active_history_query(db, active_only=False)
            .order_by(IngestionHistory.criado_em.desc(), Document.cod_documento.desc())
            .limit(limit)
            .all()
        )
        return [cls._row_to_payload(row) for row in rows]

    @staticmethod
    def _row_to_payload(row) -> dict:
        fallback_file_name = f"{row.title}.{str(row.type).lower()}"
        file_name = row.original_file_name or fallback_file_name
        file_path = Path(row.file_path)
        size_bytes = row.size_bytes
        if size_bytes is None:
            size_bytes = file_path.stat().st_size if file_path.exists() else 0
        return {
            "id": row.id,
            "title": row.title,
            "type": row.type,
            "document_type": row.document_type or row.type,
            "category": row.category,
            "document_date": row.document_date,
            "uploaded_at": row.uploaded_at,
            "version": row.version,
            "file_path": row.file_path,
            "file_name": file_name,
            "original_file_name": file_name,
            "mime_type": row.mime_type,
            "file_hash": row.file_hash or "",
            "content": row.content,
            "ingestion_status": row.ingestion_status or "concluido",
            "author_name": row.document_author or row.uploader_name,
            "uploaded_by_name": row.uploader_name,
            "size_bytes": int(size_bytes or 0),
        }
