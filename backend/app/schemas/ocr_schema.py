from pydantic import BaseModel


class OcrRunResponse(BaseModel):
    document_id: int
    version_id: int | None = None
    ocr_executed: bool
    success: bool
    pages_processed: int = 0
    text_length: int = 0
    processing_time_ms: int = 0
    message: str | None = None
    error: str | None = None


class OcrVersionStatus(BaseModel):
    version_id: int
    history_id: int
    active: bool
    ocr_executed: bool
    ocr_status: str | None = None
    ocr_language: str | None = None
    pages_processed: int | None = None
    processing_time_ms: int | None = None
    error: str | None = None
    executed_at: str | None = None
    text_length: int = 0


class OcrStatusResponse(BaseModel):
    document_id: int
    versions: list[OcrVersionStatus]


class OcrReprocessResponse(BaseModel):
    processed: int
    successCount: int
    failureCount: int
    items: list[OcrRunResponse]
