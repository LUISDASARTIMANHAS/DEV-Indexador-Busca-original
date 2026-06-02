from datetime import date

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse, Response

from app.core.logging import logger
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.domain.user import User
from app.domain.user_role import UserRole
from app.schemas.document_schema import (
    DocumentDetailsResponse,
    DocumentMetadataResponse,
    DocumentOperationResponse,
    DocumentVersionResponse,
)
from app.schemas.index_schema import ReindexResponse
from app.services.document_service import document_service
from app.services.metrics_service import metrics_service

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/{document_id}", response_model=DocumentDetailsResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payload = document_service.get_document_payload(db, document_id)
    metrics_service.register_document_access(
        db,
        document_id=document_id,
        user_id=current_user.cod_usuario,
        access_type="view",
        origin="document-view",
    )
    return document_service.to_details_response(payload)


@router.put("/{document_id}", response_model=DocumentDetailsResponse)
def update_document(
    document_id: int,
    file: UploadFile = File(...),
    category: str | None = Form(default=None),
    document_date: date | None = Form(default=None),
    title: str | None = Form(default=None),
    author: str | None = Form(default=None),
    document_type: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    payload = document_service.update_document(
        db,
        document_id=document_id,
        file=file,
        updated_by=current_user,
        category=category,
        document_date=document_date,
        title=title,
        author=author,
        document_type=document_type,
    )
    return document_service.to_details_response(payload)


@router.get("/{document_id}/metadata", response_model=DocumentMetadataResponse)
def get_document_metadata(
    document_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    payload = document_service.get_document_payload(db, document_id)
    return document_service.to_metadata_response(payload)


@router.get("/{document_id}/versions", response_model=list[DocumentVersionResponse])
def list_document_versions(
    document_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return document_service.list_versions(db, document_id)


@router.get("/{document_id}/versions/{version_number}", response_model=DocumentDetailsResponse)
def get_document_version(
    document_id: int,
    version_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payload = document_service.get_document_payload(
        db,
        document_id,
        version_number=version_number,
    )
    metrics_service.register_document_access(
        db,
        document_id=document_id,
        user_id=current_user.cod_usuario,
        access_type="view",
        origin=f"document-version-view:{version_number}",
    )
    return document_service.to_details_response(payload, version_specific=True)


@router.post(
    "/{document_id}/versions/{version_number}/restore",
    response_model=DocumentDetailsResponse,
)
def restore_document_version(
    document_id: int,
    version_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    payload = document_service.restore_version(
        db,
        document_id=document_id,
        version_number=version_number,
        restored_by=current_user,
    )
    return document_service.to_details_response(payload)


@router.get("/{document_id}/versions/{version_number}/download")
def download_document_version(
    document_id: int,
    version_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_path, file_name, media_type = document_service.get_document_file(
        db,
        document_id,
        version_number=version_number,
    )
    metrics_service.register_document_access(
        db,
        document_id=document_id,
        user_id=current_user.cod_usuario,
        access_type="download",
        origin=f"document-version-download:{version_number}",
    )
    return FileResponse(path=file_path, filename=file_name, media_type=media_type)


@router.get("/{document_id}/versions/{version_number}/export")
def export_document_version(
    document_id: int,
    version_number: int,
    format: str = Query("txt", pattern="^(txt|json)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content, file_name, media_type = document_service.export_document(
        db,
        document_id=document_id,
        version_number=version_number,
        export_format=format,
    )
    metrics_service.register_document_access(
        db,
        document_id=document_id,
        user_id=current_user.cod_usuario,
        access_type="export",
        origin=f"document-version-export:{version_number}:{format}",
    )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )


@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_path, file_name, media_type = document_service.get_document_file(db, document_id)
    metrics_service.register_document_access(
        db,
        document_id=document_id,
        user_id=current_user.cod_usuario,
        access_type="download",
        origin="document-download",
    )
    return FileResponse(path=file_path, filename=file_name, media_type=media_type)


@router.get("/{document_id}/export")
def export_document(
    document_id: int,
    format: str = Query("txt", pattern="^(txt|json)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content, file_name, media_type = document_service.export_document(
        db,
        document_id=document_id,
        export_format=format,
    )
    metrics_service.register_document_access(
        db,
        document_id=document_id,
        user_id=current_user.cod_usuario,
        access_type="export",
        origin=f"document-export:{format}",
    )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )


@router.delete("/{document_id}", response_model=DocumentOperationResponse)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    return document_service.delete_document(
        db,
        document_id=document_id,
        deleted_by=current_user,
    )


@router.delete("/{document_id}/physical", response_model=DocumentOperationResponse)
def purge_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    return document_service.purge_document(
        db,
        document_id=document_id,
        deleted_by=current_user,
    )


@router.post("/{document_id}/reindex", response_model=ReindexResponse)
def reindex_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    logger.info(
        "Requisição de reindexação do documento %s recebida por usuário %s (%s)",
        document_id,
        current_user.nome,
        current_user.cod_usuario,
    )
    result = document_service.reindex_document(
        db,
        document_id=document_id,
        triggered_by=current_user,
    )
    logger.info(
        "Documento %s reindexado com sucesso com %s termos",
        document_id,
        result["termCount"],
    )
    return {
        "processedDocuments": 1,
        "successCount": 1,
        "failureCount": 0,
        "message": (
            f"Documento {document_id} reindexado com "
            f"{result['termCount']} termos."
        ),
    }
