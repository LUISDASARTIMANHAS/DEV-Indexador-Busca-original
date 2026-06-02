from typing import Any

from pydantic import BaseModel, Field


class QueryFilters(BaseModel):
    year: int | None = None
    type: str | None = None
    category: str | None = None
    author: str | None = None
    date_from: str | None = None
    date_to: str | None = None


class DetectedFields(BaseModel):
    years: list[int] = Field(default_factory=list)
    file_types: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    authors: list[str] = Field(default_factory=list)


class QueryAnalysisRequest(BaseModel):
    query: str


class QueryAnalysisResult(BaseModel):
    raw_query: str
    normalized_query: str
    tokens: list[str] = Field(default_factory=list)
    terms: list[str] = Field(default_factory=list)
    filters: QueryFilters = Field(default_factory=QueryFilters)
    phrases: list[str] = Field(default_factory=list)
    excluded_terms: list[str] = Field(default_factory=list)
    operators: list[dict[str, Any]] = Field(default_factory=list)
    detected_fields: DetectedFields = Field(default_factory=DetectedFields)
    intent: str = "search_documents"
    is_valid: bool = True
    warnings: list[str] = Field(default_factory=list)


class SearchAnalysisSummary(BaseModel):
    terms: list[str] = Field(default_factory=list)
    filters: QueryFilters = Field(default_factory=QueryFilters)
    phrases: list[str] = Field(default_factory=list)
    excluded_terms: list[str] = Field(default_factory=list)
    intent: str = "search_documents"
    warnings: list[str] = Field(default_factory=list)
