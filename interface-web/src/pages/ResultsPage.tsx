import { useMemo } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { ArrowLeft, FileText, Calendar, Tag, Eye, Download, SearchX, ChevronLeft, ChevronRight, FileJson, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { PageError, PageLoader } from "@/components/PageState";
import { useSearchResults } from "@/hooks/use-app-query";
import type { SearchResult } from "@/types/app";

const csvEscape = (value: string | number) => `"${String(value).replace(/"/g, '""')}"`;

const stripHtml = (value: string) => value.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();

const formatSortLabel = (value: string) => {
  switch (value) {
    case "data-desc":
      return "Data mais recente";
    case "data-asc":
      return "Data mais antiga";
    case "titulo":
      return "Título (A-Z)";
    default:
      return value;
  }
};

const saveBlob = (content: string, filename: string, type: string) => {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const anchor = window.document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  window.document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
};

const buildResultsCsv = (items: SearchResult[]) => {
  const header = ["id", "titulo", "autor", "arquivo", "categoria", "tipo", "formato", "tamanho", "data", "relevancia", "trecho"];
  const rows = items.map((item) => [
    item.id,
    item.title,
    item.author,
    item.fileName,
    item.category,
    item.documentType,
    item.type,
    item.size,
    item.date,
    item.relevance,
    stripHtml(item.snippet),
  ]);

  return [header, ...rows].map((row) => row.map(csvEscape).join(",")).join("\n");
};

const getPageNumbers = (current: number, total: number) => {
  const window = 2;
  const pages: (number | string)[] = [];
  for (let i = 1; i <= total; i++) {
    if (i === 1 || i === total || (i >= current - window && i <= current + window)) {
      pages.push(i);
    } else if (i === current - window - 1 || i === current + window + 1) {
      pages.push("...");
    }
  }
  return pages.filter((v, i, a) => a.indexOf(v) === i);
};

const ResultsPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const query = searchParams.get("q") || "";
  const currentPage = Number(searchParams.get("page") || "1");
  const filters = useMemo(() => ({
    page: currentPage,
    limit: Number(searchParams.get("limit") || "20"),
    category: searchParams.get("category") || undefined,
    documentType: searchParams.get("documentType") || undefined,
    author: searchParams.get("author") || undefined,
    dateFrom: searchParams.get("dateFrom") || undefined,
    dateTo: searchParams.get("dateTo") || undefined,
    sortBy: searchParams.get("sortBy") || undefined,
  }), [currentPage, searchParams]);
  const { data, isLoading, isError, refetch } = useSearchResults(query, filters);

  const totalPages = data?.totalPages || 1;
  const hasResults = !!data && data.items.length > 0;

  const goToPage = (page: number) => {
    const next = new URLSearchParams(searchParams);
    next.set("page", String(page));
    setSearchParams(next);
  };

  const exportCsv = () => {
    if (!data) {
      return;
    }
    saveBlob(
      buildResultsCsv(data.items),
      `resultados-${query || "busca"}.csv`,
      "text/csv;charset=utf-8",
    );
  };

  const exportJson = () => {
    if (!data) {
      return;
    }
    saveBlob(
      JSON.stringify(data, null, 2),
      `resultados-${query || "busca"}.json`,
      "application/json;charset=utf-8",
    );
  };

  const openDocument = (id: number) => {
    navigate(`/documento/${id}`, {
      state: {
        resultIds: data?.items.map((item) => item.id) || [],
        query,
        from: `${location.search}`,
      },
    });
  };

  if (!query.trim()) {
    return <PageError title="Informe uma consulta para visualizar resultados." onRetry={() => navigate("/busca")} />;
  }

  if (isLoading) {
    return <PageLoader label="Consultando documentos..." />;
  }

  if (isError || !data) {
    return <PageError title="Falha ao carregar resultados da busca." onRetry={() => refetch()} />;
  }

  return (
    <div className="max-w-4xl mx-auto animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => navigate("/busca")}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-xl font-semibold text-foreground">Resultados da busca</h1>
            <p className="text-sm text-muted-foreground">
              {hasResults ? (
                <>{data.total} documentos encontrados para "<span className="font-medium text-foreground">{query}</span>" ({data.responseTimeMs}ms)</>
              ) : (
                <>Nenhum resultado para "<span className="font-medium text-foreground">{query}</span>" ({data.responseTimeMs}ms)</>
              )}
            </p>
            {(filters.category || filters.documentType || filters.author || filters.dateFrom || filters.dateTo || filters.sortBy) && (
              <div className="flex flex-wrap gap-2 mt-3">
                {filters.category && <Badge variant="secondary">Categoria: {filters.category}</Badge>}
                {filters.documentType && <Badge variant="secondary">Tipo/Formato: {filters.documentType}</Badge>}
                {filters.author && <Badge variant="secondary">Autor: {filters.author}</Badge>}
                {filters.dateFrom && <Badge variant="outline">Publicado após: {filters.dateFrom}</Badge>}
                {filters.dateTo && <Badge variant="outline">Publicado até: {filters.dateTo}</Badge>}
                {filters.sortBy && filters.sortBy !== "relevancia" && <Badge variant="outline">Ordenação: {formatSortLabel(filters.sortBy)}</Badge>}
              </div>
            )}
          </div>
        </div>
        {hasResults && (
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="gap-1.5" onClick={exportCsv}>
              <Download className="h-3.5 w-3.5" />
              CSV
            </Button>
            <Button variant="outline" size="sm" className="gap-1.5" onClick={exportJson}>
              <FileJson className="h-3.5 w-3.5" />
              JSON
            </Button>
          </div>
        )}
      </div>

      {!hasResults ? (
        <div className="glass-card p-12 text-center">
          <SearchX className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
          <h2 className="text-lg font-semibold text-foreground mb-2">Nenhuma correspondência encontrada</h2>
          <p className="text-sm text-muted-foreground max-w-md mx-auto mb-4">
            Sua consulta não retornou resultados. Tente refinar os termos de busca ou utilize filtros diferentes.
          </p>
          <Button variant="outline" onClick={() => navigate("/busca")}>
            Nova Busca
          </Button>
        </div>
      ) : (
        <>
          <div className="space-y-3">
            {data.items.map((doc) => (
              <div key={doc.id} className="glass-card p-5 hover:shadow-md transition-all duration-200">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1.5">
                      <FileText className="h-4 w-4 text-primary shrink-0" />
                      <h3 className="font-semibold text-foreground truncate">{doc.title}</h3>
                    </div>
                    <p
                      className="text-sm text-muted-foreground line-clamp-2 mb-3 [&_mark]:highlight-term [&_mark]:bg-transparent"
                      dangerouslySetInnerHTML={{ __html: doc.snippet }}
                    />
                    <div className="flex items-center gap-3 text-xs text-muted-foreground flex-wrap">
                      <span className="flex items-center gap-1">
                        <Tag className="h-3 w-3" />
                        <Badge variant="secondary" className="text-xs px-2 py-0">{doc.category}</Badge>
                      </span>
                      <Badge variant="outline" className="text-xs px-2 py-0">{doc.type}</Badge>
                      <span className="flex items-center gap-1">
                        <FileText className="h-3 w-3" />
                        {doc.documentType} · {doc.size}
                      </span>
                      <span className="flex items-center gap-1">
                        <User className="h-3 w-3" />
                        {doc.author}
                      </span>
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {new Date(doc.date).toLocaleDateString("pt-BR")}
                      </span>
                      <span className="flex items-center gap-1.5">
                        Relevância
                        <Progress value={doc.relevance} className="w-16 h-1.5" />
                        <span className="font-medium text-foreground">{doc.relevance}%</span>
                      </span>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => openDocument(doc.id)}
                    className="shrink-0 gap-1.5"
                  >
                    <Eye className="h-3.5 w-3.5" />
                    Visualizar
                  </Button>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-center gap-2 mt-6">
            <Button
              variant="outline"
              size="sm"
              disabled={currentPage === 1}
              onClick={() => goToPage(currentPage - 1)}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            {getPageNumbers(currentPage, totalPages).map((page, index) =>
              page === "..." ? (
                <span key={`dots-${index}`} className="px-2 text-muted-foreground">
                  ...
                </span>
              ) : (
                <Button
                  key={page}
                  variant={page === currentPage ? "default" : "outline"}
                  size="sm"
                  className="w-9"
                  onClick={() => goToPage(page as number)}
                >
                  {page}
                </Button>
              ),
            )}
            <Button
              variant="outline"
              size="sm"
              disabled={currentPage === totalPages}
              onClick={() => goToPage(currentPage + 1)}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </>
      )}
    </div>
  );
};

export default ResultsPage;
