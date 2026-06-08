import { useState } from "react";
import { Database, Clock, AlertTriangle, CheckCircle2, RefreshCw, TrendingUp } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { PageError, PageLoader } from "@/components/PageState";
import { useIndexStatus } from "@/hooks/use-app-query";
import { indexService } from "@/lib/api/services";

const IndexStatusPage = () => {
  const { data, isLoading, isError, refetch } = useIndexStatus();
  const { toast } = useToast();
  const [reindexing, setReindexing] = useState(false);

  const handleReindex = async () => {
    setReindexing(true);
    try {
      const result = await indexService.reindexAll();
      await refetch();
      toast({
        title: "Reindexação concluída",
        description: result.message,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Falha ao executar a reindexação.";
      toast({
        title: "Falha na reindexação",
        description: message,
        variant: "destructive",
      });
    } finally {
      setReindexing(false);
    }
  };

  if (isLoading) {
    return <PageLoader label="Carregando status da indexação..." />;
  }

  if (isError || !data) {
    return <PageError title="Falha ao carregar o status da indexação." onRetry={() => refetch()} />;
  }

  return (
    <div className="max-w-4xl mx-auto animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Status da Indexação</h1>
          <p className="text-sm text-muted-foreground mt-1">Processamento, índice e monitoramento (UC15–UC19)</p>
        </div>
        <Button onClick={handleReindex} disabled={reindexing} className="gap-2">
          <RefreshCw className={`h-4 w-4 ${reindexing ? "animate-spin" : ""}`} />
          {reindexing ? "Reindexando..." : "Reindexar Todos"}
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-6">
        <div className="stat-card">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <Database className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{data.indexedDocuments}</p>
              <p className="text-xs text-muted-foreground">Documentos indexados</p>
            </div>
          </div>
        </div>
        <div className="stat-card">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-info/10 flex items-center justify-center">
              <Clock className="h-5 w-5 text-info" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{data.averageTime}</p>
              <p className="text-xs text-muted-foreground">Tempo médio</p>
            </div>
          </div>
        </div>
        <div className="stat-card">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-success/10 flex items-center justify-center">
              <TrendingUp className="h-5 w-5 text-success" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{data.successRate}</p>
              <p className="text-xs text-muted-foreground">Taxa de sucesso</p>
            </div>
          </div>
        </div>
        <div className="stat-card">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-destructive/10 flex items-center justify-center">
              <AlertTriangle className="h-5 w-5 text-destructive" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{data.errors}</p>
              <p className="text-xs text-muted-foreground">Erros detectados</p>
            </div>
          </div>
        </div>
      </div>

      <div className="glass-card p-5 mb-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-foreground">Integridade do Índice</h3>
          <Badge variant={data.integrityOk ? "default" : "destructive"}>
            {data.integrityOk ? "Consistente" : `${data.inconsistencyCount} inconsistência(s)`}
          </Badge>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-lg font-bold text-foreground">{data.consistency.documentsWithoutActiveVersion}</p>
            <p className="text-xs text-muted-foreground">Sem versão ativa</p>
          </div>
          <div>
            <p className="text-lg font-bold text-foreground">{data.consistency.documentsWithoutIndex}</p>
            <p className="text-xs text-muted-foreground">Sem índice</p>
          </div>
          <div>
            <p className="text-lg font-bold text-foreground">{data.consistency.orphanIndexEntries}</p>
            <p className="text-xs text-muted-foreground">Entradas órfãs</p>
          </div>
          <div>
            <p className="text-lg font-bold text-foreground">{data.consistency.staleTerms}</p>
            <p className="text-xs text-muted-foreground">Termos desatualizados</p>
          </div>
        </div>
      </div>

      {/* Current Progress */}
      <div className="glass-card p-5 mb-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-foreground">Indexação em andamento</h3>
          <Badge>Em processamento</Badge>
        </div>
        <Progress value={data.currentProgress} className="h-2.5 mb-2" />
        <p className="text-xs text-muted-foreground">{data.currentProgress}% concluído · Estimativa: {data.remainingEstimate}</p>
      </div>

      {/* Status summary */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="glass-card p-4 text-center">
          <p className="text-lg font-bold text-success">{data.summary.completed}</p>
          <p className="text-xs text-muted-foreground">Concluídos</p>
        </div>
        <div className="glass-card p-4 text-center">
          <p className="text-lg font-bold text-info">{data.summary.processing}</p>
          <p className="text-xs text-muted-foreground">Em processamento</p>
        </div>
        <div className="glass-card p-4 text-center">
          <p className="text-lg font-bold text-destructive">{data.summary.failed}</p>
          <p className="text-xs text-muted-foreground">Falhas</p>
        </div>
      </div>

      <div className="glass-card p-5 mb-6">
        <h3 className="text-sm font-semibold text-foreground mb-4">Métricas Básicas do Índice</h3>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 text-sm">
          <div>
            <p className="text-lg font-bold text-foreground">{data.metrics.activeDocuments}</p>
            <p className="text-xs text-muted-foreground">Docs ativos</p>
          </div>
          <div>
            <p className="text-lg font-bold text-foreground">{data.metrics.activeVersions}</p>
            <p className="text-xs text-muted-foreground">Versões ativas</p>
          </div>
          <div>
            <p className="text-lg font-bold text-foreground">{data.metrics.totalTerms}</p>
            <p className="text-xs text-muted-foreground">Termos</p>
          </div>
          <div>
            <p className="text-lg font-bold text-foreground">{data.metrics.totalPostings}</p>
            <p className="text-xs text-muted-foreground">Postings</p>
          </div>
          <div>
            <p className="text-lg font-bold text-foreground">{data.metrics.averageTermsPerDocument}</p>
            <p className="text-xs text-muted-foreground">Termos/doc</p>
          </div>
        </div>
        <p className="text-xs text-muted-foreground mt-4">
          Última indexação bem-sucedida: {data.metrics.lastIndexedAt ? new Date(data.metrics.lastIndexedAt).toLocaleString("pt-BR") : "indisponível"}
        </p>
      </div>

      <div className="glass-card p-5 mb-6">
        <h3 className="text-sm font-semibold text-foreground mb-4">OCR em PDFs escaneados</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-lg font-bold text-foreground">{data.metrics.ocrDocuments}</p>
            <p className="text-xs text-muted-foreground">Docs com OCR</p>
          </div>
          <div>
            <p className="text-lg font-bold text-success">{data.metrics.ocrSuccess}</p>
            <p className="text-xs text-muted-foreground">OCRs com sucesso</p>
          </div>
          <div>
            <p className="text-lg font-bold text-destructive">{data.metrics.ocrFailed}</p>
            <p className="text-xs text-muted-foreground">OCRs com falha</p>
          </div>
          <div>
            <p className="text-lg font-bold text-foreground">{(data.metrics.averageOcrTimeMs / 1000).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}s</p>
            <p className="text-xs text-muted-foreground">Tempo médio OCR</p>
          </div>
        </div>
      </div>

      {/* Log */}
      <div className="glass-card overflow-hidden">
        <div className="p-4 border-b border-border">
          <h3 className="text-sm font-semibold text-foreground">Log de Processamento em Tempo Real</h3>
        </div>
        <div className="divide-y divide-border max-h-96 overflow-y-auto">
          {data.logs.map((log, i) => (
            <div key={i} className="flex items-start gap-3 p-3 text-sm hover:bg-muted/30 transition-colors">
              <span className="text-xs text-muted-foreground font-mono whitespace-nowrap mt-0.5">{log.time}</span>
              {log.type === "success" && <CheckCircle2 className="h-4 w-4 text-success shrink-0 mt-0.5" />}
              {log.type === "error" && <AlertTriangle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />}
              {log.type === "info" && <Database className="h-4 w-4 text-info shrink-0 mt-0.5" />}
              <span className={log.type === "error" ? "text-destructive" : "text-foreground"}>{log.message}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default IndexStatusPage;
