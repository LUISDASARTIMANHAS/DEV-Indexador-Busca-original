import type {
  AccessedDocumentMetric,
  AppSettings,
  DocumentDetails,
  HistoryEntry,
  IndexStatusSnapshot,
  IngestionBatchFile,
  IngestionHistoryEntry,
  MetricCalculation,
  MetricsReport,
  MetricsSnapshot,
  AppNotification,
  SearchHistoryEntry,
  SearchHistoryFilters,
  SearchHistoryResponse,
  SearchHistoryItem,
  SearchResponse,
  SearchResult,
  SessionUser,
  UserSummary,
} from "@/types/app";
const stripHtml = (input: string): string =>
  input.replace(/<[^>]+>/g, "");

const normalizeMockText = (input: string): string =>
  input
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();

export const mockUsers: UserSummary[] = [
  { id: 1, name: "Carlos Silva", login: "admin", email: "admin@ifes.edu.br", role: "Administrador", active: true },
  { id: 2, name: "João Oliveira", login: "joao.oliveira", email: "joao.oliveira@ifes.edu.br", role: "Usuário", active: true },
  { id: 3, name: "Ana Costa", login: "ana.costa", email: "ana.costa@ifes.edu.br", role: "Usuário", active: false },
  { id: 4, name: "Pedro Lima", login: "pedro.lima", email: "pedro.lima@ifes.edu.br", role: "Administrador", active: true },
  { id: 5, name: "Maria Santos", login: "maria.santos", email: "maria.santos@ifes.edu.br", role: "Usuário", active: true },
];

export const mockSessionUser: SessionUser = {
  ...mockUsers[0],
  token: "mock-admin-token",
};

const allSearchResults: SearchResult[] = [
  { id: 1, title: "Resolução Normativa nº 45/2025 - Normas Acadêmicas", snippet: "Estabelece as normas para o funcionamento dos cursos de graduação, incluindo <mark>resolução</mark> sobre matrículas e avaliações...", category: "Acadêmico", type: "PDF", documentType: "Resolução", author: "Conselho Superior", fileName: "resolucao_normativa_45_2025.pdf", mimeType: "application/pdf", size: "2.4 MB", date: "2025-08-12", relevance: 95 },
  { id: 2, title: "Edital de Seleção 012/2025 - Programa de Monitoria", snippet: "O Instituto Federal do Espírito Santo torna público o <mark>edital</mark> para seleção de monitores para o semestre 2025/2...", category: "Acadêmico", type: "PDF", documentType: "Edital", author: "Diretoria de Ensino", fileName: "edital_monitoria_012_2025.pdf", mimeType: "application/pdf", size: "1.1 MB", date: "2025-07-28", relevance: 88 },
  { id: 3, title: "Relatório de Gestão 2024 - Campus Serra", snippet: "Apresenta os resultados alcançados no exercício de 2024, contemplando indicadores de <mark>gestão</mark> acadêmica e administrativa...", category: "Administrativo", type: "PDF", documentType: "Relatório", author: "Campus Serra", fileName: "relatorio_gestao_2024.pdf", mimeType: "application/pdf", size: "3.8 MB", date: "2025-03-15", relevance: 76 },
  { id: 4, title: "Plano de Desenvolvimento Institucional 2024-2028", snippet: "Define as diretrizes estratégicas e metas institucionais para o quinquênio, abordando <mark>plano</mark> de expansão e qualidade...", category: "Administrativo", type: "PDF", documentType: "Plano", author: "Reitoria", fileName: "pdi_2024_2028.pdf", mimeType: "application/pdf", size: "4.2 MB", date: "2024-12-10", relevance: 72 },
  { id: 5, title: "Portaria nº 234/2025 - Comissão de Avaliação", snippet: "Designa os membros da comissão responsável pela avaliação institucional do período letivo 2025/1...", category: "Administrativo", type: "TXT", documentType: "Portaria", author: "Direção Geral", fileName: "portaria_234_2025.txt", mimeType: "text/plain", size: "46 KB", date: "2025-06-01", relevance: 64 },
];

export const mockRecentSearches: SearchHistoryItem[] = [
  { id: 1, term: "resolução normativa" },
  { id: 2, term: "edital 2025" },
  { id: 3, term: "relatório gestão" },
  { id: 4, term: "plano pedagógico" },
];

