import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useDocument, useDocumentVersions, useSearchResults } from "@/hooks/use-app-query";
import ResultsPage from "./ResultsPage";

vi.mock("@/hooks/use-app-query", () => ({
  useDocument: vi.fn(),
  useDocumentVersions: vi.fn(),
  useSearchResults: vi.fn(),
}));

const result = {
  id: 7,
  title: "Resolucao institucional",
  snippet: 'Trecho <script>alert("xss")</script> com <mark>resolução</mark> relevante.',
  category: "Administrativo",
  type: "TXT",
  documentType: "Resolucao",
  author: "Conselho",
  fileName: "resolucao.txt",
  mimeType: "text/plain",
  size: "2 KB",
  date: "2026-05-20",
  relevance: 98,
};

const preview = {
  id: 7,
  title: "Resolucao institucional",
  displayTitle: "Resolucao institucional",
  fileName: "resolucao.txt",
  category: "Administrativo",
  type: "TXT",
  documentType: "Resolucao",
  date: "2026-05-20",
  author: "Conselho",
  uploadedBy: "Administrador",
  format: "TXT",
  mimeType: "text/plain",
  pages: 1,
  version: 1,
  indexedAt: "2026-05-20T10:00:00",
  sizeBytes: 2048,
  size: "2 KB",
  hash: "hash",
  content: "Conteudo extraido para consulta rapida.",
  formattedContent: "Conteudo extraido para consulta rapida.",
  extractedCharacters: 37,
};

describe("ResultsPage", () => {
  beforeEach(() => {
    vi.mocked(useSearchResults).mockReturnValue({
      data: {
        query: "resolucao",
        total: 1,
        page: 1,
        perPage: 20,
        totalPages: 1,
        responseTimeMs: 4,
        items: [result],
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as never);
    vi.mocked(useDocument).mockReturnValue({
      data: preview,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as never);
    vi.mocked(useDocumentVersions).mockReturnValue({
      data: [
        { version: 2, createdAt: "2026-05-21T10:00:00", active: true },
        { version: 1, createdAt: "2026-05-20T10:00:00", active: false },
      ],
      isLoading: false,
    } as never);
  });

  it("renders highlighted snippets without mounting injected tags and opens a quick preview", () => {
    const { container } = render(
      <MemoryRouter
        initialEntries={["/resultados?q=resolucao"]}
        future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
      >
        <Routes>
          <Route path="/resultados" element={<ResultsPage />} />
        </Routes>
      </MemoryRouter>,
    );

    const marked = container.querySelector("mark");
    expect(marked).toHaveTextContent("resolução");
    expect(container.querySelector("script")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Versões" }));

    const dialog = screen.getByRole("dialog");
    expect(within(dialog).getByText("Conteudo extraido para consulta rapida.")).toBeInTheDocument();
    expect(within(dialog).getByRole("combobox", { name: "Versão exibida" })).toBeInTheDocument();
    expect(within(dialog).getByRole("button", { name: "Abrir documento" })).toBeEnabled();
  });
});
