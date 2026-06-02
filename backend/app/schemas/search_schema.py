from pydantic import BaseModel

from app.schemas.query_schema import SearchAnalysisSummary


class SearchResultResponse(BaseModel):
    id: int
    documentId: int | None = None
    document_id: int | None = None
    title: str
    snippet: str
    category: str
    type: str
    documentType: str
    author: str
    fileName: str
    mimeType: str
    size: str
    date: str
    relevance: int
    textualScore: float | None = None
    semanticScore: float | None = None
    finalScore: float | None = None
    searchMode: str | None = None
    matchedTerms: list[str] | None = None
    textual_score: float | None = None
    semantic_score: float | None = None
    final_score: float | None = None
    search_mode: str | None = None
    matched_terms: list[str] | None = None


class SearchResponse(BaseModel):
    searchId: int | None = None
    query: str
    analysis: SearchAnalysisSummary | None = None
    mode: str | None = None
    searchMode: str | None = None
    total: int
    page: int
    perPage: int
    totalPages: int
    responseTimeMs: int
    items: list[SearchResultResponse]
    results: list[SearchResultResponse] | None = None


class SearchHistoryItemResponse(BaseModel):
    id: int
    term: str


class SearchHistoryFiltersResponse(BaseModel):
    category: str | None = None
    documentType: str | None = None
    author: str | None = None
    dateFrom: str | None = None
    dateTo: str | None = None
    sortBy: str | None = None
    searchMode: str | None = None
    textWeight: str | None = None
    semanticWeight: str | None = None


class SearchHistoryEntryResponse(BaseModel):
    id: int
    query: str
    createdAt: str
    resultCount: int
    responseTimeMs: int
    user: str
    filters: SearchHistoryFiltersResponse


class SearchHistoryListResponse(BaseModel):
    total: int
    page: int
    perPage: int
    totalPages: int
    items: list[SearchHistoryEntryResponse]
