# indexadordebusca/backend/app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError, ProgrammingError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.logging import logger
from app.domain.administrative_history import AdministrativeHistory
from app.domain.document_category import DocumentCategory
from app.domain.document_field import DocumentField
from app.domain.document_history import DocumentHistory
from app.domain.document_metadata import DocumentMetadata
from app.domain.field_type import FieldType
from app.domain.index_history import IndexHistory
from app.domain.ingestion_history import IngestionHistory
from app.domain.ingestion_status import IngestionStatus
from app.domain.inverted_index import InvertedIndex
from app.domain.invalid_document import InvalidDocument
from app.domain.document import Document
from app.domain.notification import Notification
from app.domain.search_history import SearchHistory
from app.domain.term import Term
from app.domain.user import User
from app.domain.user_session import UserSession


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Inicializando aplicação e criando tabelas no banco de dados")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Banco de dados inicializado com sucesso")
    except OperationalError as exc:
        logger.warning("Falha ao inicializar o schema do banco de dados: %s", exc)
    yield


app = FastAPI(title="IFESDOC API", lifespan=lifespan)
logger.info("IFESDOC API criada com sucesso")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_: Request, exc: StarletteHTTPException):
    detail = exc.detail
    if isinstance(detail, list) and detail:
        first_error = detail[0]
        if isinstance(first_error, dict):
            message = first_error.get("msg", "Dados inválidos.")
        else:
            message = str(first_error)
    elif isinstance(detail, dict):
        message = str(detail.get("message") or detail.get("detail") or "Erro na requisição.")
    elif isinstance(detail, str):
        message = detail
    else:
        message = "Erro na requisição."

    logger.warning("HTTPException %s: %s", exc.status_code, message)
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": message},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    first_error = exc.errors()[0] if exc.errors() else None
    message = first_error.get("msg", "Dados inválidos.") if first_error else "Dados inválidos."
    logger.warning("RequestValidationError: %s", exc.errors())
    return JSONResponse(
        status_code=422,
        content={"message": message},
    )


@app.exception_handler(OperationalError)
async def database_unavailable_handler(_: Request, exc: OperationalError):
    logger.error("Banco de dados indisponível: %s", exc)
    return JSONResponse(
        status_code=503,
        content={"message": "Banco de dados indisponível. Verifique se o PostgreSQL está em execução."},
    )


@app.exception_handler(ProgrammingError)
async def database_schema_handler(_: Request, exc: ProgrammingError):
    logger.error("Erro de schema do banco de dados: %s", exc)
    return JSONResponse(
        status_code=503,
        content={"message": "Estrutura do banco não inicializada. Reinicie a API com o PostgreSQL ativo ou rode a criação do schema."},
    )


@app.get("/")
def root():
    logger.info("GET / - healthcheck acessado")
    return {"message": "IFESDOC rodando 🚀"}
