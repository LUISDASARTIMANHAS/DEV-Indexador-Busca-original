from pydantic import BaseModel


class IndexLogEntryResponse(BaseModel):
    time: str
    message: str
    type: str


class IndexSummaryResponse(BaseModel):
    completed: int
    processing: int
    failed: int


class IndexConsistencyResponse(BaseModel):
    documentsWithoutActiveVersion: int
    documentsWithoutIndex: int
    orphanIndexEntries: int
    staleTerms: int


class IndexMetricsResponse(BaseModel):
    activeDocuments: int
    activeVersions: int
    totalTerms: int
    totalPostings: int
    averageTermsPerDocument: str
    lastIndexedAt: str | None = None
    ocrDocuments: int = 0
    ocrSuccess: int = 0
    ocrFailed: int = 0
    averageOcrTimeMs: int = 0


class IndexStatusResponse(BaseModel):
    indexedDocuments: int
    averageTime: str
    successRate: str
    errors: int
    integrityOk: bool
    inconsistencyCount: int
    currentProgress: int
    remainingEstimate: str
    summary: IndexSummaryResponse
    consistency: IndexConsistencyResponse
    metrics: IndexMetricsResponse
    logs: list[IndexLogEntryResponse]


class ReindexResponse(BaseModel):
    processedDocuments: int
    successCount: int
    failureCount: int
    message: str
