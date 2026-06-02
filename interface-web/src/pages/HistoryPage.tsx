import { useState } from "react";
import { ChevronLeft, ChevronRight, Download } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useHistory, useSearchHistory } from "@/hooks/use-app-query";
import { PageError, PageLoader } from "@/components/PageState";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type {
  AdministrativeHistoryFilters,
  HistoryEntry,
  SearchHistoryAppliedFilters,
  SearchHistoryEntry,
  SearchHistoryFilters,
} from "@/types/app";

const statusVariant: Record<string, "default" | "destructive" | "secondary"> = {
  success: "default",
  error: "destructive",
  info: "secondary",
  warning: "secondary",
};

const statusColors: Record<string, string> = {
  success: "bg-success hover:bg-success/90",
  warning: "bg-warning hover:bg-warning/90 text-warning-foreground",
};

const csvEscape = (value: string | number) =>
  `"${String(value).replace(/"/g, '""')}"`;

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

const formatDateTime = (value: string) => {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString("pt-BR");
};

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

const formatAppliedFilters = (filters: SearchHistoryAppliedFilters) => {
  const labels: string[] = [];
  if (filters.category) {
    labels.push(`Categoria: ${filters.category}`);
  }
  if (filters.documentType) {
    labels.push(`Tipo/Formato: ${filters.documentType}`);
  }
  if (filters.author) {
    labels.push(`Autor: ${filters.author}`);
  }
  if (filters.dateFrom) {
    labels.push(`Publicação desde ${filters.dateFrom}`);
  }
  if (filters.dateTo) {
    labels.push(`Publicação até ${filters.dateTo}`);
  }
  if (filters.sortBy && filters.sortBy !== "relevancia") {
    labels.push(`Ordenação: ${formatSortLabel(filters.sortBy)}`);
  }
  return labels;
};

const buildHistoryCsv = (items: SearchHistoryEntry[]) => {
  const header = [
    "data",
    "consulta",
    "usuario",
    "resultados",
    "tempo_ms",
    "categoria",
    "tipo_documento",
    "autor",
    "data_publicacao_de",
    "data_publicacao_ate",
    "ordenacao",
  ];
  const rows = items.map((item) => [
    item.createdAt,
    item.query,
    item.user,
    item.resultCount,
    item.responseTimeMs,
    item.filters.category ?? "",
    item.filters.documentType ?? "",
    item.filters.author ?? "",
    item.filters.dateFrom ?? "",
    item.filters.dateTo ?? "",
    item.filters.sortBy ?? "",
  ]);

  return [header, ...rows]
    .map((row) => row.map(csvEscape).join(","))
    .join("\n");
};

const buildAdministrativeHistoryCsv = (items: HistoryEntry[]) => {
  const header = ["data", "usuario", "acao", "detalhes", "status"];
  const rows = items.map((item) => [
    item.date,
    item.user,
    item.action,
    item.details,
    item.status,
  ]);

  return [header, ...rows]
    .map((row) => row.map(csvEscape).join(","))
    .join("\n");
};

