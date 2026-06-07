import { useMemo, useState } from "react";
import { GitCompareArrows, Search } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PageError, PageLoader } from "@/components/PageState";
import { useSearchCompare } from "@/hooks/use-app-query";
import { HighlightedSnippet } from "@/pages/ResultsPage";
import type { SearchMode, SearchResult } from "@/types/app";

const availableModes: { value: SearchMode; label: string }[] = [
  { value: "frequency", label: "Frequência" },
  { value: "bm25", label: "BM25" },
  { value: "postgres_fts", label: "PostgreSQL FTS" },
  { value: "hybrid_postgres", label: "Híbrida PostgreSQL" },
];

const formatScore = (value?: number) =>
  typeof value === "number" && Number.isFinite(value) ? value.toFixed(3) : "0.000";

const isUnavailable = (value: unknown): value is { available: false; reason: string } =>
  !!value && typeof value === "object" && "available" in value && (value as { available: boolean }).available === false;

const SearchComparePage = () => {
  const [input, setInput] = useState("estágio supervisionado");
  const [submittedQuery, setSubmittedQuery] = useState("estágio supervisionado");
  const [selectedModes, setSelectedModes] = useState<SearchMode[]>(["frequency", "bm25", "postgres_fts", "hybrid_postgres"]);
  const [limit, setLimit] = useState(5);
  const filters = useMemo(() => ({ modes: selectedModes, limit }), [selectedModes, limit]);
  const { data, isLoading, isError, refetch } = useSearchCompare(submittedQuery, filters);

  const toggleMode = (mode: SearchMode) => {
    setSelectedModes((current) =>
      current.includes(mode)
        ? current.filter((item) => item !== mode)
        : [...current, mode],
    );
  };

  const submit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (input.trim()) {
      setSubmittedQuery(input.trim());
    }
  };

  return (
    <div className="mx-auto max-w-6xl animate-fade-in">
      <div className="mb-6 flex items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-foreground">Comparação de busca</h1>
          <p className="text-sm text-muted-foreground">
            Compare frequência, BM25, PostgreSQL FTS e busca híbrida sobre a mesma consulta.
          </p>
        </div>
        <GitCompareArrows className="h-5 w-5 text-primary" />
      </div>

      <form onSubmit={submit} className="mb-5 space-y-4 border-b border-border pb-5">
        <div className="flex flex-col gap-3 md:flex-row">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              className="pl-9"
              placeholder="Consulta para comparar"
            />
          </div>
          <div className="flex items-center gap-2">
            <Label htmlFor="compare-limit" className="text-xs text-muted-foreground">Limite</Label>
            <Input
              id="compare-limit"
              type="number"
              min={1}
              max={20}
              value={limit}
              onChange={(event) => setLimit(Number(event.target.value))}
              className="w-20"
            />
            <Button type="submit">Comparar</Button>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {availableModes.map((mode) => (
            <Button
              key={mode.value}
              type="button"
              variant={selectedModes.includes(mode.value) ? "default" : "outline"}
              size="sm"
              onClick={() => toggleMode(mode.value)}
            >
              {mode.label}
            </Button>
          ))}
        </div>
      </form>

      {isLoading && <PageLoader label="Comparando estratégias..." />}
      {isError && <PageError title="Falha ao comparar estratégias." onRetry={() => refetch()} />}

      {data && !isLoading && !isError && (
        <>
          <div className="mb-4 flex flex-wrap gap-2">
            {data.analysis?.terms.map((term) => (
              <Badge key={term} variant="secondary">Termo: {term}</Badge>
            ))}
            {data.summary.best_mode_by_top_score && (
              <Badge variant="outline">Maior topo: {data.summary.best_mode_by_top_score}</Badge>
            )}
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2 xl:grid-cols-4">
            {data.compared_modes.map((mode) => {
              const modeResult = data.results_by_mode[mode];
              const label = availableModes.find((item) => item.value === mode)?.label ?? mode;
              return (
                <section key={mode} className="min-w-0 rounded-lg border border-border bg-card p-4">
                  <div className="mb-3 flex items-center justify-between gap-2">
                    <h2 className="text-sm font-semibold text-foreground">{label}</h2>
                    <Badge variant="outline">{mode}</Badge>
                  </div>

                  {isUnavailable(modeResult) ? (
                    <p className="text-sm text-muted-foreground">{modeResult.reason}</p>
                  ) : (
                    <div className="space-y-3">
                      {(modeResult as SearchResult[]).slice(0, limit).map((item, index) => (
                        <article key={`${mode}-${item.id}`} className="rounded-md border border-border p-3">
                          <div className="mb-1 flex items-start justify-between gap-2">
                            <h3 className="line-clamp-2 text-sm font-medium text-foreground">
                              {index + 1}. {item.title}
                            </h3>
                            <Badge variant="secondary">{formatScore(item.finalScore ?? item.score)}</Badge>
                          </div>
                          <p className="line-clamp-3 text-xs text-muted-foreground [&_mark]:highlight-term [&_mark]:bg-transparent">
                            <HighlightedSnippet value={item.snippet || ""} />
                          </p>
                          <div className="mt-2 flex flex-wrap gap-1 text-xs">
                            {item.postgresScore !== undefined && <Badge variant="outline">PG {formatScore(item.postgresScore)}</Badge>}
                            {item.secondaryScore !== undefined && <Badge variant="outline">Sec {formatScore(item.secondaryScore)}</Badge>}
                            <Badge variant="outline">{item.documentType}</Badge>
                          </div>
                        </article>
                      ))}
                    </div>
                  )}
                </section>
              );
            })}
          </div>

          <div className="mt-5 rounded-lg border border-border bg-card p-4">
            <h2 className="mb-2 text-sm font-semibold text-foreground">Notas</h2>
            <ul className="space-y-1 text-sm text-muted-foreground">
              {data.summary.notes.map((note) => (
                <li key={note}>{note}</li>
              ))}
            </ul>
          </div>
        </>
      )}
    </div>
  );
};

export default SearchComparePage;
