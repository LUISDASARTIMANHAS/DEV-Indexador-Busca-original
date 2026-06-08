# app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1.auth_routes import router as auth_router
from app.api.v1.bot_routes import router as bot_router
from app.api.v1.document_routes import router as document_router
from app.api.v1.history_routes import router as history_router
from app.api.v1.index_routes import router as index_router
from app.api.v1.ingestion_routes import router as ingestion_router
from app.api.v1.user_routes import router as user_router
from app.api.v1.search_routes import router as search_router
from app.api.v1.metrics_routes import router as metrics_router
from app.api.v1.settings_routes import router as settings_router
from app.api.v1.notification_routes import router as notification_router
from app.api.v1.feedback_routes import router as feedback_router
from app.api.v1.ocr_routes import router as ocr_router


api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(bot_router)
api_router.include_router(document_router)
api_router.include_router(history_router)
api_router.include_router(index_router)
api_router.include_router(ingestion_router)
api_router.include_router(user_router)

api_router.include_router(search_router)
api_router.include_router(metrics_router)
api_router.include_router(settings_router)
api_router.include_router(notification_router)
api_router.include_router(feedback_router)
api_router.include_router(ocr_router)
