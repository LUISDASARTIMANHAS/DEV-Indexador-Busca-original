import { useNavigate } from "react-router-dom";
import {
  BarChart3,
  Bell,
  Clock,
  Database,
  FileUp,
  Search,
  Settings,
  SlidersHorizontal,
  User,
  Users,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useAuth } from "@/contexts/AuthContext";
import { useNotifications } from "@/hooks/use-app-query";
import { appEnv } from "@/lib/env";
import { notificationService } from "@/lib/api/services";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useMemo, useRef, useState } from "react";
import type { AppNotification } from "@/types/app";

type QuickSearchItem = {
  title: string;
  description: string;
  path: string;
  keywords: string[];
  adminOnly?: boolean;
  icon: typeof Search;
};

const quickSearchItems: QuickSearchItem[] = [
  {
    title: "Busca",
    description: "Pesquisar documentos indexados",
    path: "/busca",
    keywords: ["busca", "pesquisa", "documentos", "consulta"],
    icon: Search,
  },
  {
    title: "Ingestão",
    description: "Enviar documentos individuais ou em lote",
    path: "/ingestao",
    keywords: ["ingestao", "upload", "documento", "lote", "arquivo"],
    adminOnly: true,
    icon: FileUp,
  },
  {
    title: "Indexação",
    description: "Status, consistência e reindexação",
    path: "/indexacao",
    keywords: ["indexacao", "indice", "reindexacao", "status", "consistencia"],
    adminOnly: true,
    icon: Database,
  },
  {
    title: "Métricas",
    description: "Indicadores de busca e documentos",
    path: "/metricas",
    keywords: ["metricas", "indicadores", "dashboard", "relatorios"],
    adminOnly: true,
    icon: BarChart3,
  },
  {
    title: "Histórico",
    description: "Consultar ações e eventos do sistema",
    path: "/historico",
    keywords: ["historico", "logs", "auditoria", "eventos"],
    icon: Clock,
  },
  {
    title: "Gestão de Usuários",
    description: "Criar e alterar usuários",
    path: "/usuarios",
    keywords: ["usuarios", "gestao", "admin", "permissoes", "perfil"],
    adminOnly: true,
    icon: Users,
  },
  {
    title: "Configurações",
    description: "Ajustar parâmetros gerais do sistema",
    path: "/configuracoes",
    keywords: ["configuracoes", "ajustes", "preferencias"],
    adminOnly: true,
    icon: Settings,
  },
  {
    title: "Nome da instância",
    description: "Configuração geral da identidade do sistema",
    path: "/configuracoes#instanceName",
    keywords: ["nome", "instancia", "ifesdoc", "geral"],
    adminOnly: true,
    icon: SlidersHorizontal,
  },
  {
    title: "URL base da API",
    description: "Configurar endereço do backend",
    path: "/configuracoes#apiBaseUrl",
    keywords: ["api", "url", "backend", "base"],
    adminOnly: true,
    icon: SlidersHorizontal,
  },
  {
    title: "Indexação automática",
    description: "Ativar indexação após upload",
    path: "/configuracoes#autoIndexing",
    keywords: ["indexacao automatica", "upload", "automatico"],
    adminOnly: true,
    icon: SlidersHorizontal,
  },
  {
    title: "OCR habilitado",
    description: "Reconhecimento óptico em documentos digitalizados",
    path: "/configuracoes#ocrEnabled",
    keywords: ["ocr", "digitalizado", "reconhecimento"],
    adminOnly: true,
    icon: SlidersHorizontal,
  },
  {
    title: "Tamanho máximo de arquivo",
    description: "Limite de upload em MB",
    path: "/configuracoes#maxFileSizeMb",
    keywords: ["tamanho", "arquivo", "upload", "limite", "mb"],
    adminOnly: true,
    icon: SlidersHorizontal,
  },
  {
    title: "Notificações por e-mail",
    description: "Alertas de erros de indexação",
    path: "/configuracoes#emailNotifications",
    keywords: ["email", "notificacao", "alerta", "erro"],
    adminOnly: true,
    icon: SlidersHorizontal,
  },
  {
    title: "Relatório semanal",
    description: "Resumo periódico de atividades",
    path: "/configuracoes#weeklyReport",
    keywords: ["relatorio", "semanal", "resumo", "atividades"],
    adminOnly: true,
    icon: SlidersHorizontal,
  },
];

