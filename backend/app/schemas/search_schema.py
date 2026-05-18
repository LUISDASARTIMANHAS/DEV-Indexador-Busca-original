from pydantic import BaseModel


class SearchResultResponse(BaseModel):
    id: int
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


class SearchResponse(BaseModel):
    query: str
    total: int
    page: int
    perPage: int
    totalPages: int
    responseTimeMs: int
    items: list[SearchResultResponse]


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
