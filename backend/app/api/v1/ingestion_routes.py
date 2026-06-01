from datetime import date

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.core.logging import logger

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.domain.user import User
from app.domain.user_role import UserRole
from app.schemas.document_schema import (
    BatchUploadResponse,
    DocumentUploadResponse,
    IngestionBatchFileResponse,
    IngestionHistoryEntryResponse,
)
from app.services.document_service import document_service

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_document(
    file: UploadFile = File(...),
    category: str = Form(...),
    document_date: date | None = Form(default=None),
    title: str | None = Form(default=None),
    author: str | None = Form(default=None),
    document_type: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    logger.info(
        "Upload de documento iniciado por usuário %s (%s): filename=%s category=%s",
        current_user.nome,
        current_user.cod_usuario,
        file.filename,
        category,
    )
    document = document_service.upload_document(
        db,
        file=file,
        category=category,
        uploaded_by=current_user,
        document_date=document_date,
        title=title,
        author=author,
        document_type=document_type,
    )
    response = document_service.to_upload_response(document)
    logger.info(
        "Upload de documento concluído: document_id=%s title=%s",
        response["id"],
        response["title"],
    )
    return response


@router.post(
    "/upload-batch",
    response_model=BatchUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_documents_batch(
    files: list[UploadFile] = File(...),
    category: str = Form(...),
    document_date: date | None = Form(default=None),
    author: str | None = Form(default=None),
    document_type: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    logger.info(
        "Upload em lote iniciado por usuário %s (%s): arquivos=%s categoria=%s",
        current_user.nome,
        current_user.cod_usuario,
        len(files),
        category,
    )
    response = document_service.upload_documents_batch(
        db,
        files=files,
        category=category,
        uploaded_by=current_user,
        document_date=document_date,
        author=author,
        document_type=document_type,
    )
    logger.info(
        "Upload em lote concluído: arquivos processados=%s",
        len(response.get("items", [])),
    )
    return response


@router.get("/batch", response_model=list[IngestionBatchFileResponse])
def get_batch_files(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    logger.info("Listagem de arquivos em lote solicitada")
    documents = document_service.list_batch_files(db)
    return [document_service.to_batch_response(document) for document in documents]


@router.get("/history", response_model=list[IngestionHistoryEntryResponse])
def get_ingestion_history(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    logger.info("Listagem de histórico de ingestão solicitada")
    return document_service.list_ingestion_history_entries(db)