const notificationDateFormatter = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
});

const notificationTypeClasses: Record<AppNotification["type"], string> = {
  info: "bg-info",
  success: "bg-success",
  warning: "bg-warning",
  error: "bg-destructive",
};

const formatNotificationDate = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return notificationDateFormatter.format(date);
};

const formatNotificationOrigin = (origin: string) =>
  origin.startsWith("admin:") ? "Administrador" : "IFESDOC";

export function AppHeader() {
  const navigate = useNavigate();
  const { user, isAdmin } = useAuth();
  const [quickSearch, setQuickSearch] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const blurTimeout = useRef<number | null>(null);
  const queryClient = useQueryClient();
  const notificationsQuery = useNotifications(!!user);
  const notifications = notificationsQuery.data ?? [];
  const unreadCount = notifications.filter((notification) => !notification.read).length;
  const unreadLabel = unreadCount > 9 ? "9+" : String(unreadCount);
  const unreadDescription =
    unreadCount === 1 ? "1 mensagem não lida" : `${unreadCount} mensagens não lidas`;
  const unreadAriaLabel =
    unreadCount === 1 ? "1 notificação não lida" : `${unreadCount} notificações não lidas`;
  const markAsReadMutation = useMutation({
    mutationFn: notificationService.markAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
  const markAllAsReadMutation = useMutation({
    mutationFn: notificationService.markAllAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const quickResults = useMemo(() => {
    const query = quickSearch.trim().toLowerCase();
    if (!query) {
      return [];
    }

    return quickSearchItems
      .filter((item) => !item.adminOnly || isAdmin)
      .map((item) => {
        const haystack = [item.title, item.description, ...item.keywords].join(" ").toLowerCase();
        const title = item.title.toLowerCase();
        let score = 0;
        if (title === query) {
          score += 100;
        }
        if (title.includes(query)) {
          score += 50;
        }
        if (haystack.includes(query)) {
          score += 20;
        }
        return { item, score };
      })
      .filter((result) => result.score > 0)
      .sort((left, right) => right.score - left.score)
      .slice(0, 6)
      .map((result) => result.item);
  }, [isAdmin, quickSearch]);

  const navigateToItem = (item: QuickSearchItem) => {
    navigate(item.path);
    setQuickSearch("");
    setIsOpen(false);
  };

  const handleQuickSearch = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!quickSearch.trim()) {
      return;
    }

    if (quickResults[0]) {
      navigateToItem(quickResults[0]);
      return;
    }

    navigate(`/resultados?q=${encodeURIComponent(quickSearch.trim())}`);
    setQuickSearch("");
    setIsOpen(false);
  };

  const handleNotificationClick = (notification: AppNotification) => {
    if (!notification.read) {
      markAsReadMutation.mutate(notification.id);
    }
  };

  return (
    <header className="h-16 bg-card border-b border-border flex items-center justify-between px-6 shrink-0">
      <form onSubmit={handleQuickSearch} className="flex items-center gap-4 flex-1 max-w-xl">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            value={quickSearch}
            onChange={(event) => {
              setQuickSearch(event.target.value);
              setIsOpen(true);
            }}
            onFocus={() => setIsOpen(true)}
            onBlur={() => {
              blurTimeout.current = window.setTimeout(() => setIsOpen(false), 120);
            }}
            placeholder="Buscar menus, configurações ou documentos..."
            className="pl-9 h-9 bg-muted border-0"
          />
          {isOpen && quickSearch.trim() && (
            <div className="absolute left-0 right-0 top-11 z-50 overflow-hidden rounded-xl border border-border bg-card shadow-lg">
              {quickResults.length > 0 ? (
                <div className="p-2">
                  {quickResults.map((item) => (
                    <button
                      key={item.path}
                      type="button"
                      onMouseDown={(event) => event.preventDefault()}
                      onClick={() => navigateToItem(item)}
                      className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left hover:bg-muted"
                    >
                      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                        <item.icon className="h-4 w-4" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-foreground">{item.title}</p>
                        <p className="truncate text-xs text-muted-foreground">{item.description}</p>
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <button
                  type="submit"
                  onMouseDown={(event) => event.preventDefault()}
                  className="flex w-full items-center gap-3 p-4 text-left hover:bg-muted"
                >
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <Search className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">Buscar documentos por “{quickSearch.trim()}”</p>
                    <p className="text-xs text-muted-foreground">Nenhum menu ou configuração encontrado.</p>
                  </div>
                </button>
              )}
            </div>
          )}
        </div>
      </form>

      <div className="flex items-center gap-2">
        <Popover>
          <PopoverTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="relative"
              aria-label={unreadCount > 0 ? unreadAriaLabel : "Notificações"}
            >
              <Bell className="h-4.5 w-4.5 text-muted-foreground" />
              {unreadCount > 0 && (
                <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] font-semibold leading-none text-destructive-foreground">
                  {unreadLabel}
                </span>
              )}
            </Button>
          </PopoverTrigger>
          <PopoverContent align="end" className="w-80 p-0">
            <div className="flex items-center justify-between gap-3 p-4">
              <div>
                <p className="text-sm font-semibold text-foreground">Notificações</p>
                <p className="text-xs text-muted-foreground">
                  {unreadCount > 0 ? unreadDescription : "Nenhuma mensagem pendente"}
                </p>
              </div>
              {unreadCount > 0 && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  disabled={markAllAsReadMutation.isPending}
                  onClick={() => markAllAsReadMutation.mutate()}
                >
                  Marcar lidas
                </Button>
              )}
            </div>

            <div className="border-t border-border">
              {notificationsQuery.isLoading ? (
                <p className="p-4 text-sm text-muted-foreground">Carregando mensagens...</p>
              ) : notificationsQuery.isError ? (
                <div className="p-4">
                  <p className="text-sm font-medium text-foreground">Não foi possível carregar.</p>
                  <button
                    type="button"
                    onClick={() => notificationsQuery.refetch()}
                    className="mt-1 text-xs font-medium text-primary hover:underline"
                  >
                    Tentar novamente
                  </button>
                </div>
              ) : notifications.length > 0 ? (
                <ScrollArea className="max-h-80">
                  <div className="p-2">
                    {notifications.map((notification) => (
                      <button
                        key={notification.id}
                        type="button"
                        onClick={() => handleNotificationClick(notification)}
                        className={`flex w-full gap-3 rounded-md px-3 py-2.5 text-left transition-colors hover:bg-muted ${
                          notification.read ? "opacity-75" : "bg-muted/60"
                        }`}
                      >
                        <span
                          className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${
                            notification.read
                              ? "bg-border"
                              : notificationTypeClasses[notification.type]
                          }`}
                        />
                        <span className="min-w-0 flex-1">
                          <span className="block text-sm font-medium leading-snug text-foreground">
                            {notification.title}
                          </span>
                          <span className="mt-1 block text-xs leading-relaxed text-muted-foreground">
                            {notification.message}
                          </span>
                          <span className="mt-1.5 block text-[11px] text-muted-foreground">
                            {formatNotificationDate(notification.createdAt)} · {formatNotificationOrigin(notification.origin)}
                          </span>
                        </span>
                      </button>
                    ))}
                  </div>
                </ScrollArea>
              ) : (
                <div className="p-4 text-sm text-muted-foreground">Sem mensagens no momento.</div>
              )}
            </div>
          </PopoverContent>
        </Popover>

        <div className="flex items-center gap-3 ml-2 pl-4 border-l border-border">
          <div className="text-right hidden sm:block">
            <p className="text-sm font-medium leading-none">{user?.name || appEnv.appName}</p>
            <p className="text-xs text-muted-foreground">{user?.email || "sem sessão"}</p>
          </div>
          <div className="h-9 w-9 rounded-full bg-primary flex items-center justify-center">
            <User className="h-4 w-4 text-primary-foreground" />
          </div>
        </div>
      </div>
    </header>
  );
}
