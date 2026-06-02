# Arquitetura do Frontend (`interface-web`)

## Visão geral

O frontend do IFESDOC é uma SPA em React 18 + TypeScript + Vite voltada para operação administrativa e consulta documental. A arquitetura atual foi desenhada para funcionar em modo híbrido:

- `mock-first`: a maior parte dos módulos continua operando com dados simulados;
- `API real`: a autenticação já possui backend FastAPI disponível, e a camada de serviços já está preparada para migrar os demais módulos.

Na prática, o frontend está organizado em cinco blocos principais:

- bootstrap e infraestrutura de runtime;
- shell da aplicação e roteamento;
- sessão/autenticação;
- acesso a dados por serviços e hooks;
- páginas de negócio e biblioteca de UI.

## Fluxo arquitetural atual

```text
main.tsx
  -> App.tsx
    -> QueryClientProvider
    -> AuthProvider
    -> TooltipProvider / Toasters
    -> BrowserRouter
      -> /login
      -> ProtectedRoute
        -> AppLayout
          -> AppSidebar
          -> AppHeader
          -> Pages
            -> hooks/use-app-query
              -> lib/api/services
                -> lib/api/client
                -> backend real ou mock-data
```

## Stack

- `React 18`: composição de componentes e renderização da SPA.
- `TypeScript`: tipagem dos contratos da interface.
- `Vite`: ambiente de desenvolvimento, build e alias de módulos.
- `React Router DOM`: navegação e proteção de rotas.
- `@tanstack/react-query`: cache, sincronização e ciclo de vida das consultas.
- `Tailwind CSS`: base de estilo utilitário.
- `shadcn/ui` + `Radix UI`: sistema de componentes reutilizáveis.
- `Vitest` + Testing Library: infraestrutura de testes frontend.

## Estrutura de diretórios e função de cada pacote

### Raiz `interface-web/`

- `package.json`: define scripts, dependências de runtime e ferramentas de desenvolvimento.
- `vite.config.ts`: configura o Vite, porta `8080`, HMR e alias `@`.
- `tailwind.config.ts`: define tokens visuais, cores semânticas, animações e tema.
- `postcss.config.js`: integra Tailwind ao processamento CSS.
- `components.json`: configuração do ecossistema `shadcn/ui`.
- `tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json`: configuração TypeScript.
- `eslint.config.js`: lint do projeto.
- `vitest.config.ts`: configuração de testes.
- `index.html`: documento base da SPA.
- `.env.example`: variáveis de ambiente públicas do frontend.
- `.env`: configuração local efetiva da interface.
- `Dockerfile`: container de desenvolvimento do frontend com Node 20 e `npm run dev`.
- `README.md`: guia de execução do módulo.
- `public/`: arquivos estáticos.
- `src/`: código-fonte da aplicação.
- `dist/`: build gerado.
- `node_modules/`: dependências instaladas.

### `public/`

- `favicon.ico`: ícone da aplicação.
- `robots.txt`: instruções para crawlers.
- `placeholder.svg`: asset estático auxiliar.

### `src/`

É o núcleo do frontend.

#### `src/main.tsx`

- ponto de entrada da SPA;
- monta `App` em `#root`;
- executa a aplicação em `StrictMode`.

#### `src/App.tsx`

É o orquestrador global do frontend.

Responsabilidades:

- cria o `QueryClient`;
- injeta `QueryClientProvider`;
- injeta `AuthProvider`;
- injeta `TooltipProvider`, `Toaster` e `Sonner`;
- define as rotas públicas e protegidas;
- aplica `AppLayout` ao shell autenticado.

Rotas atuais:

- `/login`
- `/busca`
- `/resultados`
- `/documento/:id`
- `/ingestao`
- `/indexacao`
- `/metricas`
- `/historico`
- `/usuarios`
- `/configuracoes`

#### `src/index.css`

- CSS global da aplicação;
- concentra variáveis CSS, tokens visuais e classes compartilhadas do layout.

#### `src/App.css`

- CSS complementar da aplicação;
- acomoda ajustes específicos fora da folha global.

### `src/components/`

Pacote de componentes compostos do produto.

#### `src/components/AppLayout.tsx`

- estrutura-base das páginas autenticadas;
- organiza `AppSidebar`, `AppHeader` e a região principal via `Outlet`.

#### `src/components/AppSidebar.tsx`

- navegação lateral da aplicação;
- centraliza menu das áreas funcionais;
- executa logout via `AuthContext`;
- usa `appEnv.appName` como identificação visual da instância.

