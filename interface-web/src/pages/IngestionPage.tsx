import { useRef, useState } from "react";
import { Upload, FileText, CheckCircle2, X, ArrowRight, FilePlus2, History, Search } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { PageError, PageLoader } from "@/components/PageState";
import { useIngestionBatch, useIngestionHistory } from "@/hooks/use-app-query";
import { documentService, ingestionService, searchService } from "@/lib/api/services";
import type { BatchUploadResult, DocumentDetails, SearchResult, UploadedDocument } from "@/types/app";

const statusMap = {
  validated: { label: "Validado", variant: "secondary" as const, color: "text-info" },
  indexed: { label: "Indexado", variant: "default" as const, color: "text-success" },
  error: { label: "Falha", variant: "destructive" as const, color: "text-destructive" },
};

const documentTypeOptions = ["Edital", "Portaria", "Resolução", "Relatório", "Ata", "Contrato", "Plano", "Outro"];

const IngestionPage = () => {
  const batchQuery = useIngestionBatch();
  const historyQuery = useIngestionHistory();
  const queryClient = useQueryClient();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const batchInputRef = useRef<HTMLInputElement | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [batchDragOver, setBatchDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadMode, setUploadMode] = useState<"new" | "version">("new");
  const [documentLookup, setDocumentLookup] = useState("");
  const [versionTarget, setVersionTarget] = useState<SearchResult | null>(null);
  const [versionMatches, setVersionMatches] = useState<SearchResult[]>([]);
  const [batchFiles, setBatchFiles] = useState<File[]>([]);
  const [category, setCategory] = useState("");
  const [batchCategory, setBatchCategory] = useState("");
  const [documentDate, setDocumentDate] = useState("");
  const [batchDocumentDate, setBatchDocumentDate] = useState("");
  const [documentTitle, setDocumentTitle] = useState("");
  const [documentAuthor, setDocumentAuthor] = useState("");
  const [documentType, setDocumentType] = useState("");
  const [batchAuthor, setBatchAuthor] = useState("");
  const [batchDocumentType, setBatchDocumentType] = useState("");
  const [uploadedDocument, setUploadedDocument] = useState<UploadedDocument | DocumentDetails | null>(null);
  const [batchResult, setBatchResult] = useState<BatchUploadResult | null>(null);
  const [step, setStep] = useState<"idle" | "uploading" | "validated" | "done">("idle");
  const { toast } = useToast();
  const uploadMutation = useMutation({
    mutationFn: ingestionService.uploadDocument,
    onSuccess: async (document) => {
      setUploadedDocument(document);
      setStep("done");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["ingestion-batch"] }),
        queryClient.invalidateQueries({ queryKey: ["ingestion-history"] }),
        queryClient.invalidateQueries({ queryKey: ["search-results"] }),
        queryClient.invalidateQueries({ queryKey: ["index-status"] }),
      ]);
      toast({
        title: "Documento enviado",
        description: "Upload concluído, arquivo validado, texto extraído e metadados registrados.",
      });
    },
    onError: (error: Error) => {
      setStep("idle");
      toast({
        title: "Falha no upload",
        description: error.message,
        variant: "destructive",
      });
    },
  });
  const versionLookupMutation = useMutation({
    mutationFn: (query: string) => searchService.search(query, { limit: 5, page: 1 }),
    onSuccess: (result) => {
      setVersionMatches(result.items);
      if (!result.items.some((item) => item.id === versionTarget?.id)) {
        setVersionTarget(null);
      }
    },
    onError: (error: Error) => {
      toast({
        title: "Falha ao localizar documento",
        description: error.message,
        variant: "destructive",
      });
    },
  });
  const createVersionMutation = useMutation({
    mutationFn: ({ documentId, file }: { documentId: number; file: File }) =>
      documentService.createVersion(documentId, {
        file,
        category: category || undefined,
        documentDate: documentDate || undefined,
        title: documentTitle || undefined,
        author: documentAuthor || undefined,
        documentType: documentType || undefined,
      }),
    onSuccess: async (document) => {
      setUploadedDocument(document);
      setStep("done");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["document", document.id] }),
        queryClient.invalidateQueries({ queryKey: ["document-versions", document.id] }),
        queryClient.invalidateQueries({ queryKey: ["ingestion-batch"] }),
        queryClient.invalidateQueries({ queryKey: ["ingestion-history"] }),
        queryClient.invalidateQueries({ queryKey: ["search-results"] }),
        queryClient.invalidateQueries({ queryKey: ["index-status"] }),
      ]);
      toast({
        title: "Nova versão indexada",
        description: `Versão ${document.version} registrada como ativa para ${document.title}.`,
      });
    },
    onError: (error: Error) => {
      setStep("idle");
      toast({
        title: "Falha ao registrar versão",
        description: error.message,
        variant: "destructive",
      });
    },
  });
  const batchUploadMutation = useMutation({
    mutationFn: ingestionService.uploadBatch,
    onSuccess: async (result) => {
      setBatchResult(result);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["ingestion-batch"] }),
        queryClient.invalidateQueries({ queryKey: ["ingestion-history"] }),
      ]);
      toast({
        title: "Lote processado",
        description: `${result.successCount} arquivo(s) com sucesso, ${result.failureCount} falha(s).`,
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Falha no upload em lote",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const uploaded = !!selectedFile;

  const handleFileSelection = (file: File | null) => {
    setSelectedFile(file);
    setUploadedDocument(null);
    setStep(file ? "validated" : "idle");
  };

  const handleBatchFileSelection = (files: FileList | File[] | null) => {
    const normalizedFiles = files ? Array.from(files) : [];
    setBatchFiles(normalizedFiles);
    setBatchResult(null);
  };

  const handleSubmitUpload = () => {
    if (!selectedFile || (uploadMode === "new" && !category) || (uploadMode === "version" && !versionTarget)) {
      toast({
        title: "Dados incompletos",
        description: uploadMode === "version"
          ? "Selecione um arquivo e o documento que receberá a nova versão."
          : "Selecione um arquivo e informe a categoria antes de enviar.",
        variant: "destructive",
      });
      return;
    }

    setStep("uploading");
    if (uploadMode === "version" && versionTarget) {
      createVersionMutation.mutate({ documentId: versionTarget.id, file: selectedFile });
      return;
    }
    uploadMutation.mutate({
      file: selectedFile,
      category,
      documentDate: documentDate || undefined,
      title: documentTitle || undefined,
      author: documentAuthor || undefined,
      documentType: documentType || undefined,
    });
  };

  const setMode = (mode: "new" | "version") => {
    setUploadMode(mode);
    setUploadedDocument(null);
    setStep(selectedFile ? "validated" : "idle");
    setVersionTarget(null);
    setVersionMatches([]);
    setDocumentLookup("");
  };

  const searchVersionTarget = () => {
    const query = documentLookup.trim();
    if (!query) {
      toast({
        title: "Informe a busca",
        description: "Digite o título ou conteúdo do documento original.",
        variant: "destructive",
      });
      return;
    }
    versionLookupMutation.mutate(query);
  };

  const resetUpload = () => {
    setSelectedFile(null);
    setUploadedDocument(null);
    setCategory("");
    setDocumentDate("");
    setDocumentTitle("");
    setDocumentAuthor("");
    setDocumentType("");
    setVersionTarget(null);
    setVersionMatches([]);
    setDocumentLookup("");
    setStep("idle");
    if (inputRef.current) {
      inputRef.current.value = "";
    }
  };

  const handleSubmitBatchUpload = () => {
    if (batchFiles.length === 0 || !batchCategory) {
      toast({
        title: "Dados incompletos",
        description: "Selecione os arquivos e informe a categoria para o lote.",
        variant: "destructive",
      });
      return;
    }

    batchUploadMutation.mutate({
      files: batchFiles,
      category: batchCategory,
      documentDate: batchDocumentDate || undefined,
      author: batchAuthor || undefined,
      documentType: batchDocumentType || undefined,
    });
  };

  const resetBatchUpload = () => {
    setBatchFiles([]);
    setBatchCategory("");
    setBatchDocumentDate("");
    setBatchAuthor("");
    setBatchDocumentType("");
    setBatchResult(null);
    if (batchInputRef.current) {
      batchInputRef.current.value = "";
    }
  };

  const stepLabels = [
    { key: "upload", label: "Upload", done: uploaded },
    { key: "validate", label: "Validação", done: ["validated", "uploading", "done"].includes(step) },
    { key: "extract", label: "Extração", done: step === "done" },
    { key: "store", label: "Armazenamento", done: step === "done" },
    { key: "register", label: "Registro", done: step === "done" },
  ];

  if (batchQuery.isLoading || historyQuery.isLoading) {
    return <PageLoader label="Carregando dados de ingestão..." />;
  }

  if (batchQuery.isError || historyQuery.isError || !batchQuery.data || !historyQuery.data) {
    return <PageError title="Falha ao carregar o módulo de ingestão." onRetry={() => {
      batchQuery.refetch();
      historyQuery.refetch();
    }} />;
  }

  return (
    <div className="max-w-4xl mx-auto animate-fade-in">
      <h1 className="text-2xl font-bold text-foreground mb-1">Ingestão de Documentos</h1>
      <p className="text-sm text-muted-foreground mb-6">Upload, validação, extração e indexação (UC08–UC14)</p>

      <Tabs defaultValue="individual">
        <TabsList>
          <TabsTrigger value="individual">Individual</TabsTrigger>
          <TabsTrigger value="batch">Em Lote</TabsTrigger>
          <TabsTrigger value="history">Histórico de Ingestão</TabsTrigger>
        </TabsList>

        <TabsContent value="individual" className="mt-4 space-y-4">
          <div className="flex w-fit rounded-lg border border-border bg-background p-1">
            <Button
              size="sm"
              variant={uploadMode === "new" ? "default" : "ghost"}
              className="gap-2"
              onClick={() => setMode("new")}
            >
              <FilePlus2 className="h-4 w-4" />
              Novo documento
            </Button>
            <Button
              size="sm"
              variant={uploadMode === "version" ? "default" : "ghost"}
              className="gap-2"
              onClick={() => setMode("version")}
            >
              <History className="h-4 w-4" />
              Nova versão
            </Button>
          </div>

          {uploadMode === "version" && (
            <div className="rounded-lg border border-border bg-card p-4 space-y-3">
              <Label htmlFor="version-document-search">Documento original</Label>
              <div className="flex flex-col gap-2 sm:flex-row">
                <Input
                  id="version-document-search"
                  value={documentLookup}
                  onChange={(event) => setDocumentLookup(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      event.preventDefault();
                      searchVersionTarget();
                    }
                  }}
                  placeholder="Título ou termos do documento"
                />
                <Button
                  variant="outline"
                  className="shrink-0 gap-2"
                  onClick={searchVersionTarget}
                  disabled={versionLookupMutation.isPending}
                >
                  <Search className="h-4 w-4" />
                  {versionLookupMutation.isPending ? "Buscando..." : "Buscar"}
                </Button>
              </div>
              {versionMatches.length > 0 && (
                <div className="space-y-2" aria-label="Documentos encontrados">
                  {versionMatches.map((document) => (
                    <button
                      key={document.id}
                      type="button"
                      onClick={() => setVersionTarget(document)}
                      className={`flex w-full items-start justify-between gap-3 rounded-md border px-3 py-2 text-left text-sm transition-colors ${
                        versionTarget?.id === document.id
                          ? "border-primary bg-primary/5"
                          : "border-border hover:bg-muted/50"
                      }`}
                    >
                      <span className="min-w-0">
                        <span className="block truncate font-medium text-foreground">{document.title}</span>
                        <span className="block text-xs text-muted-foreground">
                          {document.category} | {document.documentType} | {document.author}
                        </span>
                      </span>
                      {versionTarget?.id === document.id && <Badge>Selecionado</Badge>}
                    </button>
                  ))}
                </div>
              )}
              {versionLookupMutation.isSuccess && versionMatches.length === 0 && (
                <p className="text-sm text-muted-foreground">Nenhum documento encontrado.</p>
              )}
            </div>
          )}

          {/* Pipeline steps */}
          <div className="glass-card p-4">
            <div className="flex items-center gap-2 justify-between">
              {stepLabels.map((s, i) => (
                <div key={s.key} className="flex items-center gap-2 flex-1">
                  <div className={`flex items-center gap-2 text-sm font-medium ${s.done ? "text-success" : "text-muted-foreground"}`}>
                    <div className={`h-6 w-6 rounded-full flex items-center justify-center text-xs font-bold ${s.done ? "bg-success text-success-foreground" : "bg-muted text-muted-foreground"}`}>
                      {s.done ? "✓" : i + 1}
                    </div>
                    {s.label}
                  </div>
                  {i < stepLabels.length - 1 && (
                    <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0" />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Drop zone */}
          <div
            className={`border-2 border-dashed rounded-xl p-10 text-center transition-all duration-200 cursor-pointer ${
              dragOver ? "border-primary bg-accent" : uploaded ? "border-success bg-success/5" : "border-border hover:border-primary/50"
            }`}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              handleFileSelection(e.dataTransfer.files[0] ?? null);
            }}
            onClick={() => inputRef.current?.click()}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.docx,.txt,.csv"
              className="hidden"
              onChange={(e) => handleFileSelection(e.target.files?.[0] ?? null)}
            />
            {uploaded ? (
              <div className="flex flex-col items-center gap-2">
                <CheckCircle2 className="h-10 w-10 text-success" />
                <p className="font-medium text-foreground">{selectedFile?.name}</p>
                <p className="text-sm text-muted-foreground">
                  {selectedFile ? `${(selectedFile.size / 1024 / 1024).toFixed(2)} MB` : ""} · {selectedFile?.name.split(".").pop()?.toUpperCase()}
                </p>
                <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); resetUpload(); }}>
                  <X className="h-3 w-3 mr-1" /> Remover
                </Button>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2">
                <Upload className="h-10 w-10 text-muted-foreground" />
                <p className="font-medium text-foreground">Arraste o arquivo aqui ou clique para selecionar</p>
                <p className="text-sm text-muted-foreground">Formatos aceitos: PDF, DOCX, TXT, CSV (máx. 50MB)</p>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5 sm:col-span-2">
              <Label>Título do documento</Label>
              <Input
                value={documentTitle}
                onChange={(e) => setDocumentTitle(e.target.value)}
                placeholder={selectedFile ? selectedFile.name.replace(/\.[^.]+$/, "") : "Ex.: Portaria de comissão avaliadora"}
              />
            </div>
            <div className="space-y-1.5">
              <Label>Autor</Label>
              <Input
                value={documentAuthor}
                onChange={(e) => setDocumentAuthor(e.target.value)}
                placeholder="Ex.: Conselho Superior"
              />
            </div>
            <div className="space-y-1.5">
              <Label>Tipo documental</Label>
              <Select value={documentType} onValueChange={setDocumentType}>
                <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
                <SelectContent>
                  {documentTypeOptions.map((option) => (
                    <SelectItem key={option} value={option}>{option}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>{uploadMode === "version" ? "Nova categoria (opcional)" : "Categoria"}</Label>
              <Select value={category} onValueChange={setCategory}>
                <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="academico">Acadêmico</SelectItem>
                  <SelectItem value="administrativo">Administrativo</SelectItem>
                  <SelectItem value="pesquisa">Pesquisa</SelectItem>
                  <SelectItem value="extensao">Extensão</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Data do documento</Label>
              <Input type="date" value={documentDate} onChange={(e) => setDocumentDate(e.target.value)} />
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              onClick={handleSubmitUpload}
              disabled={
                !uploaded ||
                (uploadMode === "new" && !category) ||
                (uploadMode === "version" && !versionTarget) ||
                uploadMutation.isPending ||
                createVersionMutation.isPending
              }
            >
              {step === "uploading"
                ? "Enviando..."
                : step === "done"
                  ? uploadMode === "version" ? "Enviar outra versão" : "Enviar novo documento"
                  : uploadMode === "version" ? "Registrar versão" : "Validar e enviar"}
            </Button>
            <Button variant="outline" onClick={resetUpload} disabled={!uploaded && !uploadedDocument}>
              Limpar
            </Button>
          </div>

          {step === "validated" && selectedFile && (
            <div className="glass-card p-4 flex items-center gap-3 border-l-4 border-l-success">
              <CheckCircle2 className="h-5 w-5 text-success shrink-0" />
              <div>
                <p className="text-sm font-medium text-foreground">Arquivo pronto para envio</p>
                <p className="text-xs text-muted-foreground">O backend vai validar tipo, tamanho, integridade e então extrair o conteúdo textual.</p>
              </div>
            </div>
          )}
          {step === "done" && (
            <div className="glass-card p-4 flex items-center gap-3 border-l-4 border-l-success">
              <CheckCircle2 className="h-5 w-5 text-success shrink-0" />
              <div>
                <p className="text-sm font-medium text-foreground">
                  {uploadMode === "version" ? "Nova versão registrada" : "Ingestão concluída com sucesso"}
                </p>
                <p className="text-xs text-muted-foreground">
                  {uploadedDocument?.fileName} armazenado com validação concluída, texto extraído e metadados registrados.
                </p>
                <p className="text-xs text-muted-foreground">
                  {uploadedDocument?.title} · {uploadedDocument?.author} · {uploadedDocument?.documentType}
                </p>
                {uploadMode === "version" && uploadedDocument && "version" in uploadedDocument && (
                  <p className="text-xs text-muted-foreground">Versão ativa: {uploadedDocument.version}</p>
                )}
                <p className="text-xs text-muted-foreground">
                  {uploadedDocument?.extractedCharacters ?? 0} caracteres extraídos para processamento e indexação.
                </p>
              </div>
            </div>
          )}
        </TabsContent>

        <TabsContent value="batch" className="mt-4 space-y-4">
          <div
            className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all duration-200 ${
              batchDragOver ? "border-primary bg-accent" : batchFiles.length > 0 ? "border-success bg-success/5" : "border-border hover:border-primary/50"
            }`}
            onDragOver={(e) => { e.preventDefault(); setBatchDragOver(true); }}
            onDragLeave={() => setBatchDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setBatchDragOver(false);
              handleBatchFileSelection(e.dataTransfer.files);
            }}
            onClick={() => batchInputRef.current?.click()}
          >
            <input
              ref={batchInputRef}
              type="file"
              multiple
              accept=".pdf,.docx,.txt,.csv"
              className="hidden"
              onChange={(e) => handleBatchFileSelection(e.target.files)}
            />
            <Upload className="h-10 w-10 text-muted-foreground mx-auto mb-2" />
            <p className="font-medium text-foreground">
              {batchFiles.length > 0 ? `${batchFiles.length} arquivo(s) selecionado(s)` : "Arraste múltiplos arquivos ou clique para selecionar"}
            </p>
            <p className="text-sm text-muted-foreground">Formatos aceitos: PDF, DOCX, TXT, CSV</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label>Autor do lote</Label>
              <Input
                value={batchAuthor}
                onChange={(e) => setBatchAuthor(e.target.value)}
                placeholder="Ex.: Diretoria de Ensino"
              />
            </div>
            <div className="space-y-1.5">
              <Label>Tipo documental do lote</Label>
              <Select value={batchDocumentType} onValueChange={setBatchDocumentType}>
                <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
                <SelectContent>
                  {documentTypeOptions.map((option) => (
                    <SelectItem key={option} value={option}>{option}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Categoria do lote</Label>
              <Select value={batchCategory} onValueChange={setBatchCategory}>
                <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="academico">Acadêmico</SelectItem>
                  <SelectItem value="administrativo">Administrativo</SelectItem>
                  <SelectItem value="pesquisa">Pesquisa</SelectItem>
                  <SelectItem value="extensao">Extensão</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Data dos documentos</Label>
              <Input type="date" value={batchDocumentDate} onChange={(e) => setBatchDocumentDate(e.target.value)} />
            </div>
          </div>

          <div className="flex gap-2">
            <Button onClick={handleSubmitBatchUpload} disabled={batchFiles.length === 0 || !batchCategory || batchUploadMutation.isPending}>
              {batchUploadMutation.isPending ? "Processando lote..." : "Enviar lote"}
            </Button>
            <Button variant="outline" onClick={resetBatchUpload} disabled={batchFiles.length === 0 && !batchResult}>
              Limpar lote
            </Button>
          </div>

          <div className="glass-card p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-foreground">Progresso geral (UC09)</span>
              <span className="text-sm text-muted-foreground">
                {batchResult ? `${Math.round((batchResult.successCount + batchResult.failureCount) / Math.max(batchResult.totalFiles, 1) * 100)}%` : "0%"}
              </span>
            </div>
            <Progress value={batchResult ? ((batchResult.successCount + batchResult.failureCount) / Math.max(batchResult.totalFiles, 1)) * 100 : 0} className="h-2" />
            <p className="text-xs text-muted-foreground mt-2">
              {batchResult
                ? `${batchResult.successCount + batchResult.failureCount} de ${batchResult.totalFiles} documentos processados.`
                : "Selecione os arquivos e envie o lote para processar."}
            </p>
          </div>

          <div className="glass-card overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="text-left p-3 font-medium text-muted-foreground">Arquivo</th>
                  <th className="text-left p-3 font-medium text-muted-foreground">Tamanho</th>
                  <th className="text-left p-3 font-medium text-muted-foreground">Status</th>
                  <th className="text-right p-3 font-medium text-muted-foreground">Ação</th>
                </tr>
              </thead>
              <tbody>
                {(batchResult?.items ?? batchQuery.data.map((file) => ({
                  fileName: file.name,
                  status: file.status,
                  sizeLabel: file.size,
                  message: "",
                }))).map((file, i) => (
                  <tr key={i} className="border-b border-border last:border-0 hover:bg-muted/30 transition-colors">
                    <td className="p-3 flex items-center gap-2">
                      <FileText className="h-4 w-4 text-muted-foreground" />
                      {file.fileName}
                    </td>
                    <td className="p-3 text-muted-foreground">{file.sizeLabel ?? "-"}</td>
                    <td className="p-3">
                      <Badge variant={statusMap[file.status].variant}>
                        {statusMap[file.status].label}
                      </Badge>
                    </td>
                    <td className="p-3 text-right">
                      {file.status === "error" && (
                        <span className="text-xs text-destructive">{file.message || "Falha no processamento"}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </TabsContent>

        <TabsContent value="history" className="mt-4 space-y-4">
          <div className="glass-card overflow-hidden">
            <div className="p-4 border-b border-border bg-muted/50">
              <h3 className="text-sm font-semibold text-foreground">Histórico de Ingestão (UC14)</h3>
              <p className="text-xs text-muted-foreground mt-1">Registro de todas as operações de ingestão para auditoria</p>
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left p-3 font-medium text-muted-foreground">Data</th>
                  <th className="text-left p-3 font-medium text-muted-foreground">Arquivo</th>
                  <th className="text-left p-3 font-medium text-muted-foreground">Tipo</th>
                  <th className="text-left p-3 font-medium text-muted-foreground">Resultado</th>
                  <th className="text-left p-3 font-medium text-muted-foreground">Detalhes</th>
                </tr>
              </thead>
              <tbody>
            {historyQuery.data.map((item, i) => (
                  <tr key={i} className="border-b border-border last:border-0 hover:bg-muted/30 transition-colors">
                    <td className="p-3 text-muted-foreground font-mono text-xs whitespace-nowrap">{item.date}</td>
                    <td className="p-3 text-foreground flex items-center gap-2">
                      <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                      {item.file}
                    </td>
                    <td className="p-3">
                      <Badge variant="secondary">{item.type}</Badge>
                    </td>
                    <td className="p-3">
                      <Badge variant={item.result === "Sucesso" ? "default" : "destructive"}
                        className={item.result === "Sucesso" ? "bg-success hover:bg-success/90" : ""}
                      >
                        {item.result}
                      </Badge>
                    </td>
                    <td className="p-3 text-muted-foreground text-xs">{item.details}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default IngestionPage;
