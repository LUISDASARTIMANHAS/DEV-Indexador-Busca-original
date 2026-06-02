export type UserRole = "Administrador" | "Usuário";

export type UserSummary = {
  id: number;
  name: string;
  login: string;
  email: string;
  role: UserRole;
  active: boolean;
};

export type SessionUser = UserSummary & {
  token: string;
};

export type SearchFilters = {
  category?: string;
  documentType?: string;
  author?: string;
  dateFrom?: string;
  dateTo?: string;
  sortBy?: string;
  mode?: SearchMode;
  textWeight?: number;
  semanticWeight?: number;
  limit?: number;
  page?: number;
};

export type SearchMode = "frequency" | "tfidf" | "bm25" | "semantic" | "hybrid";

export type SearchResult = {
  id: number;
  documentId?: number;
  title: string;
  snippet: string;
  category: string;
  type: string;
  documentType: string;
  author: string;
  fileName: string;
  mimeType: string;
  size: string;
  date: string;
  relevance: number;
  textualScore?: number;
  semanticScore?: number;
  finalScore?: number;
  searchMode?: SearchMode | string;
  matchedTerms?: string[];
};

export type SearchResponse = {
  searchId: number | null;
  query: string;
  mode?: SearchMode | string;
  searchMode?: SearchMode | string;
  total: number;
  page: number;
  perPage: number;
  totalPages: number;
  responseTimeMs: number;
  items: SearchResult[];
  results?: SearchResult[];
};

export type RelevanceFeedbackPayload = {
  searchId: number;
  documentId: number;
  rating: number;
  comment?: string;
};

export type RelevanceFeedback = {
  id: number;
  searchId: number;
  documentId: number;
  rating: number;
  comment?: string | null;
  createdAt: string;
};

export type SearchHistoryItem = {
  id: number;
  term: string;
};

export type SearchHistoryFilters = {
  query?: string;
  performedFrom?: string;
  performedTo?: string;
  limit?: number;
  page?: number;
};

export type SearchHistoryAppliedFilters = {
  category?: string | null;
  documentType?: string | null;
  author?: string | null;
  dateFrom?: string | null;
  dateTo?: string | null;
  sortBy?: string | null;
};

export type SearchHistoryEntry = {
  id: number;
  query: string;
  createdAt: string;
  resultCount: number;
  responseTimeMs: number;
  user: string;
  filters: SearchHistoryAppliedFilters;
};

export type SearchHistoryResponse = {
  total: number;
  page: number;
  perPage: number;
  totalPages: number;
  items: SearchHistoryEntry[];
};

export type DocumentDetails = {
  id: number;
  title: string;
  displayTitle?: string;
  fileName: string;
  category: string;
  type: string;
  documentType: string;
  date: string;
  author: string;
  uploadedBy: string;
  format: string;
  mimeType: string;
  pages: number;
  version: number;
  indexedAt: string;
  sizeBytes: number;
  size: string;
  hash: string;
  downloadUrl?: string | null;
  content: string;
  formattedContent?: string;
  extractedCharacters: number;
};

export type DocumentVersion = {
  version: number;
  createdAt: string;
  active: boolean;
};

export type IngestionBatchFile = {
  name: string;
  size: string;
  status: "validated" | "indexed" | "error";
};

export type IngestionHistoryEntry = {
  date: string;
  file: string;
  type: string;
  result: string;
  details: string;
};

export type DocumentUploadPayload = {
  file: File;
  category: string;
  documentDate?: string;
  title?: string;
  author?: string;
  documentType?: string;
};

export type DocumentVersionUploadPayload = Omit<DocumentUploadPayload, "category"> & {
  category?: string;
};

export type BatchUploadPayload = {
  files: File[];
  category: string;
  documentDate?: string;
  author?: string;
  documentType?: string;
};

export type UploadedDocument = {
  id: number;
  title: string;
  fileName: string;
  category: string;
  type: string;
  documentType: string;
  author: string;
  mimeType: string;
  sizeBytes: number;
  sizeLabel: string;
  date: string | null;
  uploadedAt: string;
  validated: boolean;
  integrityOk: boolean;
  hash: string;
  extracted: boolean;
  extractedCharacters: number;
};