const HistoryPage = () => {
  const { isAdmin } = useAuth();
  const [formQuery, setFormQuery] = useState("");
  const [formPerformedFrom, setFormPerformedFrom] = useState("");
  const [formPerformedTo, setFormPerformedTo] = useState("");
  const [filters, setFilters] = useState<SearchHistoryFilters>({
    page: 1,
    limit: 10,
  });
  const [adminUserId, setAdminUserId] = useState("");
  const [adminDateFrom, setAdminDateFrom] = useState("");
  const [adminDateTo, setAdminDateTo] = useState("");
  const [adminFilters, setAdminFilters] = useState<AdministrativeHistoryFilters>({ limit: 100 });
  const { data, isLoading, isError, refetch } = useSearchHistory(filters);
  const adminHistory = useHistory(adminFilters, isAdmin);

  const applyFilters = (event: React.FormEvent) => {
    event.preventDefault();
    setFilters((current) => ({
      ...current,
      page: 1,
      query: formQuery.trim() || undefined,
      performedFrom: formPerformedFrom || undefined,
      performedTo: formPerformedTo || undefined,
    }));
  };

  const clearFilters = () => {
    setFormQuery("");
    setFormPerformedFrom("");
    setFormPerformedTo("");
    setFilters((current) => ({
      page: 1,
      limit: current.limit ?? 10,
    }));
  };

  const goToPage = (page: number) => {
    setFilters((current) => ({
      ...current,
      page,
    }));
  };

  const exportCsv = () => {
    if (!data || data.items.length === 0) {
      return;
    }
    saveBlob(
      buildHistoryCsv(data.items),
      "historico-consultas.csv",
      "text/csv;charset=utf-8",
    );
  };

  const applyAdminFilters = (event: React.FormEvent) => {
    event.preventDefault();
    const parsedUserId = Number(adminUserId);
    setAdminFilters({
      userId: adminUserId && Number.isInteger(parsedUserId) && parsedUserId > 0 ? parsedUserId : undefined,
      dateFrom: adminDateFrom || undefined,
      dateTo: adminDateTo || undefined,
      limit: 100,
    });
  };

  const clearAdminFilters = () => {
    setAdminUserId("");
    setAdminDateFrom("");
    setAdminDateTo("");
    setAdminFilters({ limit: 100 });
  };

  const exportAdminCsv = () => {
    if (!adminHistory.data?.length) {
      return;
    }
    saveBlob(
      buildAdministrativeHistoryCsv(adminHistory.data),
      "auditoria-administrativa.csv",
      "text/csv;charset=utf-8",
    );
  };

  if (isLoading) {
    return <PageLoader label="Carregando histórico de consultas..." />;
  }

  if (isError || !data) {
    return (
      <PageError
        title="Falha ao carregar histórico de consultas."
        onRetry={() => refetch()}
      />
    );
  }

  return (
    <div className="animate-fade-in space-y-8">
      <section>
        <div className="flex items-center justify-between mb-6 gap-4">
          <div>
            <h1 className="text-2xl font-bold text-foreground">
              Histórico de Consultas
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Consultas realizadas, filtros aplicados e desempenho registrado pelo
              IFESDOC.
            </p>
          </div>
          <Button
            variant="outline"
            className="gap-2"
            onClick={exportCsv}
            disabled={data.items.length === 0}
          >
            <Download className="h-4 w-4" />
            Exportar CSV
          </Button>
        </div>

        <form onSubmit={applyFilters} className="glass-card p-4 mb-6 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="space-y-1.5">
              <Label className="text-xs">Consulta</Label>
              <Input
                value={formQuery}
                onChange={(event) => setFormQuery(event.target.value)}
                placeholder='Ex.: "resolução normativa"'
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Realizada de</Label>
              <Input
                type="date"
                value={formPerformedFrom}
                onChange={(event) => setFormPerformedFrom(event.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Realizada até</Label>
              <Input
                type="date"
                value={formPerformedTo}
                onChange={(event) => setFormPerformedTo(event.target.value)}
              />
            </div>
          </div>
          <div className="flex gap-2">
            <Button type="submit">Aplicar filtros</Button>
            <Button type="button" variant="outline" onClick={clearFilters}>
              Limpar
            </Button>
          </div>
        </form>

        {data.items.length === 0 ? (
          <div className="glass-card p-8 text-center text-sm text-muted-foreground">
            Nenhuma consulta encontrada para os filtros informados.
          </div>
        ) : (
          <>
            <div className="glass-card overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border bg-muted/50">
                    <th className="text-left p-3 font-medium text-muted-foreground">
                      Data
                    </th>
                    <th className="text-left p-3 font-medium text-muted-foreground">
                      Consulta
                    </th>
                    <th className="text-left p-3 font-medium text-muted-foreground">
                      Filtros Aplicados
                    </th>
                    <th className="text-left p-3 font-medium text-muted-foreground">
                      Resultados
                    </th>
                    <th className="text-left p-3 font-medium text-muted-foreground">
                      Tempo
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((row) => {
                    const appliedFilters = formatAppliedFilters(row.filters);
                    return (
                      <tr
                        key={row.id}
                        className="border-b border-border last:border-0 hover:bg-muted/30 transition-colors align-top"
                      >
                        <td className="p-3 text-muted-foreground font-mono text-xs whitespace-nowrap">
                          {formatDateTime(row.createdAt)}
                        </td>
                        <td className="p-3 text-foreground font-medium max-w-60">
                          {row.query}
                        </td>
                        <td className="p-3">
                          {appliedFilters.length > 0 ? (
                            <div className="flex flex-wrap gap-2">
                              {appliedFilters.map((label) => (
                                <Badge
                                  key={`${row.id}-${label}`}
                                  variant="outline"
                                >
                                  {label}
                                </Badge>
                              ))}
                            </div>
                          ) : (
                            <span className="text-muted-foreground">
                              Sem filtros adicionais
                            </span>
                          )}
                        </td>
                        <td className="p-3 text-foreground">{row.resultCount}</td>
                        <td className="p-3 text-muted-foreground">
                          {row.responseTimeMs} ms
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="flex items-center justify-between mt-4">
              <p className="text-sm text-muted-foreground">
                {data.total} consulta(s) registrada(s)
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={data.page <= 1}
                  onClick={() => goToPage(data.page - 1)}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="text-sm text-muted-foreground">
                  Página {data.page} de {data.totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={data.page >= data.totalPages}
                  onClick={() => goToPage(data.page + 1)}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </>
        )}
      </section>

      {isAdmin && (
        <section>
          <div className="mb-4 flex flex-wrap items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold text-foreground">
                Auditoria Administrativa
              </h2>
              <p className="text-sm text-muted-foreground mt-1">
                Eventos administrativos mantidos separadamente do histórico de
                buscas.
              </p>
            </div>
            <Button
              variant="outline"
              className="gap-2"
              onClick={exportAdminCsv}
              disabled={!adminHistory.data?.length}
            >
              <Download className="h-4 w-4" />
              Exportar CSV
            </Button>
          </div>

          <form onSubmit={applyAdminFilters} className="glass-card mb-4 space-y-4 p-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="space-y-1.5">
                <Label className="text-xs">ID do usuário</Label>
                <Input
                  type="number"
                  min="1"
                  value={adminUserId}
                  onChange={(event) => setAdminUserId(event.target.value)}
                  placeholder="Ex.: 2"
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Ação realizada de</Label>
                <Input
                  type="date"
                  value={adminDateFrom}
                  onChange={(event) => setAdminDateFrom(event.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Ação realizada até</Label>
                <Input
                  type="date"
                  value={adminDateTo}
                  onChange={(event) => setAdminDateTo(event.target.value)}
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Button type="submit">Aplicar filtros</Button>
              <Button type="button" variant="outline" onClick={clearAdminFilters}>
                Limpar
              </Button>
            </div>
          </form>

          {adminHistory.isLoading ? (
            <div className="glass-card p-6 text-sm text-muted-foreground">
              Carregando auditoria administrativa...
            </div>
          ) : adminHistory.isError || !adminHistory.data ? (
            <div className="glass-card p-6 space-y-3">
              <p className="text-sm text-destructive">
                Falha ao carregar a auditoria administrativa.
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => adminHistory.refetch()}
              >
                Tentar novamente
              </Button>
            </div>
          ) : (
            <div className="glass-card overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border bg-muted/50">
                    <th className="text-left p-3 font-medium text-muted-foreground">
                      Data
                    </th>
                    <th className="text-left p-3 font-medium text-muted-foreground">
                      Usuário
                    </th>
                    <th className="text-left p-3 font-medium text-muted-foreground">
                      Ação
                    </th>
                    <th className="text-left p-3 font-medium text-muted-foreground">
                      Detalhes
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {adminHistory.data.map((row, index) => (
                    <tr
                      key={`${row.date}-${index}`}
                      className="border-b border-border last:border-0 hover:bg-muted/30 transition-colors"
                    >
                      <td className="p-3 text-muted-foreground font-mono text-xs whitespace-nowrap">
                        {row.date}
                      </td>
                      <td className="p-3 text-foreground">{row.user}</td>
                      <td className="p-3">
                        <Badge
                          variant={statusVariant[row.status]}
                          className={statusColors[row.status] || ""}
                        >
                          {row.action}
                        </Badge>
                      </td>
                      <td className="p-3 text-muted-foreground">
                        {row.details}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
    </div>
  );
};

export default HistoryPage;