const mockSearchHistoryEntries: SearchHistoryEntry[] = [
  {
    id: 101,
    query: "resolução normativa",
    createdAt: "2025-08-12T14:30:00",
    resultCount: 5,
    responseTimeMs: 182,
    user: "admin@ifes.edu.br",
    filters: {
      category: "Acadêmico",
      documentType: "Resolução",
      author: "Conselho Superior",
      dateFrom: "2025-01-01",
      dateTo: "2025-12-31",
      sortBy: "relevancia",
    },
  },
  {
    id: 102,
    query: "edital 2025",
    createdAt: "2025-08-12T13:12:00",
    resultCount: 3,
    responseTimeMs: 141,
    user: "admin@ifes.edu.br",
    filters: {
      category: "Acadêmico",
      documentType: "Edital",
      author: null,
      dateFrom: null,
      dateTo: null,
      sortBy: "data-desc",
    },
  },
  {
    id: 103,
    query: "relatório gestão",
    createdAt: "2025-08-11T16:10:00",
    resultCount: 2,
    responseTimeMs: 117,
    user: "admin@ifes.edu.br",
    filters: {
      category: "Administrativo",
      documentType: "Relatório",
      author: "Campus Serra",
      dateFrom: "2024-01-01",
      dateTo: null,
      sortBy: "titulo",
    },
  },
  {
    id: 104,
    query: "plano pedagógico",
    createdAt: "2025-08-10T09:45:00",
    resultCount: 1,
    responseTimeMs: 98,
    user: "admin@ifes.edu.br",
    filters: {
      category: null,
      documentType: "Plano",
      author: null,
      dateFrom: null,
      dateTo: null,
      sortBy: "relevancia",
    },
  },
];

export const mockSearch = (
  query: string,
  page = 1,
  perPage = 20,
  filters: {
    category?: string;
    documentType?: string;
    author?: string;
    dateFrom?: string;
    dateTo?: string;
  } = {},
): SearchResponse => {
  const normalized = normalizeMockText(query.trim());
  const filtered = normalized === "xyz123"
    ? []
    : allSearchResults.filter((result) => {
        if (filters.category && normalizeMockText(result.category) !== normalizeMockText(filters.category)) {
          return false;
        }
        if (filters.documentType) {
          const documentTypeMatches = normalizeMockText(result.documentType) === normalizeMockText(filters.documentType);
          const fileTypeMatches = normalizeMockText(result.type) === normalizeMockText(filters.documentType);
          if (!documentTypeMatches && !fileTypeMatches) {
            return false;
          }
        }
        if (filters.author && normalizeMockText(result.author) !== normalizeMockText(filters.author)) {
          return false;
        }
        if (filters.dateFrom && result.date < filters.dateFrom) {
          return false;
        }
        if (filters.dateTo && result.date > filters.dateTo) {
          return false;
        }
        if (!normalized) {
          return true;
        }

        return [
          result.title,
          stripHtml(result.snippet),
          result.category,
          result.documentType,
          result.author,
          result.fileName,
        ].some((text) => normalizeMockText(text).includes(normalized));
      });

  const total = filtered.length;
  const totalPages = Math.max(1, Math.ceil(total / perPage));
  const safePage = Math.min(Math.max(page, 1), totalPages);
  const start = (safePage - 1) * perPage;

  return {
    query,
    total,
    page: safePage,
    perPage,
    totalPages,
    responseTimeMs: 150 + Math.floor(Math.random() * 100),
    items: filtered.slice(start, start + perPage),
  };
};

export const mockSearchHistory = (
  filters: SearchHistoryFilters = {},
): SearchHistoryResponse => {
  const filtered = mockSearchHistoryEntries.filter((entry) => {
    if (
      filters.query &&
      !normalizeMockText(entry.query).includes(normalizeMockText(filters.query))
    ) {
      return false;
    }
    if (filters.performedFrom && entry.createdAt.slice(0, 10) < filters.performedFrom) {
      return false;
    }
    if (filters.performedTo && entry.createdAt.slice(0, 10) > filters.performedTo) {
      return false;
    }
    return true;
  });

  const perPage = filters.limit ?? 10;
  const total = filtered.length;
  const totalPages = Math.max(1, Math.ceil(total / perPage));
  const safePage = Math.min(Math.max(filters.page ?? 1, 1), totalPages);
  const start = (safePage - 1) * perPage;

  return {
    total,
    page: safePage,
    perPage,
    totalPages,
    items: filtered.slice(start, start + perPage),
  };
};