export type BatchUploadItem = {
  fileName: string;
  status: "indexed" | "error";
  message: string;
  documentId?: number | null;
  extractedCharacters: number;
  sizeLabel?: string | null;
};

export type BatchUploadResult = {
  totalFiles: number;
  successCount: number;
  failureCount: number;
  items: BatchUploadItem[];
};

export type IndexLogEntry = {
  time: string;
  message: string;
  type: "info" | "success" | "error";
};

export type IndexStatusSnapshot = {
  indexedDocuments: number;
  averageTime: string;
  successRate: string;
  errors: number;
  integrityOk: boolean;
  inconsistencyCount: number;
  currentProgress: number;
  remainingEstimate: string;
  summary: {
    completed: number;
    processing: number;
    failed: number;
  };
  consistency: {
    documentsWithoutActiveVersion: number;
    documentsWithoutIndex: number;
    orphanIndexEntries: number;
    staleTerms: number;
  };
  metrics: {
    activeDocuments: number;
    activeVersions: number;
    totalTerms: number;
    totalPostings: number;
    averageTermsPerDocument: string;
    lastIndexedAt?: string | null;
  };
  logs: IndexLogEntry[];
};

export type ReindexResult = {
  processedDocuments: number;
  successCount: number;
  failureCount: number;
  message: string;
};

export type MetricsOverview = {
  totalQueries: number;
  averageSearchTime: string;
  indexedDocuments: number;
  successRate: string;
  averageResults: string;
  queriesToday: number;
  queriesWithoutResults: number;
  zeroResultsRate: string;
};

export type MetricsPoint = {
  day: string;
  consultas: number;
};

export type NamedValue = {
  name: string;
  value: number;
};

export type MetricsSnapshot = {
  overview: MetricsOverview;
  queriesByDay: MetricsPoint[];
  topTerms: NamedValue[];
  documentsByCategory: NamedValue[];
  queryOutcomeDistribution: NamedValue[];
  recentCalculations: MetricCalculation[];
};

export type MetricCalculation = {
  id: number;
  periodStart: string;
  periodEnd: string;
  totalQueries: number;
  averageResponseTimeMs: number;
  averageResults: string;
  queriesWithoutResults: number;
  calculatedAt: string;
};

export type FrequentQueryMetric = {
  query: string;
  count: number;
  averageResponseTimeMs: number;
  averageResults: string;
};

export type AccessedDocumentMetric = {
  id: number;
  title: string;
  category: string;
  accessCount: number;
  viewCount: number;
  downloadCount: number;
  exportCount: number;
  lastAccessedAt?: string | null;
};

export type MetricsReportFilters = {
  dateFrom?: string;
  dateTo?: string;
};

export type MetricsReportSummary = {
  periodStart: string;
  periodEnd: string;
  totalQueries: number;
  uniqueQueries: number;
  averageResponseTimeMs: number;
  averageResults: string;
  queriesWithoutResults: number;
  zeroResultsRate: string;
  indexedDocuments: number;
  mostFrequentQuery?: string | null;
  mostAccessedDocument?: string | null;
};

export type MetricsReport = {
  summary: MetricsReportSummary;
  frequentQueries: FrequentQueryMetric[];
  zeroResultQueries: FrequentQueryMetric[];
  topTerms: NamedValue[];
  accessedDocuments: AccessedDocumentMetric[];
  storedCalculation?: MetricCalculation | null;
};

export type HistoryEntry = {
  date: string;
  user: string;
  action: string;
  details: string;
  status: "success" | "error" | "info" | "warning";
};

export type AdministrativeHistoryFilters = {
  userId?: number;
  dateFrom?: string;
  dateTo?: string;
  limit?: number;
};

export type NotificationType = "info" | "success" | "warning" | "error";

export type AppNotification = {
  id: number;
  userId: number;
  title: string;
  message: string;
  type: NotificationType;
  origin: string;
  read: boolean;
  createdAt: string;
  readAt?: string | null;
};

export type AppSettings = {
  instanceName: string;
  apiBaseUrl: string;
  autoIndexing: boolean;
  ocrEnabled: boolean;
  maxFileSizeMb: number;
  emailNotifications: boolean;
  weeklyReport: boolean;
};
