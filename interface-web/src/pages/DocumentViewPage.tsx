import { useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  Download,
  Calendar,
  Tag,
  User,
  FileText,
  RefreshCw,
  Hash,
  Clock,
  ChevronLeft,
  ChevronRight,
  FileJson,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";
import { documentService } from "@/lib/api/services";
import { PageError, PageLoader } from "@/components/PageState";
import { useDocument } from "@/hooks/use-app-query";

type DocumentNavigationState = {
  resultIds?: number[];
  query?: string;
  from?: string;
};

const HEADING_BLOCK_MAX_LENGTH = 90;

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

const isHeadingBlock = (block: string) =>
  block.length <= HEADING_BLOCK_MAX_LENGTH &&
  !/[.!?]$/.test(block) &&
  block.split(/\s+/).length <= 14;

const DocumentViewPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { id } = useParams();
  const { toast } = useToast();
  const { isAdmin } = useAuth();
  const [reindexing, setReindexing] = useState(false);
  const [exporting, setExporting] = useState<string | null>(null);
  const documentId = Number(id);
  const { data: document, isLoading, isError, refetch } = useDocument(documentId);
  const navigationState = (location.state || {}) as DocumentNavigationState;
  const resultIds = navigationState.resultIds || [];
  const currentResultIndex = resultIds.indexOf(documentId);
  const previousDocumentId = currentResultIndex > 0 ? resultIds[currentResultIndex - 1] : null;
  const nextDocumentId = currentResultIndex >= 0 && currentResultIndex < resultIds.length - 1
    ? resultIds[currentResultIndex + 1]
    : null;

  const handleReindex = async () => {
    setReindexing(true);
    try {
      await documentService.reindex(documentId);
      await refetch();
      toast({
        title: "Documento reindexado",
        description: "O documento foi reprocessado e o índice foi atualizado com sucesso (UC13).",
      });
    } catch {
      toast({
        title: "Falha na reindexação",
        description: "Não foi possível reindexar o documento.",
        variant: "destructive",
      });
    } finally {
      setReindexing(false);
    }
  };

  const handleDownload = async () => {
    if (!document?.downloadUrl) {
      toast({
        title: "Download indisponível",
        description: "Este documento não possui arquivo associado para recuperação.",
        variant: "destructive",
      });
      return;
    }

    setExporting("download");
    try {
      const { blob, filename } = await documentService.download(documentId);
      saveBlob(blob, filename || `${document.title}.${document.type.toLowerCase()}`);
    } catch {
      toast({
        title: "Falha no download",
        description: "Não foi possível baixar o arquivo original do documento.",
        variant: "destructive",
      });
    } finally {
      setExporting(null);
    }
  };

  const handleExport = async (format: "txt" | "json") => {
    setExporting(format);
    try {
      const { blob, filename } = await documentService.export(documentId, format);
      saveBlob(blob, filename || `${document?.title || "documento"}.${format}`);
    } catch {
      toast({
        title: "Falha na exportação",
        description: "Não foi possível exportar o conteúdo do documento.",
        variant: "destructive",
      });
    } finally {
      setExporting(null);
    }
  };

  const goToRelatedDocument = (targetId: number | null) => {
    if (!targetId) {
      return;
    }
    navigate(`/documento/${targetId}`, { state: navigationState });
  };

  if (isLoading) {
    return <PageLoader label="Carregando documento..." />;
  }

  if (isError || !document) {
    return <PageError title="Falha ao carregar o documento." onRetry={() => refetch()} />;
  }

  const displayTitle = document.displayTitle || document.title;
  const readingContent = document.formattedContent || document.content;
  const readingBlocks = readingContent
    .split(/\n{2,}/)
    .map((block) => block.trim())
    .filter(Boolean);

  return (
    <div className="max-w-4xl mx-auto animate-fade-in">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <Button
          variant="ghost"
          onClick={() => {
            if (navigationState.from) {
              navigate(`/resultados${navigationState.from}`);
              return;
            }
            navigate(-1);
          }}
          className="gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Voltar
        </Button>
        <div className="flex flex-wrap gap-2 lg:justify-end">
          {resultIds.length > 1 && (
            <div className="hidden sm:flex items-center gap-1 mr-2">
              <Button
                variant="outline"
                size="icon"
                disabled={!previousDocumentId}
                onClick={() => goToRelatedDocument(previousDocumentId)}
                title="Documento anterior dos resultados"
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                disabled={!nextDocumentId}
                onClick={() => goToRelatedDocument(nextDocumentId)}
                title="Próximo documento dos resultados"
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
          {isAdmin && (
            <Button
              variant="outline"
              className="gap-2"
              onClick={handleReindex}
              disabled={reindexing}
            >
              <RefreshCw className={`h-4 w-4 ${reindexing ? "animate-spin" : ""}`} />
              {reindexing ? "Reindexando..." : "Reindexar (Admin)"}
            </Button>
          )}
          <Button variant="outline" className="gap-2" onClick={() => handleExport("txt")} disabled={!!exporting}>
            <FileText className="h-4 w-4" />
            TXT
          </Button>
          <Button variant="outline" className="gap-2" onClick={() => handleExport("json")} disabled={!!exporting}>
            <FileJson className="h-4 w-4" />
            JSON
          </Button>
          <Button className="gap-2" onClick={handleDownload} disabled={!!exporting || !document.downloadUrl}>
            <Download className="h-4 w-4" />
            Original
          </Button>
        </div>
      </div>

      <div className="glass-card">
        <div className="border-b border-border bg-muted/40 p-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            <span className="font-medium text-foreground">Visualização completa do conteúdo extraído</span>
          </div>
          <p className="mt-2 break-words">
            Leitura otimizada de <span className="font-medium text-foreground">{displayTitle}</span>.
          </p>
        </div>

        <div className="border-b border-border p-6">
          <div className="mb-6">
            <h1 className="text-2xl font-semibold leading-tight text-foreground break-words">
              {displayTitle}
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Documento indexado para leitura clara, preservando o arquivo original para download e reprocessamento.
            </p>
          </div>

          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            <div className="rounded-xl border border-border/70 bg-background/70 p-4">
              <div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                <Tag className="h-3.5 w-3.5" />
                Classificação
              </div>
              <div className="flex flex-wrap items-center gap-2 text-sm text-foreground">
                <Badge variant="secondary">{document.category}</Badge>
                <span>{document.documentType}</span>
                <span className="text-muted-foreground">·</span>
                <span>{document.format}</span>
                <span className="text-muted-foreground">·</span>
                <span>{document.size}</span>
              </div>
            </div>

            <div className="rounded-xl border border-border/70 bg-background/70 p-4">
              <div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                <Calendar className="h-3.5 w-3.5" />
                Datas
              </div>
              <div className="space-y-1 text-sm text-foreground">
                <p>Documento: {new Date(document.date).toLocaleDateString("pt-BR")}</p>
                <p className="text-muted-foreground">Indexado em {new Date(document.indexedAt).toLocaleString("pt-BR")}</p>
              </div>
            </div>

            <div className="rounded-xl border border-border/70 bg-background/70 p-4">
              <div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                <User className="h-3.5 w-3.5" />
                Responsáveis
              </div>
              <div className="space-y-1 text-sm text-foreground">
                <p>{document.author}</p>
                <p className="text-muted-foreground">Enviado por {document.uploadedBy}</p>
              </div>
            </div>

            <div className="rounded-xl border border-border/70 bg-background/70 p-4 md:col-span-2 xl:col-span-1">
              <div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                <FileText className="h-3.5 w-3.5" />
                Arquivo
              </div>
              <div className="space-y-1 text-sm text-foreground">
                <p className="break-words">{document.fileName}</p>
                <p className="text-muted-foreground">{document.mimeType}</p>
              </div>
            </div>

            <div className="rounded-xl border border-border/70 bg-background/70 p-4">
              <div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                <Hash className="h-3.5 w-3.5" />
                Controle
              </div>
              <div className="space-y-1 text-sm text-foreground">
                <p>Versão {document.version}</p>
                <p>{document.extractedCharacters.toLocaleString("pt-BR")} caracteres extraídos</p>
                {currentResultIndex >= 0 && (
                  <p className="text-muted-foreground">
                    Resultado {currentResultIndex + 1} de {resultIds.length}
                  </p>
                )}
              </div>
            </div>

            <div className="rounded-xl border border-border/70 bg-background/70 p-4">
              <div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                <Clock className="h-3.5 w-3.5" />
                Integridade
              </div>
              <div className="space-y-1 text-sm text-foreground">
                <p className="break-all">{document.hash}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-background/80 p-6 md:p-8">
          <div className="mx-auto max-w-3xl">
            <div className="mb-6 border-b border-border/70 pb-4">
              <p className="text-xs font-medium uppercase tracking-[0.22em] text-muted-foreground">
                Texto formatado para leitura
              </p>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                O conteúdo abaixo reaproveita o texto extraído e reorganiza parágrafos e blocos para reduzir quebras ruins de linha.
              </p>
            </div>

            <article className="space-y-4 text-[1.02rem] leading-8 text-foreground/90">
              {readingBlocks.map((block, index) =>
                isHeadingBlock(block) ? (
                  <h2 key={`${index}-${block.slice(0, 20)}`} className="pt-2 text-lg font-semibold leading-7 text-foreground">
                    {block}
                  </h2>
                ) : (
                  <p key={`${index}-${block.slice(0, 20)}`} className="text-pretty">
                    {block}
                  </p>
                ),
              )}
            </article>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentViewPage;