#### `src/components/AppHeader.tsx`

- cabeçalho superior persistente;
- mostra dados do usuário autenticado;
- oferece busca rápida que redireciona para `/resultados`.

#### `src/components/ProtectedRoute.tsx`

- camada de proteção de rotas;
- bloqueia acesso sem sessão válida;
- trata carregamento inicial da sessão;
- redireciona para `/login`.

#### `src/components/PageState.tsx`

- abstrai estados de carregamento e erro das páginas;
- reduz repetição de componentes de feedback.

#### `src/components/NavLink.tsx`

- utilitário de navegação interna com estilo padronizado.

### `src/components/ui/`

Biblioteca visual reutilizável baseada em `shadcn/ui` e `Radix UI`.

Função arquitetural:

- padronizar os blocos de interface;
- separar páginas de baixo nível visual;
- manter consistência de estilo e comportamento.

Subgrupos lógicos:

- formulários e entrada: `input.tsx`, `textarea.tsx`, `checkbox.tsx`, `radio-group.tsx`, `select.tsx`, `switch.tsx`, `slider.tsx`, `input-otp.tsx`, `form.tsx`, `label.tsx`.
- estrutura e navegação: `tabs.tsx`, `breadcrumb.tsx`, `pagination.tsx`, `menubar.tsx`, `navigation-menu.tsx`, `sidebar.tsx`, `sheet.tsx`, `drawer.tsx`, `resizable.tsx`, `scroll-area.tsx`.
- feedback e overlays: `toast.tsx`, `toaster.tsx`, `sonner.tsx`, `tooltip.tsx`, `alert.tsx`, `alert-dialog.tsx`, `dialog.tsx`, `popover.tsx`, `hover-card.tsx`.
- visualização de dados: `table.tsx`, `card.tsx`, `badge.tsx`, `avatar.tsx`, `progress.tsx`, `skeleton.tsx`, `chart.tsx`, `calendar.tsx`, `carousel.tsx`.
- interação contextual: `command.tsx`, `context-menu.tsx`, `dropdown-menu.tsx`, `accordion.tsx`, `collapsible.tsx`, `toggle.tsx`, `toggle-group.tsx`, `separator.tsx`, `aspect-ratio.tsx`.

Observação:

- `src/components/ui/sidebar.tsx` é infraestrutura de UI genérica;
- `src/components/AppSidebar.tsx` é a aplicação dessa infraestrutura ao domínio IFESDOC.

### `src/contexts/`

#### `src/contexts/AuthContext.tsx`

Camada global de sessão.

Responsabilidades:

- carregar sessão do `localStorage`;
- persistir o resultado do login;
- expor `user`, `isAuthenticated`, `isLoading`, `login` e `logout`;
- integrar a interface com `authService`.

Estado arquitetural atual:

- a sessão é persistida localmente;
- o token JWT retornado pelo backend é armazenado dentro de `SessionUser`;
- ainda não há refresh token nem revalidação automática da sessão em `/auth/me`.

### `src/hooks/`

Pacote de hooks compartilhados.

#### `src/hooks/use-app-query.ts`

- centraliza hooks de leitura com `react-query`;
- encapsula `queryKey`, `queryFn` e políticas de polling/cache;
- expõe hooks por domínio: busca, documento, usuários, ingestão, indexação, métricas, histórico e configurações.

#### `src/hooks/use-toast.ts`

- abstrai o sistema de notificações visuais.

#### `src/hooks/use-mobile.tsx`

- utilitário para comportamento responsivo.

### `src/lib/`

Camada de utilidades e integração.

#### `src/lib/env.ts`

- lê `VITE_API_URL`, `VITE_USE_MOCK_API` e `VITE_APP_NAME`;
- define o modo operacional do frontend.

#### `src/lib/storage.ts`

- centraliza chaves do `localStorage`, como sessão e configurações.

#### `src/lib/utils.ts`

- helpers genéricos leves do frontend.

#### `src/lib/api/`

Camada de acesso a dados da aplicação.

##### `src/lib/api/client.ts`

- wrapper HTTP sobre `fetch`;
- monta URL com query string;
- injeta `Content-Type`;
- aceita token opcional;
- normaliza falhas via `ApiError`.

Observação importante:

- o cliente suporta token Bearer, mas os serviços atuais ainda não injetam o token da sessão automaticamente;
- isso significa que a autenticação real está pronta para login, mas a autorização dos demais endpoints ainda não foi acoplada de ponta a ponta.

##### `src/lib/api/services.ts`

