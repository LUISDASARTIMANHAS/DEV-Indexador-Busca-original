# IFESDOC

Sistema de indexacao e busca documental projetado para ingestao, processamento, indexacao e recuperacao de documentos por meio de uma API REST moderna. O projeto adota Python como linguagem principal e uma arquitetura modular voltada a clareza estrutural, baixo acoplamento, alta coesao e evolucao incremental.

## Visao Geral

O IFESDOC foi concebido como um backend orientado a servicos, com separacao explicita de responsabilidades e foco em processamento textual, persistencia relacional e mecanismos de busca extensiveis. A proposta arquitetural combina principios de:

- Clean Architecture
- Domain-Driven Design (DDD simplificado)
- Arquitetura em camadas
- Padroes de projeto orientados a extensibilidade

Essa base permite desenvolver o sistema de forma segura por sprint, facilitando manutencao, testes e substituicao futura de componentes internos sem impacto amplo no dominio.

## Objetivos do Sistema

- Receber documentos para ingestao e processamento.
- Extrair conteudo e metadados de diferentes formatos.
- Construir e manter um indice invertido persistido.
- Executar buscas com estrategias de ranking intercambiaveis.
- Disponibilizar os recursos por meio de API REST.
- Suportar evolucao futura para busca semantica, embeddings e mecanismos hibridos.

## Stack Tecnologica

| Camada | Tecnologia | Papel no sistema |
| --- | --- | --- |
| Linguagem | Python 3.11+ | Base do backend e do processamento textual |
| API | FastAPI | Exposicao da API REST com alta performance e tipagem forte |
| Validacao | Pydantic | Schemas de entrada, saida e serializacao |
| Banco de dados | PostgreSQL | Persistencia relacional e suporte a estrategias de busca |
| ORM | SQLAlchemy | Abstracao de acesso a dados via camada de repositorios |
| Seguranca | Token-based auth, hash seguro de senha | Autenticacao e controle de acesso |
| Testes | Pytest | Testes unitarios e de integracao |
| Containerizacao | Docker | Ambiente isolado e reprodutivel |
| Frontend | interface-web/ | Aplicacao cliente consumindo a API REST |

## Arquitetura

O backend segue uma organizacao modular inspirada em separacao de camadas:

```text
backend/
 └── app/
     ├── api/
     ├── domain/
     ├── services/
     ├── repositories/
     ├── strategies/
     ├── pipeline/
     ├── adapters/
     ├── schemas/
     ├── core/
     ├── exceptions/
     └── utils/
```

### Responsabilidades por camada

- `api/`: recebe requisicoes HTTP, valida entradas e retorna respostas padronizadas.
- `domain/`: concentra entidades centrais, objetos de valor e regras de negocio puras.
- `services/`: orquestra casos de uso, validacoes e coordenacao entre modulos.
- `repositories/`: encapsula o acesso a persistencia e desacopla dominio do banco.
- `strategies/`: permite trocar algoritmos de ranking, relevancia e indexacao.
- `pipeline/`: organiza fluxos de ingestao, preprocessamento, indexacao e busca.
- `adapters/`: isola integracoes externas, como leitura de PDF, TXT e extracao de metadados.
- `schemas/`: define contratos de request/response e validacao com Pydantic.
- `core/`: centraliza configuracoes, bootstrap da aplicacao e dependencias.
- `exceptions/`: padroniza o tratamento de erros de dominio e infraestrutura.
- `utils/`: abriga funcoes auxiliares compartilhadas.

## Padroes de Projeto Adotados

O IFESDOC foi estruturado com padroes que favorecem flexibilidade e testabilidade:

- Repository
- Strategy
- Adapter
- Pipeline / Chain of Responsibility
- Service Layer
- DTOs com Pydantic
- Separacao de camadas inspirada em Clean Architecture

## Indexacao e Busca

O modelo funcional do sistema preve um indice invertido persistido em PostgreSQL, com foco em operacoes de busca documental e calculo de relevancia. A modelagem foi pensada para suportar entidades como:

- `TERMO`
- `INDICE_INVERTIDO`
- `CAMPO_DOCUMENTO`
- `HISTORICO_DOCUMENTO`

Essa abordagem viabiliza:

- Calculo de TF
- Calculo de DF
- Uso futuro de IDF
- Indexacao por campo
- Evolucao para estrategias hibridas e busca semantica

