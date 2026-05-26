import { useQuery } from "@tanstack/react-query";
import {
  documentService,
  historyService,
  indexService,
  ingestionService,
  metricsService,
  notificationService,
  searchService,
  settingsService,
  userService,
} from "@/lib/api/services";
import type { SearchFilters, SearchHistoryFilters } from "@/types/app";
import type { MetricsReportFilters } from "@/types/app";

export const useRecentSearches = () =>
  useQuery({
    queryKey: ["recent-searches"],
    queryFn: () => searchService.recentSearches(),
  });

export const useSearchResults = (query: string, filters: SearchFilters) =>
  useQuery({
    queryKey: ["search-results", query, filters],
    queryFn: () => searchService.search(query, filters),
    enabled: !!query.trim(),
  });

export const useSearchHistory = (filters: SearchHistoryFilters) =>
  useQuery({
    queryKey: ["search-history", filters],
    queryFn: () => searchService.history(filters),
  });

export const useDocument = (id: number, version?: number) =>
  useQuery({
    queryKey: ["document", id, version ?? "active"],
    queryFn: () => documentService.getById(id, version),
    enabled: Number.isFinite(id),
  });

export const useDocumentVersions = (id: number) =>
  useQuery({
    queryKey: ["document-versions", id],
    queryFn: () => documentService.versions(id),
    enabled: Number.isFinite(id),
  });

export const useUsers = () =>
  useQuery({
    queryKey: ["users"],
    queryFn: () => userService.list(),
  });

export const useIngestionBatch = () =>
  useQuery({
    queryKey: ["ingestion-batch"],
    queryFn: () => ingestionService.batchFiles(),
  });

export const useIngestionHistory = () =>
  useQuery({
    queryKey: ["ingestion-history"],
    queryFn: () => ingestionService.history(),
  });

export const useIndexStatus = () =>
  useQuery({
    queryKey: ["index-status"],
    queryFn: () => indexService.status(),
    refetchInterval: 30000,
  });

export const useMetrics = () =>
  useQuery({
    queryKey: ["metrics"],
    queryFn: () => metricsService.snapshot(),
  });

export const useMetricsReport = (filters: MetricsReportFilters) =>
  useQuery({
    queryKey: ["metrics-report", filters],
    queryFn: () => metricsService.report(filters),
  });

export const useMetricCalculations = (limit = 10) =>
  useQuery({
    queryKey: ["metric-calculations", limit],
    queryFn: () => metricsService.calculations(limit),
  });

export const useHistory = (enabled = true) =>
  useQuery({
    queryKey: ["history"],
    queryFn: () => historyService.list(),
    enabled,
  });

export const useNotifications = (enabled = true) =>
  useQuery({
    queryKey: ["notifications"],
    queryFn: () => notificationService.list(),
    enabled,
    refetchInterval: 30000,
  });

export const useSettings = () =>
  useQuery({
    queryKey: ["settings"],
    queryFn: () => settingsService.get(),
  });