export const mockDocuments: DocumentDetails[] = [
  {
    id: 1,
    title: "Resolução Normativa nº 45/2025 - Normas Acadêmicas",
    fileName: "resolucao_normativa_45_2025.pdf",
    category: "Acadêmico",
    type: "PDF",
    documentType: "Resolução",
    date: "2025-08-12",
    author: "Conselho Superior",
    uploadedBy: "Administrador",
    format: "PDF",
    mimeType: "application/pdf",
    pages: 12,
    version: 2,
    indexedAt: "2025-08-12 14:32",
    sizeBytes: 2516582,
    size: "2.4 MB",
    hash: "mock-sha256",
    downloadUrl: "#",
    extractedCharacters: 2340,
    content: `Art. 1º Esta Resolução estabelece as normas gerais para o funcionamento dos cursos de graduação do Instituto Federal do Espírito Santo - IFES.

Art. 2º A organização didático-pedagógica dos cursos de graduação observará os seguintes princípios:
I - flexibilidade curricular e interdisciplinaridade;
II - articulação entre ensino, pesquisa e extensão;
III - incentivo à inovação e ao empreendedorismo;
IV - valorização da diversidade e da inclusão social.

Art. 3º O ingresso nos cursos de graduação dar-se-á por meio de processo seletivo, conforme edital específico publicado pela instituição.

Parágrafo único. Poderão ser utilizados como forma de ingresso:
a) Sistema de Seleção Unificada (SiSU);
b) Vestibular próprio;
c) Transferência externa;
d) Portador de diploma de graduação.

Art. 4º A matrícula será realizada semestralmente, conforme calendário acadêmico aprovado pelo Conselho de Ensino.

§1º O discente que não efetuar a matrícula no prazo estabelecido terá seu vínculo com a instituição cancelado.

§2º É assegurado ao discente o direito de trancamento de matrícula por até 2 (dois) semestres consecutivos ou 4 (quatro) alternados.

Art. 5º A avaliação da aprendizagem será processual, contínua e cumulativa, prevalecendo os aspectos qualitativos sobre os quantitativos.`,
  },
];

export const mockBatchFiles: IngestionBatchFile[] = [
  { name: "relatorio_2025.pdf", size: "2.4 MB", status: "indexed" },
  { name: "edital_monitoria.pdf", size: "1.1 MB", status: "validated" },
  { name: "ata_reuniao.txt", size: "45 KB", status: "indexed" },
  { name: "planilha_notas.csv", size: "320 KB", status: "error" },
  { name: "portaria_032.pdf", size: "890 KB", status: "validated" },
];

export const mockIngestionHistory: IngestionHistoryEntry[] = [
  { date: "2025-08-12 14:32", file: "resolucao_45_2025.pdf", type: "Individual", result: "Sucesso", details: "Validado → Extraído → Indexado" },
  { date: "2025-08-12 14:30", file: "edital_monitoria.pdf", type: "Individual", result: "Sucesso", details: "Validado → Extraído → Indexado" },
  { date: "2025-08-11 16:42", file: "planilha_notas.csv", type: "Lote", result: "Falha", details: "Validação falhou: formato incompatível" },
  { date: "2025-08-11 16:40", file: "ata_reuniao.txt", type: "Lote", result: "Sucesso", details: "Validado → Extraído → Indexado" },
  { date: "2025-08-10 09:15", file: "portaria_032.pdf", type: "Individual", result: "Sucesso", details: "Validado → Extraído → Indexado" },
];

export const mockIndexStatus: IndexStatusSnapshot = {
  indexedDocuments: 1247,
  averageTime: "2.4s",
  successRate: "96.2%",
  errors: 3,
  currentProgress: 73,
  remainingEstimate: "12 segundos restantes",
  summary: {
    completed: 2,
    processing: 0,
    failed: 1,
  },
  logs: [
    { time: "14:32:01", message: "Iniciando indexação de 3 documentos...", type: "info" },
    { time: "14:32:03", message: "resolucao_45_2025.pdf — Extraindo texto (UC12)...", type: "info" },
    { time: "14:32:05", message: "resolucao_45_2025.pdf — Pré-processamento textual (UC15)...", type: "info" },
    { time: "14:32:08", message: "resolucao_45_2025.pdf — Tokenização concluída (2.340 tokens)", type: "success" },
    { time: "14:32:08", message: "resolucao_45_2025.pdf — Construção de índice invertido (UC16)", type: "success" },
    { time: "14:32:09", message: "edital_monitoria.pdf — Extraindo texto...", type: "info" },
    { time: "14:32:14", message: "edital_monitoria.pdf — Tokenização concluída (1.120 tokens)", type: "success" },
    { time: "14:32:14", message: "edital_monitoria.pdf — Índice atualizado incrementalmente (UC17)", type: "success" },
    { time: "14:32:15", message: "planilha_notas.csv — Formato incompatível com parser", type: "error" },
    { time: "14:32:15", message: "planilha_notas.csv — Documento registrado como inválido (UC11)", type: "error" },
    { time: "14:32:16", message: "Verificação de consistência documento-índice (UC18)...", type: "info" },
    { time: "14:32:17", message: "Indexação finalizada: 2 sucesso, 1 falha · Tempo total: 16s (UC19)", type: "info" },
  ],
};

