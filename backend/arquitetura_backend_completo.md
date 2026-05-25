# Arquitetura do Backend Completo (`backend`)

## Visão geral

O backend do IFESDOC agora possui uma arquitetura híbrida entre:

- um núcleo principal em `backend/app`, já com API FastAPI, autenticação JWT, integração com PostgreSQL via SQLAlchemy e bootstrap de infraestrutura;
- dois módulos de pipeline em `backend/pipeline_indexador` e `backend/pipeline_busca`, mantidos como implementações separadas de indexação e busca em memória.

Em relação ao estado anterior, houve uma evolução concreta do backend principal:

- autenticação real foi implementada;
- o domínio `User` já está mapeado com SQLAlchemy;
- a API `v1` já possui rotas de autenticação;
- dependências de segurança e sessão foram adicionadas;
- o schema relacional do sistema foi formalizado em SQL.

Ao mesmo tempo, o backend ainda está em transição:

- a parte de autenticação já está integrada;
- os demais domínios continuam parcialmente apenas modelados na estrutura do banco ou previstos pela arquitetura do frontend;
- os pipelines de busca/indexação ainda estão desacoplados da API principal.

## Visão arquitetural macro

```text
Frontend (interface-web)
  -> /api/v1/auth/login
  -> futuramente /api/v1/search, /documents, /users, /metrics, ...

backend/app
  -> FastAPI
  -> core (config, database, dependencies, security)
  -> api/v1 (auth)
  -> services (auth)
  -> repositories (user)
  -> domain (user)
  -> schemas (auth)

docker/postgres/init
  -> schema SQL relacional do sistema
  -> seed do usuário administrador

backend/pipeline_indexador
  -> indexação em memória

backend/pipeline_busca
  -> busca em memória
```

## Estrutura da pasta `backend/`

- `backend/app/`: backend principal da aplicação.
- `backend/pipeline_indexador/`: prova de conceito do pipeline de indexação.
- `backend/pipeline_busca/`: prova de conceito do pipeline de busca.
- `backend/tests/`: testes do backend principal.
- `backend/Dockerfile`: container da API FastAPI.

## 1. Backend principal: `backend/app/`

Essa pasta representa a aplicação principal que o frontend deve consumir. A arquitetura vigente segue uma combinação de:

- arquitetura em camadas;
- Service Layer;
- Repository Pattern;
- autenticação baseada em JWT;
- ORM com SQLAlchemy.

## Estrutura e função de cada diretório/pacote

### `backend/app/main.py`

É o ponto de entrada efetivo da API.

Responsabilidades:

- cria a aplicação FastAPI;
- define `lifespan` para tentativa de criação das tabelas do ORM;
- registra `CORSMiddleware`;
- inclui `api_router` em `/api/v1`;
- padroniza respostas de erro para:
  - exceções HTTP;
  - validação de request;
  - indisponibilidade do banco;
  - schema de banco não inicializado;
- expõe `GET /`.

Função arquitetural:

- bootstrap da aplicação web;
- composição final das camadas internas;
- adaptação do backend às condições de infraestrutura.

Observação:

- `main.py` já não é mais apenas um stub;
- ele agora conecta configuração, banco, domínio e roteamento.

### `backend/app/api/`

Camada HTTP do sistema.

#### `backend/app/api/v1/`

Pacote de versionamento da API.

##### `router.py`

- agregador das rotas versionadas;
- atualmente inclui `auth_router`.

##### `auth_routes.py`

- módulo HTTP de autenticação;
- expõe:
  - `POST /api/v1/auth/login`
  - `GET /api/v1/auth/me`

Responsabilidades:

- receber `LoginRequest`;
- usar `AuthService` com `Session`;
- resolver dependência de usuário autenticado via `get_current_user`;
- serializar respostas por `TokenResponse` e `AuthenticatedUserResponse`.

##### `__init__.py`

- marcador de pacote.

Estado arquitetural atual:

- a API `v1` já existe funcionalmente, mas ainda focada em autenticação;
- rotas de busca, documentos, ingestão, métricas e histórico ainda não foram movidas para esta camada.

### `backend/app/core/`

Infraestrutura transversal do backend principal.

#### `config.py`

- carrega variáveis de ambiente a partir da raiz do projeto;
- usa `BaseSettings` de `pydantic-settings`;
- define:
  - `DATABASE_URL`
  - `SECRET_KEY`
  - `ALGORITHM`
  - `ACCESS_TOKEN_EXPIRE_MINUTES`
  - `BACKEND_CORS_ORIGINS`

Função arquitetural:

- centralizar configuração e ambiente;
- evitar parâmetros espalhados em múltiplos módulos.

#### `database.py`

- cria `engine` SQLAlchemy com `DATABASE_URL`;
- cria `SessionLocal`;
- define `Base = declarative_base()`;
- expõe `get_db()` para injeção de sessão.

Função arquitetural:

- padronizar acesso ao banco;
- sustentar ORM e dependências do FastAPI.

#### `security.py`

- encapsula hashing de senha com `passlib/bcrypt`;
- verifica senha;
- cria JWT com `python-jose`;
- decodifica e valida token.

