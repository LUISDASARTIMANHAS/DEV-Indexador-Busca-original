# AI Agent Instructions for Indexador-Busca-original

This repository is a Python-based document indexing/search system with a separate frontend in `interface-web/`.

## What to know first

- The main backend application is in `backend/app/`.
- The frontend is a separate Vite/TypeScript app in `interface-web/` and consumes the FastAPI backend.
- The repository uses a layered architecture inspired by Clean Architecture / DDD.
- Important backend layers:
  - `api/` for HTTP routes
  - `domain/` for core entities and business rules
  - `services/` for use-case orchestration
  - `repositories/` for persistence abstractions
  - `strategies/` for interchangeable ranking/indexing logic
  - `pipeline/` for ingestion/indexing flows
  - `adapters/` for document parsers and external integration
  - `schemas/` for Pydantic request/response contracts
  - `core/` for configuration, bootstrap, dependencies
  - `exceptions/` for error handling

## Recommended files and docs

- `README.md` — high-level project overview and system goals
- `docs/arquitetura_backend_completo.md` — backend architecture details
- `docs/stack_tecnologica.md` — technology choices and architecture notes
- `docs/api_spec.md` — API expectations
- `interface-web/README.md` — frontend setup and API integration

## Development commands

- Local backend startup: `backend\start.cmd`
- Backend environment bootstrap (Windows): `backend\setup-dev.cmd`
- Docker-compose workflow: `docker compose up -d --build`
- Docker image build wrapper: `docker\create-Image.cmd`
- Run tests via `pytest` from the repository root or backend root

## Testing conventions

- Backend tests live in `backend/app/tests/`
- Additional tests are under `backend/tests/` and `backend/pipeline_indexador/src/tests`
- `pyproject.toml` configures `pythonpath` for backend imports and test discovery

## What the AI should do

- Prefer changes inside `backend/app/` for backend functionality.
- Keep frontend changes isolated to `interface-web/` unless API contract changes are required.
- Preserve existing architecture boundaries when adding features or refactoring.
- Use repo documentation links rather than duplicating design rationale.
- Avoid making broad changes to the overall structure unless a feature requires it.

## Notes for code suggestions

- Use FastAPI/Pydantic idioms consistently for routes, schemas, and validation.
- SQLAlchemy data access should be encapsulated in repository classes.
- Document parsing and ingestion logic should remain in `adapters/` and `pipeline/`.
- Authentication is token-based; follow existing auth service and dependency patterns.
- A single API contract exists; avoid splitting backend and frontend concerns unnecessarily.
- For frontend work, keep `VITE_API_URL` awareness in mind and use `interface-web/README.md` as guidance.

## Why this file exists

This file makes it easier for AI coding agents to understand the repository layout, the main development entry points, and the architectural boundaries without reading every document.