export const mockMetrics: MetricsSnapshot = {
  overview: {
    totalQueries: 1893,
    averageSearchTime: "0.34s",
    indexedDocuments: 1247,
    successRate: "96.2%",
    averageResults: "8.3",
    queriesToday: 289,
    queriesWithoutResults: 214,
    zeroResultsRate: "11.3%",
  },
  queriesByDay: [
    { day: "Seg", consultas: 42 },
    { day: "Ter", consultas: 58 },
    { day: "Qua", consultas: 35 },
    { day: "Qui", consultas: 71 },
    { day: "Sex", consultas: 63 },
    { day: "Sáb", consultas: 12 },
    { day: "Dom", consultas: 8 },
  ],
  topTerms: [
    { name: "resolução", value: 124 },
    { name: "edital", value: 98 },
    { name: "relatório", value: 76 },
    { name: "plano pedagógico", value: 54 },
    { name: "portaria", value: 41 },
  ],
  documentsByCategory: [
    { name: "Acadêmico", value: 520 },
    { name: "Administrativo", value: 380 },
    { name: "Pesquisa", value: 210 },
    { name: "Extensão", value: 137 },
  ],
  queryOutcomeDistribution: [
    { name: "Com resultados", value: 1679 },
    { name: "Sem resultados", value: 214 },
  ],
  recentCalculations: [
    {
      id: 41,
      periodStart: "2026-05-01T00:00:00",
      periodEnd: "2026-05-18T23:59:59",
      totalQueries: 1893,
      averageResponseTimeMs: 340,
      averageResults: "8.3",
      queriesWithoutResults: 214,
      calculatedAt: "2026-05-18T10:30:00",
    },
    {
      id: 40,
      periodStart: "2026-04-01T00:00:00",
      periodEnd: "2026-04-30T23:59:59",
      totalQueries: 1627,
      averageResponseTimeMs: 362,
      averageResults: "7.9",
      queriesWithoutResults: 201,
      calculatedAt: "2026-05-01T08:00:00",
    },
  ],
};

export const mockMetricCalculations: MetricCalculation[] = [
  ...mockMetrics.recentCalculations,
  {
    id: 39,
    periodStart: "2026-03-01T00:00:00",
    periodEnd: "2026-03-31T23:59:59",
    totalQueries: 1410,
    averageResponseTimeMs: 389,
    averageResults: "7.4",
    queriesWithoutResults: 188,
    calculatedAt: "2026-04-01T08:00:00",
  },
];

export const mockAccessedDocuments: AccessedDocumentMetric[] = [
  {
    id: 1,
    title: "Resolução Normativa nº 45/2025 - Normas Acadêmicas",
    category: "Acadêmico",
    accessCount: 82,
    viewCount: 61,
    downloadCount: 14,
    exportCount: 7,
    lastAccessedAt: "2026-05-18T09:32:00",
  },
  {
    id: 2,
    title: "Edital de Seleção 012/2025 - Programa de Monitoria",
    category: "Acadêmico",
    accessCount: 64,
    viewCount: 48,
    downloadCount: 10,
    exportCount: 6,
    lastAccessedAt: "2026-05-18T08:12:00",
  },
  {
    id: 3,
    title: "Relatório de Gestão 2024 - Campus Serra",
    category: "Administrativo",
    accessCount: 39,
    viewCount: 30,
    downloadCount: 5,
    exportCount: 4,
    lastAccessedAt: "2026-05-17T17:42:00",
  },
];

