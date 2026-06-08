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
from app.core.database import Base, SessionLocal, engine
from app.core.logging import logger
from app.core.schema import ensure_full_text_search_schema, ensure_ocr_schema, ensure_version_file_metadata_columns
from app.core.security import hash_password
from app.domain.administrative_history import AdministrativeHistory
from app.domain.bot_conversation import BotConversation
from app.domain.bot_interaction import BotInteraction
from app.domain.bot_user_link import BotUserLink
from app.domain.document_category import DocumentCategory
from app.domain.document_access_history import DocumentAccessHistory
from app.domain.document_field import DocumentField
from app.domain.document_history import DocumentHistory
from app.domain.document_metadata import DocumentMetadata
from app.domain.field_type import FieldType
from app.domain.index_history import IndexHistory
from app.domain.ingestion_history import IngestionHistory
from app.domain.ingestion_status import IngestionStatus
from app.domain.inverted_index import InvertedIndex
from app.domain.metric_calculation import MetricCalculation
from app.domain.invalid_document import InvalidDocument
from app.domain.document import Document
from app.domain.document_embedding import DocumentEmbedding
from app.domain.notification import Notification
from app.domain.ocr_history import OCRHistory
from app.domain.search_history import SearchHistory
from app.domain.relevance_feedback import RelevanceFeedback
from app.domain.term import Term
from app.domain.user import User
from app.domain.user_session import UserSession


def ensure_initial_admin() -> None:
    if not settings.INITIAL_ADMIN_PASSWORD:
        logger.info("Senha administrativa inicial nao configurada; bootstrap de administrador ignorado.")
        return

    with SessionLocal() as db:
        if db.query(User).filter(User.perfil == "ADMIN").first():
            return
        db.add(
            User(
                nome="Administrador",
                login="admin",
                email="admin@ifes.edu.br",
                senha_hash=hash_password(settings.INITIAL_ADMIN_PASSWORD),
                perfil="ADMIN",
                ativo=True,
            )
        )
        db.commit()
        logger.info("Usuario administrador inicial criado a partir da configuracao segura.")


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Inicializando aplicação e criando tabelas no banco de dados")
    try:
        Base.metadata.create_all(bind=engine)
        ensure_version_file_metadata_columns(engine)
        ensure_ocr_schema(engine)
        ensure_full_text_search_schema(engine)
        ensure_initial_admin()
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
    return {"message": "IFESDOC API running"}