- camada de serviço por domínio;
- concentra o contrato consumido pelas páginas;
- decide entre backend real e dados mockados com base em `VITE_USE_MOCK_API`.

Observação importante:

- o modo mock ainda é o padrão de desenvolvimento (`VITE_USE_MOCK_API=true`);
- a autenticação real do backend já está disponível para login e perfis quando o modo API estiver habilitado;
- outros domínios ainda podem depender de mocks até que as rotas do backend sejam implementadas completamente.

Serviços atuais:

- `authService`
- `searchService`
- `documentService`
- `userService`
- `ingestionService`
- `indexService`
- `metricsService`
- `historyService`
- `settingsService`

Estado arquitetural atual:

- `authService.login()` já aponta para `/api/v1/auth/login`;
- os demais serviços continuam estruturados para REST real, mas dependem de endpoints ainda não implementados ou não integrados.

##### `src/lib/api/mock-data.ts`

- fornece dados simulados para busca, documentos, ingestão, métricas, usuários, histórico e configurações;
- viabiliza desenvolvimento funcional da interface sem backend completo.

### `src/pages/`

Camada de páginas roteáveis.

#### `src/pages/LoginPage.tsx`

- tela pública de autenticação;
- usa `AuthContext`;
- redireciona após login para a rota de origem ou `/busca`.

#### `src/pages/SearchPage.tsx`

- tela principal de consulta;
- captura texto de busca;
- mostra filtros avançados;
- exibe buscas recentes.

#### `src/pages/ResultsPage.tsx`

- lista resultados da consulta;
- lê parâmetros da URL;
- usa `useSearchResults`;
- trata paginação no client-side da rota.

#### `src/pages/DocumentViewPage.tsx`

- detalha um documento;
- mostra metadados, conteúdo e ações como download e reindexação.

#### `src/pages/IngestionPage.tsx`

- representa o fluxo de ingestão;
- combina upload, lote e histórico;
- simula etapas operacionais do pipeline documental.

#### `src/pages/IndexStatusPage.tsx`

- painel de status da indexação;
- mostra progresso, resumo e logs.

#### `src/pages/MetricsPage.tsx`

- dashboard analítico com indicadores e gráficos.

#### `src/pages/HistoryPage.tsx`

- área de auditoria e histórico operacional.

#### `src/pages/UsersPage.tsx`

- gestão de usuários no nível da interface;
- modela cadastro, edição e ativação/inativação.

#### `src/pages/SettingsPage.tsx`

- preferências e parâmetros operacionais do sistema.

#### `src/pages/NotFound.tsx`

- fallback para rotas inexistentes.

#### `src/pages/Index.tsx`

- página residual de template;
- não participa do fluxo principal do produto.

### `src/types/`

#### `src/types/app.ts`

- define os contratos tipados do frontend;
- modela usuário, sessão, busca, documento, ingestão, métricas, histórico e configurações.

Observação:

- `SessionUser` contém `token`, refletindo a integração atual com JWT do backend.

### `src/test/`

- `setup.ts`: bootstrap do ambiente de testes.
- `example.test.ts`: teste inicial de sanidade.

## Relação entre as camadas

### 1. Bootstrap

- `main.tsx` inicializa a SPA;
- `App.tsx` injeta providers e rotas.

### 2. Sessão

- `AuthContext` controla autenticação local;
- `ProtectedRoute` protege o shell autenticado;
- `AppHeader` e `AppSidebar` consomem o estado da sessão.

### 3. Dados

- páginas chamam hooks de `use-app-query`;
- hooks chamam `services.ts`;
- `services.ts` decide entre mock e API real;
- `client.ts` faz o transporte HTTP.

### 4. Apresentação

- `pages/` implementa os casos de uso da interface;
- `components/` organiza o shell do produto;
- `components/ui/` fornece as primitivas visuais reutilizáveis.

## Estado atual da arquitetura frontend

### O que está consolidado

- shell autenticado com rotas protegidas;
- persistência local de sessão;
- camada de serviços centralizada;
- uso de React Query para leitura de dados;
- biblioteca visual reutilizável;
- container de desenvolvimento via `Dockerfile`.

### O que está parcialmente consolidado

- autenticação com backend real já existe para login;
- a sessão é armazenada com JWT, mas ainda sem consumo automático do token nos demais serviços;
- a maior parte dos módulos operacionais ainda depende de mocks.

### Consequência prática

O frontend já tem arquitetura estável para versionamento e evolução incremental. O principal ponto em aberto não é estrutural, e sim de integração: migrar progressivamente os serviços hoje mockados para os endpoints reais do backend.
