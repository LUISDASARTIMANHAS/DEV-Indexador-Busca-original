import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AppLayout } from "@/components/AppLayout";
import { PageLoader } from "@/components/PageState";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { RoleRoute } from "@/components/RoleRoute";
import { AuthProvider } from "@/contexts/AuthContext";

const LoginPage = lazy(() => import("./pages/LoginPage"));
const SearchPage = lazy(() => import("./pages/SearchPage"));
const SearchComparePage = lazy(() => import("./pages/SearchComparePage"));
const ResultsPage = lazy(() => import("./pages/ResultsPage"));
const DocumentViewPage = lazy(() => import("./pages/DocumentViewPage"));
const IngestionPage = lazy(() => import("./pages/IngestionPage"));
const IndexStatusPage = lazy(() => import("./pages/IndexStatusPage"));
const MetricsPage = lazy(() => import("./pages/MetricsPage"));
const HistoryPage = lazy(() => import("./pages/HistoryPage"));
const UsersPage = lazy(() => import("./pages/UsersPage"));
const SettingsPage = lazy(() => import("./pages/SettingsPage"));
const NotFound = lazy(() => import("./pages/NotFound"));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 15000,
    },
  },
});

const App = () => (
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Suspense fallback={<PageLoader label="Carregando interface..." />}>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/" element={<Navigate to="/busca" replace />} />
              <Route element={<ProtectedRoute />}>
                <Route element={<AppLayout />}>
                  <Route path="/busca" element={<SearchPage />} />
                  <Route path="/comparar-busca" element={<SearchComparePage />} />
                  <Route path="/resultados" element={<ResultsPage />} />
                  <Route path="/documento/:id" element={<DocumentViewPage />} />
                  <Route path="/historico" element={<HistoryPage />} />
                  <Route element={<RoleRoute allow="admin" />}>
                    <Route path="/ingestao" element={<IngestionPage />} />
                    <Route path="/indexacao" element={<IndexStatusPage />} />
                    <Route path="/metricas" element={<MetricsPage />} />
                    <Route path="/usuarios" element={<UsersPage />} />
                    <Route path="/configuracoes" element={<SettingsPage />} />
                  </Route>
                </Route>
              </Route>
              <Route path="*" element={<NotFound />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </TooltipProvider>
    </AuthProvider>
  </QueryClientProvider>
);

export default App;
