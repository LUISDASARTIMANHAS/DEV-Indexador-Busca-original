import { useMemo, useState } from "react";
import {
  BarChart3,
  Clock,
  Download,
  FileText,
  Hash,
  Save,
  Search,
  TrendingUp,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { PageError, PageLoader } from "@/components/PageState";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useMetricCalculations, useMetrics, useMetricsReport } from "@/hooks/use-app-query";
import { useToast } from "@/hooks/use-toast";
import { metricsService } from "@/lib/api/services";
import type { MetricsReportFilters } from "@/types/app";

const COLORS = [
  "hsl(152, 45%, 32%)",
  "hsl(152, 35%, 45%)",
  "hsl(152, 25%, 55%)",
  "hsl(150, 20%, 65%)",
  "hsl(150, 15%, 75%)",
];

const CATEGORY_COLORS = [
  "hsl(152, 45%, 32%)",
  "hsl(210, 70%, 50%)",
  "hsl(38, 92%, 50%)",
  "hsl(0, 65%, 48%)",
];

const formatDateInput = (value: Date) => {
  const year = value.getFullYear();
  const month = `${value.getMonth() + 1}`.padStart(2, "0");
  const day = `${value.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
};

const buildPresetRange = (preset: string): MetricsReportFilters => {
  const today = new Date();
  const start = new Date(today);

  switch (preset) {
    case "7d":
      start.setDate(today.getDate() - 6);
      break;
    case "90d":
      start.setDate(today.getDate() - 89);
      break;
    case "365d":
      start.setDate(today.getDate() - 364);
      break;
    case "30d":
    default:
      start.setDate(today.getDate() - 29);
      break;
  }

  return {
    dateFrom: formatDateInput(start),
    dateTo: formatDateInput(today),
  };
};

const saveBlob = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob);
  const anchor = window.document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  window.document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
};

const formatDateTime = (value?: string | null) => {
  if (!value) {
    return "indisponível";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString("pt-BR");
};

const MetricsPage = () => {
  const { toast } = useToast();
  const initialRange = useMemo(() => buildPresetRange("30d"), []);
  const [preset, setPreset] = useState("30d");
  const [formDateFrom, setFormDateFrom] = useState(initialRange.dateFrom || "");
  const [formDateTo, setFormDateTo] = useState(initialRange.dateTo || "");
  const [reportFilters, setReportFilters] = useState<MetricsReportFilters>(initialRange);
  const [exporting, setExporting] = useState<"csv" | "pdf" | null>(null);
  const [persisting, setPersisting] = useState(false);

  const { data, isLoading, isError, refetch } = useMetrics();
  const {
    data: report,
    isLoading: reportLoading,
    isError: reportError,
    refetch: refetchReport,
  } = useMetricsReport(reportFilters);
  const {
    data: calculations,
    isLoading: calculationsLoading,
    refetch: refetchCalculations,
  } = useMetricCalculations(8);

  const applyPreset = (value: string) => {
    setPreset(value);
    const nextRange = buildPresetRange(value);
    setFormDateFrom(nextRange.dateFrom || "");
    setFormDateTo(nextRange.dateTo || "");
    setReportFilters(nextRange);
  };

  const applyReportFilters = (event: React.FormEvent) => {
    event.preventDefault();
    setReportFilters({
      dateFrom: formDateFrom || undefined,
      dateTo: formDateTo || undefined,
    });
  };

  const handleExport = async (format: "csv" | "pdf") => {
    setExporting(format);
    try {
      const { blob, filename } = await metricsService.exportReport(format, reportFilters);
      saveBlob(blob, filename || `relatorio-busca.${format}`);
    } catch {
      toast({
        title: "Falha na exportação",
        description: "Não foi possível exportar o relatório do período selecionado.",
        variant: "destructive",
      });
    } finally {
      setExporting(null);
    }
  };

  const handlePersistCalculation = async () => {
    setPersisting(true);
    try {
      await metricsService.persistCalculation(reportFilters);
      await Promise.all([refetch(), refetchReport(), refetchCalculations()]);
      toast({
        title: "Relatório consolidado",
        description: "As métricas do período foram armazenadas para análise posterior.",
      });
    } catch {
      toast({
        title: "Falha ao consolidar",
        description: "Não foi possível armazenar o cálculo consolidado do período.",
        variant: "destructive",
      });
    } finally {
      setPersisting(false);
    }
  };

  if (isLoading) {
    return <PageLoader label="Carregando métricas..." />;
  }

  if (isError || !data) {
    return <PageError title="Falha ao carregar métricas." onRetry={() => refetch()} />;
  }

  return (
    <div className="animate-fade-in space-y-6">
      <div className="flex items-center justify-between mb-6 gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Métricas e Relatórios</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Monitoramento de desempenho, qualidade da busca e relatórios administrativos.
          </p>
        </div>
        <Select value={preset} onValueChange={applyPreset}>
          <SelectTrigger className="w-44">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="7d">Últimos 7 dias</SelectItem>
            <SelectItem value="30d">Últimos 30 dias</SelectItem>
            <SelectItem value="90d">Últimos 90 dias</SelectItem>
            <SelectItem value="365d">Último ano</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="stat-card">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <Search className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{data.overview.totalQueries}</p>
              <p className="text-xs text-muted-foreground">Total de consultas</p>
            </div>
          </div>
        </div>
        <div className="stat-card">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-info/10 flex items-center justify-center">
              <Clock className="h-5 w-5 text-info" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{data.overview.averageSearchTime}</p>
              <p className="text-xs text-muted-foreground">Tempo médio</p>
            </div>
          </div>
        </div>
        <div className="stat-card">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-success/10 flex items-center justify-center">
              <FileText className="h-5 w-5 text-success" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{data.overview.indexedDocuments}</p>
              <p className="text-xs text-muted-foreground">Docs indexados</p>
            </div>
          </div>
        </div>
        <div className="stat-card">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <TrendingUp className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{data.overview.successRate}</p>
              <p className="text-xs text-muted-foreground">Taxa de sucesso</p>
            </div>
          </div>
        </div>
        <div className="stat-card">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-warning/10 flex items-center justify-center">
              <Hash className="h-5 w-5 text-warning" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{data.overview.averageResults}</p>
              <p className="text-xs text-muted-foreground">Média de resultados</p>
            </div>
          </div>
        </div>
        <div className="stat-card">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-warning/10 flex items-center justify-center">
              <BarChart3 className="h-5 w-5 text-warning" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{data.overview.queriesToday}</p>
              <p className="text-xs text-muted-foreground">Consultas hoje</p>
            </div>
          </div>
        </div>
        <div className="stat-card">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-destructive/10 flex items-center justify-center">
              <Search className="h-5 w-5 text-destructive" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{data.overview.queriesWithoutResults}</p>
              <p className="text-xs text-muted-foreground">Consultas sem retorno</p>
            </div>
          </div>
        </div>
        <div className="stat-card">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-info/10 flex items-center justify-center">
              <TrendingUp className="h-5 w-5 text-info" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{data.overview.zeroResultsRate}</p>
              <p className="text-xs text-muted-foreground">Taxa sem resultados</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">Consultas por dia</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data.queriesByDay}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(200, 15%, 90%)" />
              <XAxis dataKey="day" tick={{ fontSize: 12 }} stroke="hsl(200, 10%, 45%)" />
              <YAxis tick={{ fontSize: 12 }} stroke="hsl(200, 10%, 45%)" />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(0, 0%, 100%)",
                  border: "1px solid hsl(200, 15%, 90%)",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
              />
              <Bar dataKey="consultas" fill="hsl(152, 45%, 32%)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">Distribuição de consultas</h3>
          <div className="flex items-center gap-6">
            <ResponsiveContainer width="50%" height={260}>
              <PieChart>
                <Pie
                  data={data.queryOutcomeDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={90}
                  dataKey="value"
                  paddingAngle={3}
                >
                  {data.queryOutcomeDistribution.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(0, 0%, 100%)",
                    border: "1px solid hsl(200, 15%, 90%)",
                    borderRadius: "8px",
                    fontSize: "12px",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex-1 space-y-3">
              {data.queryOutcomeDistribution.map((item, i) => (
                <div key={item.name} className="rounded-xl border border-border/70 bg-background/70 px-4 py-3">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <span className="h-3 w-3 rounded-full shrink-0" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                      <span className="text-foreground">{item.name}</span>
                    </div>
                    <span className="text-muted-foreground font-mono">{item.value}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">Documentos por categoria</h3>
          <div className="flex items-center gap-6">
            <ResponsiveContainer width="50%" height={260}>
              <PieChart>
                <Pie data={data.documentsByCategory} cx="50%" cy="50%" innerRadius={50} outerRadius={90} dataKey="value" paddingAngle={3}>
                  {data.documentsByCategory.map((_, i) => (
                    <Cell key={i} fill={CATEGORY_COLORS[i % CATEGORY_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(0, 0%, 100%)",
                    border: "1px solid hsl(200, 15%, 90%)",
                    borderRadius: "8px",
                    fontSize: "12px",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex-1 space-y-2">
              {data.documentsByCategory.map((cat, i) => (
                <div key={cat.name} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <span className="h-3 w-3 rounded-full shrink-0" style={{ backgroundColor: CATEGORY_COLORS[i % CATEGORY_COLORS.length] }} />
                    <span className="text-foreground">{cat.name}</span>
                  </div>
                  <span className="text-muted-foreground font-mono">{cat.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">Termos mais buscados</h3>
          <div className="flex items-center gap-6">
            <ResponsiveContainer width="40%" height={220}>
              <PieChart>
                <Pie data={data.topTerms} cx="50%" cy="50%" innerRadius={40} outerRadius={80} dataKey="value" paddingAngle={3}>
                  {data.topTerms.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(0, 0%, 100%)",
                    border: "1px solid hsl(200, 15%, 90%)",
                    borderRadius: "8px",
                    fontSize: "12px",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex-1 space-y-2">
              {data.topTerms.map((term, i) => (
                <div key={term.name} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <span className="h-3 w-3 rounded-full shrink-0" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                    <span className="text-foreground">{term.name}</span>
                  </div>
                  <span className="text-muted-foreground font-mono">{term.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <section className="glass-card p-5 space-y-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-foreground">Relatórios e Exportações</h2>
            <p className="text-sm text-muted-foreground mt-1">
              Consolide estatísticas de uso, qualidade da busca e exporte relatórios administrativos.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              className="gap-2"
              onClick={() => handleExport("csv")}
              disabled={reportLoading || exporting !== null}
            >
              <Download className="h-4 w-4" />
              {exporting === "csv" ? "Exportando CSV..." : "Exportar CSV"}
            </Button>
            <Button
              variant="outline"
              className="gap-2"
              onClick={() => handleExport("pdf")}
              disabled={reportLoading || exporting !== null}
            >
              <FileText className="h-4 w-4" />
              {exporting === "pdf" ? "Exportando PDF..." : "Exportar PDF"}
            </Button>
            <Button
              className="gap-2"
              onClick={handlePersistCalculation}
              disabled={persisting}
            >
              <Save className="h-4 w-4" />
              {persisting ? "Consolidando..." : "Consolidar Período"}
            </Button>
          </div>
        </div>

        <form onSubmit={applyReportFilters} className="grid grid-cols-1 md:grid-cols-[1fr_1fr_auto] gap-3">
          <Input
            type="date"
            value={formDateFrom}
            onChange={(event) => setFormDateFrom(event.target.value)}
          />
          <Input
            type="date"
            value={formDateTo}
            onChange={(event) => setFormDateTo(event.target.value)}
          />
          <Button type="submit" variant="secondary">
            Atualizar Relatório
          </Button>
        </form>

        {reportLoading ? (
          <div className="rounded-xl border border-border/70 bg-background/70 p-6 text-sm text-muted-foreground">
            Carregando relatório do período...
          </div>
        ) : reportError || !report ? (
          <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-6 text-sm text-destructive">
            Não foi possível carregar o relatório analítico do período selecionado.
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-6 gap-4">
              <div className="rounded-2xl border border-border/70 bg-background/70 p-4">
                <p className="text-xs text-muted-foreground">Consultas no período</p>
                <p className="mt-2 text-2xl font-bold text-foreground">{report.summary.totalQueries}</p>
              </div>
              <div className="rounded-2xl border border-border/70 bg-background/70 p-4">
                <p className="text-xs text-muted-foreground">Consultas únicas</p>
                <p className="mt-2 text-2xl font-bold text-foreground">{report.summary.uniqueQueries}</p>
              </div>
              <div className="rounded-2xl border border-border/70 bg-background/70 p-4">
                <p className="text-xs text-muted-foreground">Tempo médio</p>
                <p className="mt-2 text-2xl font-bold text-foreground">{report.summary.averageResponseTimeMs} ms</p>
              </div>
              <div className="rounded-2xl border border-border/70 bg-background/70 p-4">
                <p className="text-xs text-muted-foreground">Média de resultados</p>
                <p className="mt-2 text-2xl font-bold text-foreground">{report.summary.averageResults}</p>
              </div>
              <div className="rounded-2xl border border-border/70 bg-background/70 p-4">
                <p className="text-xs text-muted-foreground">Sem resultados</p>
                <p className="mt-2 text-2xl font-bold text-foreground">{report.summary.zeroResultsRate}</p>
              </div>
              <div className="rounded-2xl border border-border/70 bg-background/70 p-4">
                <p className="text-xs text-muted-foreground">Docs indexados</p>
                <p className="mt-2 text-2xl font-bold text-foreground">{report.summary.indexedDocuments}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="rounded-2xl border border-border/70 bg-background/70 p-4">
                <h3 className="text-sm font-semibold text-foreground mb-3">Consultas mais frequentes</h3>
                <div className="space-y-3">
                  {report.frequentQueries.length === 0 ? (
                    <p className="text-sm text-muted-foreground">Nenhuma consulta registrada no período.</p>
                  ) : (
                    report.frequentQueries.map((item) => (
                      <div key={item.query} className="flex items-start justify-between gap-3 text-sm">
                        <div>
                          <p className="font-medium text-foreground">{item.query}</p>
                          <p className="text-muted-foreground">
                            {item.averageResponseTimeMs} ms · média {item.averageResults} resultados
                          </p>
                        </div>
                        <span className="font-mono text-muted-foreground">{item.count}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div className="rounded-2xl border border-border/70 bg-background/70 p-4">
                <h3 className="text-sm font-semibold text-foreground mb-3">Consultas sem resultados</h3>
                <div className="space-y-3">
                  {report.zeroResultQueries.length === 0 ? (
                    <p className="text-sm text-muted-foreground">Nenhuma consulta sem retorno no período.</p>
                  ) : (
                    report.zeroResultQueries.map((item) => (
                      <div key={item.query} className="flex items-start justify-between gap-3 text-sm">
                        <div>
                          <p className="font-medium text-foreground">{item.query}</p>
                          <p className="text-muted-foreground">{item.averageResponseTimeMs} ms</p>
                        </div>
                        <span className="font-mono text-muted-foreground">{item.count}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div className="rounded-2xl border border-border/70 bg-background/70 p-4">
                <h3 className="text-sm font-semibold text-foreground mb-3">Documentos mais acessados</h3>
                <div className="space-y-3">
                  {report.accessedDocuments.length === 0 ? (
                    <p className="text-sm text-muted-foreground">Nenhum acesso documental registrado no período.</p>
                  ) : (
                    report.accessedDocuments.map((item) => (
                      <div key={item.id} className="text-sm">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="font-medium text-foreground">{item.title}</p>
                            <p className="text-muted-foreground">
                              {item.category} · visualizações {item.viewCount} · downloads {item.downloadCount} · exportações {item.exportCount}
                            </p>
                          </div>
                          <span className="font-mono text-muted-foreground">{item.accessCount}</span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-border/70 bg-background/70 p-4 text-sm">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-muted-foreground">Consulta mais frequente</p>
                  <p className="mt-1 font-medium text-foreground">{report.summary.mostFrequentQuery || "indisponível"}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Documento mais acessado</p>
                  <p className="mt-1 font-medium text-foreground">{report.summary.mostAccessedDocument || "indisponível"}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Período inicial</p>
                  <p className="mt-1 text-foreground">{formatDateTime(report.summary.periodStart)}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Período final</p>
                  <p className="mt-1 text-foreground">{formatDateTime(report.summary.periodEnd)}</p>
                </div>
              </div>
            </div>
          </>
        )}
      </section>

      <section className="glass-card p-5">
        <div className="flex items-center justify-between gap-4 mb-4">
          <div>
            <h2 className="text-lg font-semibold text-foreground">Cálculos Armazenados</h2>
            <p className="text-sm text-muted-foreground mt-1">
              Histórico consolidado de métricas para análise posterior e comparação entre períodos.
            </p>
          </div>
        </div>

        {calculationsLoading ? (
          <div className="text-sm text-muted-foreground">Carregando cálculos consolidados...</div>
        ) : !calculations || calculations.length === 0 ? (
          <div className="text-sm text-muted-foreground">Nenhum cálculo consolidado armazenado até o momento.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="py-2 text-left font-medium text-muted-foreground">Período</th>
                  <th className="py-2 text-left font-medium text-muted-foreground">Consultas</th>
                  <th className="py-2 text-left font-medium text-muted-foreground">Tempo médio</th>
                  <th className="py-2 text-left font-medium text-muted-foreground">Média resultados</th>
                  <th className="py-2 text-left font-medium text-muted-foreground">Sem retorno</th>
                  <th className="py-2 text-left font-medium text-muted-foreground">Calculado em</th>
                </tr>
              </thead>
              <tbody>
                {calculations.map((item) => (
                  <tr key={item.id} className="border-b border-border/60 last:border-0">
                    <td className="py-3 text-foreground">
                      {formatDateTime(item.periodStart)}<br />
                      <span className="text-muted-foreground">até {formatDateTime(item.periodEnd)}</span>
                    </td>
                    <td className="py-3 text-foreground">{item.totalQueries}</td>
                    <td className="py-3 text-foreground">{item.averageResponseTimeMs} ms</td>
                    <td className="py-3 text-foreground">{item.averageResults}</td>
                    <td className="py-3 text-foreground">{item.queriesWithoutResults}</td>
                    <td className="py-3 text-muted-foreground">{formatDateTime(item.calculatedAt)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
};

export default MetricsPage;