export const mockMetricsReport: MetricsReport = {
  summary: {
    periodStart: "2026-05-01T00:00:00",
    periodEnd: "2026-05-18T23:59:59",
    totalQueries: 1893,
    uniqueQueries: 732,
    averageResponseTimeMs: 340,
    averageResults: "8.3",
    queriesWithoutResults: 214,
    zeroResultsRate: "11.3%",
    indexedDocuments: 1247,
    mostFrequentQuery: "resolução normativa",
    mostAccessedDocument: "Resolução Normativa nº 45/2025 - Normas Acadêmicas",
  },
  frequentQueries: [
    { query: "resolução normativa", count: 96, averageResponseTimeMs: 284, averageResults: "6.2" },
    { query: "edital 2025", count: 73, averageResponseTimeMs: 251, averageResults: "5.4" },
    { query: "relatório gestão", count: 52, averageResponseTimeMs: 308, averageResults: "4.1" },
    { query: "portaria interna", count: 41, averageResponseTimeMs: 222, averageResults: "7.0" },
  ],
  zeroResultQueries: [
    { query: "normativa estagio doutorado", count: 16, averageResponseTimeMs: 401, averageResults: "0.0" },
    { query: "processo seletivo biblioteca 2022", count: 11, averageResponseTimeMs: 365, averageResults: "0.0" },
    { query: "manual laboratorio agroindustria", count: 9, averageResponseTimeMs: 348, averageResults: "0.0" },
  ],
  topTerms: [
    { name: "resolução", value: 124 },
    { name: "edital", value: 98 },
    { name: "relatório", value: 76 },
    { name: "portaria", value: 41 },
  ],
  accessedDocuments: mockAccessedDocuments,
  storedCalculation: mockMetricCalculations[0],
};

export const mockHistory: HistoryEntry[] = [
  { date: "2025-08-12 14:32", user: "admin@ifes.edu.br", action: "Indexação", details: "resolucao_45_2025.pdf indexado com sucesso", status: "success" },
  { date: "2025-08-12 14:30", user: "joao.oliveira@ifes.edu.br", action: "Busca", details: 'Consulta: "resolução normativa" — 5 resultados', status: "info" },
  { date: "2025-08-12 13:15", user: "admin@ifes.edu.br", action: "Ingestão", details: "Upload de edital_monitoria.pdf (1.1 MB)", status: "success" },
  { date: "2025-08-11 16:42", user: "admin@ifes.edu.br", action: "Falha de Indexação", details: "planilha_notas.csv — falha na indexação (UC11)", status: "error" },
  { date: "2025-08-11 10:20", user: "maria.santos@ifes.edu.br", action: "Busca", details: 'Consulta: "edital 2025" — 3 resultados', status: "info" },
  { date: "2025-08-10 09:05", user: "admin@ifes.edu.br", action: "Criação de Usuário", details: "Novo usuário maria.santos@ifes.edu.br criado (UC01)", status: "success" },
  { date: "2025-08-10 09:04", user: "admin@ifes.edu.br", action: "Ação Administrativa", details: "Perfil de pedro.lima alterado para Administrador (UC03)", status: "success" },
  { date: "2025-08-09 17:30", user: "admin@ifes.edu.br", action: "Ingestão", details: "Upload em lote: 5 arquivos processados (UC09)", status: "success" },
  { date: "2025-08-09 11:00", user: "admin@ifes.edu.br", action: "Ação Administrativa", details: "Usuário ana.costa inativado (UC05)", status: "warning" },
  { date: "2025-08-08 15:20", user: "admin@ifes.edu.br", action: "Reindexação", details: "Documento portaria_032.pdf reindexado (UC13)", status: "success" },
];

export const mockNotifications: AppNotification[] = [
  {
    id: 1,
    userId: 1,
    title: "Notificações ativas",
    message: "O serviço de notificações do IFESDOC está em execução.",
    type: "success",
    origin: "ifesdoc-worker",
    read: false,
    createdAt: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    readAt: null,
  },
  {
    id: 2,
    userId: 1,
    title: "Documento rejeitado",
    message: "planilha_notas.csv: formato incompatível com o processo de indexação.",
    type: "warning",
    origin: "ifesdoc-worker",
    read: false,
    createdAt: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
    readAt: null,
  },
  {
    id: 3,
    userId: 1,
    title: "Reindexação concluída",
    message: "A base de documentos foi reindexada com sucesso.",
    type: "info",
    origin: "admin:admin@ifes.edu.br",
    read: true,
    createdAt: new Date(Date.now() - 1000 * 60 * 90).toISOString(),
    readAt: new Date(Date.now() - 1000 * 60 * 80).toISOString(),
  },
];

export const defaultSettings: AppSettings = {
  instanceName: "IFESDOC - Campus Serra",
  apiBaseUrl: "http://localhost:8000",
  autoIndexing: true,
  ocrEnabled: true,
  maxFileSizeMb: 50,
  emailNotifications: true,
  weeklyReport: false,
};