## Seguranca

A arquitetura da aplicacao considera:

- Autenticacao baseada em token
- Hash seguro de senha
- Controle de perfil de usuario e administrador
- Registro de acoes administrativas

## Testes e Qualidade

O projeto possui estrutura dedicada para testes e foi planejado para cobrir:

- Testes unitarios de services
- Testes unitarios de repositories
- Testes unitarios de pipeline
- Testes de integracao da API

O objetivo e garantir comportamento previsivel, facilidade de refatoracao e seguranca na evolucao do codigo.

## Estrutura do Repositorio

```text
.
├── backend/
│   ├── app/
│   ├── pipeline_indexador/
│   └── tests/
├── docs/
├── docker/
└── interface-web/
```

- `backend/`: nucleo da API, dominio, servicos e pipelines.
- `backend/pipeline_indexador/`: estrutura experimental/especializada para etapas de indexacao.
- `backend/pipeline_busca/`: protótipo de busca em memória, separado do backend principal.
- `docs/`: documentacao funcional, arquitetural e especificacoes do sistema.
- `docker/`: estrutura reservada para orquestracao de ambiente.
- `interface-web/`: frontend separado, responsavel pela interface de busca e operacao.

## Como executar

- Backend local: `cd backend && .\setup-dev.cmd` e em seguida `backend\start.cmd`.
- Frontend local: `cd interface-web && npm install && npm run dev`.
- Docker: use `docker compose up -d --build` na raiz do projeto.

## Status atual

- Autenticacao JWT e login com `POST /api/v1/auth/login` ja estao implementados.
- `GET /api/v1/auth/me` expõe perfil do usuário autenticado.
- `POST /api/v1/auth/logout` encerra sessões ativas.
- O frontend suporta modo mock (`VITE_USE_MOCK_API=true`) e pode ser apontado para o backend real em `VITE_API_URL=http://localhost:8000`.
- A especificação de API basica foi documentada em `docs/api_spec.md`.

## Frontend

O frontend fica em `interface-web/` e consome a API REST do sistema. Entre as responsabilidades previstas para a interface estao:

- Busca documental
- Upload de documentos
- Exibicao de resultados
- Visualizacao de documentos
- Relatorios e acompanhamento operacional

## Execucao com Docker

Antes de iniciar os containers, configure um segredo JWT aleatorio com pelo
menos 32 caracteres e uma senha administrativa inicial forte com pelo menos
12 caracteres. O ambiente falha ao iniciar se receber valores padrao ou
curtos.

```bash
cp .env.example .env
# Substitua SECRET_KEY e INITIAL_ADMIN_PASSWORD no arquivo .env.
docker compose -f docker/docker-compose.yml up --build
```

Em volumes criados por versoes anteriores, altere imediatamente a senha do
administrador ja armazenado ou recrie o banco de desenvolvimento.

## Evolucao Arquitetural

O sistema foi desenhado para permitir expansoes sem ruptura do nucleo:

- Busca semantica com embeddings
- Substituicao de mecanismos de ranking
- Uso opcional de Full-Text Search
- Inclusao futura de modulos de IA
- Integracao com estrategias hibridas de recuperacao da informacao

## Documentacao de Apoio

Os principais documentos do projeto estao em `docs/`:

- `docs/arquitetura.md`
- `docs/stack_tecnologica.md`
- `docs/modelo_dados.md`
- `docs/api_spec.md`
- `docs/historias_usuario.md`
- `docs/sonarqube.md`

## Status do Projeto

[![Docker Frontend](https://github.com/Organizacao-LES/Indexador-Busca-original/actions/workflows/docker-frontend.yml/badge.svg)](https://github.com/Organizacao-LES/Indexador-Busca-original/actions/workflows/docker-frontend.yml)

[![Docker Backend](https://github.com/Organizacao-LES/Indexador-Busca-original/actions/workflows/docker-backend.yml/badge.svg?branch=develop)](https://github.com/Organizacao-LES/Indexador-Busca-original/actions/workflows/docker-backend.yml)

O repositorio ja apresenta a estrutura base do backend, frontend e organizacao modular da aplicacao. Parte da arquitetura esta documentada e preparada para implementacao incremental, com foco em consolidar a API, a camada de indexacao e os fluxos de busca documental.

## Principio Norteador

Tecnologia e ferramenta. O modelo representa o dominio.