Função arquitetural:

- isolar mecanismos de segurança;
- evitar lógica de token e hash dentro das rotas.

#### `dependencies.py`

- define a dependência `get_current_user`;
- lê o Bearer token com `HTTPBearer`;
- decodifica o JWT;
- resolve `sub` para `user_id`;
- consulta o usuário no banco;
- valida existência e status ativo.

Função arquitetural:

- concentrar autenticação/autorização básica reutilizável pela API.

#### `__init__.py`

- marcador de pacote.

### `backend/app/domain/`

Pacote do modelo de domínio persistido.

#### `user.py`

Modelo SQLAlchemy da tabela `usuario`.

Campos atualmente mapeados:

- `cod_usuario`
- `nome`
- `login`
- `email`
- `senha_hash`
- `perfil`
- `ativo`

Função arquitetural:

- representar o usuário no backend principal;
- servir de base para repositórios, serviços e dependências de autenticação.

#### `__init__.py`

- marcador de pacote.

Estado atual:

- o domínio já começou a ser implementado, mas ainda só para usuários;
- os demais agregados do sistema continuam apenas no schema SQL ou previstos pela arquitetura.

### `backend/app/repositories/`

Camada de acesso a dados do backend principal.

#### `user_repository.py`

- encapsula consultas de usuário com SQLAlchemy;
- expõe:
  - `get_by_login`
  - `get_by_email`
  - `get_by_login_or_email`
  - `get_by_id`

Função arquitetural:

- manter queries de usuário fora de `AuthService`;
- reduzir acoplamento entre serviço e ORM.

#### `postgresql_driver.py`

- driver alternativo de acesso ao PostgreSQL via `psycopg2`;
- fornece `conectar()` e `executar()`.

Leitura arquitetural:

- este arquivo representa uma camada de acesso de baixo nível paralela ao SQLAlchemy;
- hoje ele não está integrado ao fluxo principal da API;
- funciona mais como utilitário/manual ou resquício de uma abordagem anterior.

#### `__init__.py`

- marcador de pacote.

### `backend/app/services/`

Camada de caso de uso do backend principal.

#### `auth_service.py`

- implementa o fluxo de autenticação;
- consulta usuário via `UserRepository`;
- valida senha com `verify_password`;
- recusa usuários inexistentes ou inativos;
- cria JWT com `create_access_token`;
- converte `perfil` técnico para papel funcional com `_map_role`.

Retorno atual do login:

- id
- nome
- login
- email
- role
- active
- token
- access_token
- token_type

Função arquitetural:

- encapsular a regra de autenticação;
- manter `auth_routes.py` fina.

#### `__init__.py`

- marcador de pacote.

Estado atual:

- `auth_service.py` é a primeira service layer consolidada do backend principal.

### `backend/app/schemas/`

Camada de contratos externos da API.

#### `auth_schema.py`

Define os modelos Pydantic de autenticação:

- `LoginRequest`
- `TokenResponse`
- `AuthenticatedUserResponse`

Funções:

- validar request de login;
- impor a presença de `login` ou `email` com `model_validator`;
- padronizar serialização da resposta.

#### `__init__.py`

- marcador de pacote.

Estado atual:

- os schemas reais já começaram pela autenticação;
- os contratos dos demais domínios ainda não existem no backend principal.

### `backend/app/utils/`

Pacote auxiliar.

Arquivos:

- `pagination.py`: vazio.
- `text_processing.py`: vazio.
- `time_utils.py`: residual/minimal.
- `__init__.py`: marcador de pacote.

Leitura arquitetural:

- o pacote existe como ponto de expansão, mas ainda não participa do fluxo principal.

### `backend/app/strategies/`

- pacote reservado para estratégias de ranking e busca;
- hoje contém apenas `__init__.py`.

### `backend/app/pipeline/`

- pacote reservado para pipelines integrados ao backend principal;
- hoje contém apenas `__init__.py`.

### `backend/app/adapters/`

- pacote reservado para integrações de parsing e armazenamento;
- hoje contém apenas `__init__.py`.

### `backend/app/exceptions/`

- pacote reservado para exceções específicas do domínio/aplicação;
- hoje contém apenas `__init__.py`.

## 2. Modelagem relacional e bootstrap do banco

Embora esteja fora de `backend/app`, a pasta `docker/postgres/init/` agora é parte central da arquitetura backend porque define o modelo relacional real do sistema.

### `docker/postgres/init/01_schema.sql`

Script de criação do schema principal do IFESDOC.

Tabelas modeladas:

- `usuario`
- `categoria_documento`
- `status_ingestao`
- `tipo_campo`
- `calculo_metricas`
- `documento`
- `documentos_invalidos`
- `historico_busca`
- `historico_administrativo`
- `historico_documento`
- `historico_ingestao`
- `termo`
- `campo_documento`
- `historico_indexacao`
- `indice_invertido`
- `feedback_relevancia`

Papel arquitetural:

- formaliza o domínio de usuários, documentos, ingestão, histórico, indexação, métricas e relevância;
- mostra a arquitetura de persistência alvo do sistema;
- revela que o backend foi modelado para ir além da autenticação, mesmo que o código Python ainda não tenha todas essas entidades implementadas.

