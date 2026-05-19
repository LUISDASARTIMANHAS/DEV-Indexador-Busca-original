from datetime import datetime

from pydantic import BaseModel


class NamedValueResponse(BaseModel):
    name: str
    value: int


class MetricsPointResponse(BaseModel):
    day: str
    consultas: int


class MetricsOverviewResponse(BaseModel):
    totalQueries: int
    averageSearchTime: str
    indexedDocuments: int
    successRate: str
    averageResults: str
    queriesToday: int
    queriesWithoutResults: int
    zeroResultsRate: str


class MetricCalculationResponse(BaseModel):
    id: int
    periodStart: str
    periodEnd: str
    totalQueries: int
    averageResponseTimeMs: int
    averageResults: str
    queriesWithoutResults: int
    calculatedAt: str


class MetricsSnapshotResponse(BaseModel):
    overview: MetricsOverviewResponse
    queriesByDay: list[MetricsPointResponse]
    topTerms: list[NamedValueResponse]
    documentsByCategory: list[NamedValueResponse]
    queryOutcomeDistribution: list[NamedValueResponse]
    recentCalculations: list[MetricCalculationResponse]


class FrequentQueryResponse(BaseModel):
    query: str
    count: int
    averageResponseTimeMs: int
    averageResults: str


class AccessedDocumentResponse(BaseModel):
    id: int
    title: str
    category: str
    accessCount: int
    viewCount: int
    downloadCount: int
    exportCount: int
    lastAccessedAt: str | None = None


class SearchReportSummaryResponse(BaseModel):
    periodStart: str
    periodEnd: str
    totalQueries: int
    uniqueQueries: int
    averageResponseTimeMs: int
    averageResults: str
    queriesWithoutResults: int
    zeroResultsRate: str
    indexedDocuments: int
    mostFrequentQuery: str | None = None
    mostAccessedDocument: str | None = None


class SearchReportResponse(BaseModel):
    summary: SearchReportSummaryResponse
    frequentQueries: list[FrequentQueryResponse]
    zeroResultQueries: list[FrequentQueryResponse]
    topTerms: list[NamedValueResponse]
    accessedDocuments: list[AccessedDocumentResponse]
    storedCalculation: MetricCalculationResponse | None = None
