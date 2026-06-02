# Copilot Instructions for Indexador-Busca-original

Use this file as a lightweight repository-specific guide. For a fuller overview, consult `AGENTS.md`.

## Key rules

- Prefer changes inside `backend/app/` for backend functionality.
- Keep frontend changes inside `interface-web/` unless an API contract or integration issue requires touching both sides.
- Preserve the existing layered architecture and avoid broad structural refactors unless a feature requires it.
- Use FastAPI/Pydantic idioms consistently for routes, schemas, and validation.
- Encapsulate database access in repository classes and keep business logic in services.
- Keep document parsing and ingestion logic in `adapters/` and `pipeline/`.

## Useful references

- `README.md` — repository overview and architecture summary
- `docs/arquitetura_backend_completo.md` — backend architecture and component boundaries
- `docs/api_spec.md` — API contract and expected endpoints
- `interface-web/README.md` — frontend setup and API integration guidance

## Development workflow

- Bootstrap backend dependencies: `backend\setup-dev.cmd`
- Start backend locally: `backend\start.cmd`
- Docker-based environment: `docker compose up -d --build`
- Run tests from repository root or backend root with `pytest`

## Testing conventions

- Backend unit and integration tests: `backend/app/tests/`
- Additional test suites: `backend/tests/` and `backend/pipeline_indexador/src/tests`
- `pyproject.toml` already configures `pythonpath` for test discovery
