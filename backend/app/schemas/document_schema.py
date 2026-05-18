from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class DocumentUploadResponse(BaseModel):
    id: int
    title: str
    fileName: str
    category: str
    type: str
    documentType: str
    author: str
    mimeType: str
    sizeBytes: int
    sizeLabel: str
    date: date | None
    uploadedAt: datetime
    validated: bool
    integrityOk: bool
    hash: str
    extracted: bool
    extractedCharacters: int


class DocumentDetailsResponse(BaseModel):
    id: int
    title: str
    displayTitle: str | None = None
    fileName: str
    category: str
    type: str
    documentType: str
    date: str
    author: str
    uploadedBy: str
    format: str
    mimeType: str
    pages: int
    version: int
    indexedAt: str
    sizeBytes: int
    size: str
    hash: str
    downloadUrl: str | None = None
    content: str
    formattedContent: str | None = None
    extractedCharacters: int


class DocumentMetadataResponse(BaseModel):
    id: int
    title: str
    author: str
    uploadedBy: str
    category: str
    documentType: str
    fileFormat: str
    fileName: str
    mimeType: str
    sizeBytes: int
    sizeLabel: str
    hash: str
    publicationDate: str | None = None
    uploadedAt: datetime
    version: int


class DocumentVersionResponse(BaseModel):
    version: int
    createdAt: datetime
    active: bool


class DocumentOperationResponse(BaseModel):
    message: str


class IngestionBatchFileResponse(BaseModel):
    name: str
    size: str
    status: str


class BatchUploadItemResponse(BaseModel):
    fileName: str
    status: str
    message: str
    documentId: int | None = None
    extractedCharacters: int = 0
    sizeLabel: str | None = None


class BatchUploadResponse(BaseModel):
    totalFiles: int
    successCount: int
    failureCount: int
    items: list[BatchUploadItemResponse]


class IngestionHistoryEntryResponse(BaseModel):
    date: str
    file: str
    type: str
    result: str
    details: str

    model_config = ConfigDict(from_attributes=True)