### `docker/postgres/init/02_admin.sql`

- insere um usuário administrador padrão;
- usa `ON CONFLICT (login) DO NOTHING`.

Papel arquitetural:

- disponibiliza bootstrap mínimo do sistema autenticável;
- permite que a API de login funcione sem cadastro manual inicial.

## 3. Infraestrutura de execução do backend principal

### `backend/Dockerfile`

Container de execução da API.

Responsabilidades:

- usa `python:3.10-slim`;
- instala dependências de compilação e `libpq-dev`;
- instala `requirements.txt`;
- copia `backend/` para `/app`;
- expõe porta `8000`;
- sobe `uvicorn app.main:app`.

Função arquitetural:

- empacotar a API principal em ambiente reprodutível;
- padronizar execução local/containerizada.

## 4. Pipelines independentes

Os módulos abaixo continuam existindo e fazem parte da arquitetura do repositório, mas não estão integrados ao backend principal autenticado.

### `backend/pipeline_indexador/`

Pipeline de indexação em memória.

Função:

- pré-processar texto;
- tokenizar;
- construir índice invertido em memória.

Estrutura:

- `app.py`: execução manual;
- `src/indexer/indexer_service.py`: fachada do indexador;
- `src/pipeline/`: infraestrutura do pipeline;
- `src/stages/`: etapas `PreprocessStage`, `TokenizeStage`, `IndexBuildStage`;
- `src/storage/index_repository.py`: repositório do índice invertido em memória;
- `src/tests/pipeline_test.py`: reservado, ainda vazio.

### `backend/pipeline_busca/`

Pipeline de busca em memória.

Função:

- normalizar query;
- tokenizar consulta;
- consultar índice invertido;
- ranquear resultados por frequência.

Estrutura:

- `src/search_app.py`: execução manual;
- `src/search/search_service.py`: fachada da busca;
- `src/pipeline/`: infraestrutura do pipeline;
- `src/stages/`: etapas de preprocessamento, tokenização, consulta e ranking;
- `src/storage/index_repository.py`: índice invertido em memória para consulta.

Leitura arquitetural:

- esses dois módulos continuam relevantes como protótipos funcionais da lógica de recuperação da informação;
- porém ainda estão fora do fluxo da API FastAPI e do schema PostgreSQL principal.

## 5. Testes

### `backend/tests/`

- `test_main.py`: teste de sanidade do endpoint raiz.
- `__init__.py`: marcador de pacote.

Observação importante:

- o teste atual ainda espera a mensagem antiga `{"message": "IFESDOC API running"}`;
- o `main.py` agora retorna `{"message": "IFESDOC rodando 🚀"}`;
- isso indica que a camada de testes já ficou defasada em relação à implementação atual.

## 6. Relação entre as camadas do backend principal

### Fluxo atual de autenticação

```text
POST /api/v1/auth/login
  -> auth_routes.login()
    -> AuthService.login()
      -> UserRepository.get_by_login_or_email()
      -> verify_password()
      -> create_access_token()
    -> TokenResponse
```

### Fluxo atual de usuário autenticado

```text
GET /api/v1/auth/me
  -> Depends(get_current_user)
    -> HTTPBearer
    -> decode_token()
    -> UserRepository/ORM query em User
  -> auth_routes.me()
```

## 7. Estado atual da arquitetura backend

### O que já está consolidado

- FastAPI com `lifespan`, CORS e handlers globais de erro;
- configuração centralizada com `pydantic-settings`;
- conexão PostgreSQL via SQLAlchemy;
- modelo ORM de usuário;
- autenticação JWT com hash bcrypt;
- rotas `/api/v1/auth/login` e `/api/v1/auth/me`;
- schema SQL completo do banco;
- seed de administrador;
- `Dockerfile` da API.

### O que está parcialmente consolidado

- repositórios e services reais existem apenas para autenticação;
- o domínio completo já está modelado no banco, mas não no Python;
- há coexistência de SQLAlchemy e um driver `psycopg2` solto;
- pipelines de indexação e busca ainda não foram absorvidos pela API principal.

### O que ainda está em aberto

- rotas REST dos demais domínios consumidos pelo frontend;
- integração do JWT do login com os outros endpoints;
- implementação de documentos, busca, métricas, ingestão, histórico e configurações na camada `app`;
- convergência entre schema relacional, ORM e pipelines especializados.

## Diagnóstico final

O backend já não é mais apenas um esqueleto. A arquitetura principal entrou em fase operacional com autenticação real, banco configurado, seed inicial e modelo ORM funcional. Ainda assim, o sistema segue dividido em duas frentes:

- `backend/app`: aplicação real em consolidação, hoje centrada em autenticação;
- `pipeline_indexador` e `pipeline_busca`: motores experimentais que preservam a lógica de indexação e recuperação, porém fora da API principal.

Isso torna os documentos de arquitetura importantes para versionamento porque o repositório passou a ter uma transição clara entre arquitetura planejada e arquitetura efetivamente em uso.
