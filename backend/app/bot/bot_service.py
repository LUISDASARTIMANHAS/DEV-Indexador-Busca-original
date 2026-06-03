from sqlalchemy.orm import Session

from app.bot.entity_extractor import EntityExtractor
from app.bot.intent_detector import IntentDetector
from app.bot.message_formatter import MessageFormatter
from app.core.config import settings
from app.core.logging import logger
from app.domain.user import User
from app.repositories.bot_repository import BotRepository
from app.repositories.document_repository import DocumentRepository
from app.services.metrics_service import metrics_service
from app.services.search_service import search_service


class BotService:
    SEARCH_INTENTS = {"search_documents", "search_with_filters"}

    def __init__(
        self,
        repository: BotRepository,
        intent_detector: IntentDetector,
        entity_extractor: EntityExtractor,
        formatter: MessageFormatter,
    ):
        self.repository = repository
        self.intent_detector = intent_detector
        self.entity_extractor = entity_extractor
        self.formatter = formatter
        self.document_repository = DocumentRepository()

    def handle_message(
        self,
        db: Session,
        *,
        channel: str,
        external_user_id: str,
        message: str,
    ) -> dict:
        channel = (channel or "test").strip().lower()
        external_user_id = str(external_user_id or "").strip()
        message = message or ""
        conversation = self.repository.get_or_create_conversation(
            db,
            channel=channel,
            external_user_id=external_user_id,
        )
        context = conversation.ultimo_contexto or {}

        if self._is_rate_limited(db, channel=channel, external_user_id=external_user_id):
            response = self._response(
                channel=channel,
                external_user_id=external_user_id,
                intent="unknown",
                entities={},
                response_text=self.formatter.format_rate_limited(),
                success=False,
            )
            self._record(db, message=message, response=response)
            return response

        intent = self.intent_detector.detect(message)
        entities = self.entity_extractor.extract(message)
        logger.info("Bot message channel=%s user=%s intent=%s", channel, external_user_id, intent)

        if intent in self.SEARCH_INTENTS:
            response = self._handle_search(
                db,
                channel=channel,
                external_user_id=external_user_id,
                message=message,
                intent=intent,
                entities=entities,
            )
            context = {
                "last_query": response.get("query") or message,
                "last_results": self._context_results(response.get("results", [])),
            }
        elif intent == "get_document_details":
            response = self._handle_document_details(
                db,
                channel=channel,
                external_user_id=external_user_id,
                intent=intent,
                entities=entities,
                context=context,
            )
        elif intent == "generate_search_report":
            response = self._handle_report(
                db,
                channel=channel,
                external_user_id=external_user_id,
                intent=intent,
                entities=entities,
            )
        elif intent == "view_search_history":
            interactions = self.repository.list_recent_interactions(
                db,
                channel=channel,
                external_user_id=external_user_id,
                limit=5,
            )
            response = self._response(
                channel=channel,
                external_user_id=external_user_id,
                intent=intent,
                entities=entities,
                response_text=self.formatter.format_history(interactions),
            )
        elif intent == "help":
            response = self._response(
                channel=channel,
                external_user_id=external_user_id,
                intent=intent,
                entities=entities,
                response_text=self.formatter.format_help(),
            )
        else:
            response = self._response(
                channel=channel,
                external_user_id=external_user_id,
                intent=intent,
                entities=entities,
                response_text=self.formatter.format_unknown(),
                success=False,
            )

        self.repository.update_conversation(
            db,
            conversation=conversation,
            intent=intent,
            context=context,
        )
        self._record(db, message=message, response=response)
        return response

    def _handle_search(
        self,
        db: Session,
        *,
        channel: str,
        external_user_id: str,
        message: str,
        intent: str,
        entities: dict,
    ) -> dict:
        user = self._resolve_search_user(db, channel=channel, external_user_id=external_user_id)
        if user is None:
            return self._response(
                channel=channel,
                external_user_id=external_user_id,
                intent=intent,
                entities=entities,
                response_text="Não há usuário interno ativo para registrar a busca do bot.",
                success=False,
            )

        query = self._build_search_query(message, entities)
        result = search_service.search(
            db,
            query=query,
            user_id=user.cod_usuario,
            limit=5,
            page=1,
            mode="bm25",
            debug_analysis=True,
        )
        items = result.get("items", [])
        response_text = self.formatter.format_search_results(
            query=query,
            results=items,
            total=result.get("total", 0),
        )
        return self._response(
            channel=channel,
            external_user_id=external_user_id,
            intent=intent,
            entities=entities,
            response_text=response_text,
            results=items,
            success=True,
            extra={"query": query, "search_id": result.get("searchId")},
        )

    def _handle_document_details(
        self,
        db: Session,
        *,
        channel: str,
        external_user_id: str,
        intent: str,
        entities: dict,
        context: dict,
    ) -> dict:
        document_id = entities.get("document_id") or self._document_id_from_context(
            context,
            entities.get("result_position"),
        )
        document = self.document_repository.get_document_payload(db, int(document_id)) if document_id else None
        return self._response(
            channel=channel,
            external_user_id=external_user_id,
            intent=intent,
            entities=entities,
            response_text=self.formatter.format_document_details(document),
            results=[document] if document else [],
            success=document is not None,
        )

    def _handle_report(
        self,
        db: Session,
        *,
        channel: str,
        external_user_id: str,
        intent: str,
        entities: dict,
    ) -> dict:
        linked_user = self.repository.get_linked_user(
            db,
            channel=channel,
            external_user_id=external_user_id,
        )
        if settings.BOT_PUBLIC_MODE and (linked_user is None or linked_user.perfil != "ADMIN"):
            return self._response(
                channel=channel,
                external_user_id=external_user_id,
                intent=intent,
                entities=entities,
                response_text=(
                    "Relatórios administrativos exigem usuário IFESDOC vinculado com perfil administrador. "
                    "No modo público, posso ajudar com buscas documentais."
                ),
                success=False,
            )
        report = metrics_service.build_report(db)
        return self._response(
            channel=channel,
            external_user_id=external_user_id,
            intent=intent,
            entities=entities,
            response_text=self.formatter.format_report(report),
            results=[],
        )

    def _resolve_search_user(self, db: Session, *, channel: str, external_user_id: str) -> User | None:
        linked_user = self.repository.get_linked_user(
            db,
            channel=channel,
            external_user_id=external_user_id,
        )
        if linked_user is not None:
            return linked_user
        if settings.BOT_PUBLIC_MODE:
            return self.repository.get_public_search_user(db)
        return None

    def _build_search_query(self, message: str, entities: dict) -> str:
        parts = list(entities.get("terms") or []) + list(entities.get("phrases") or [])
        return " ".join(parts).strip() or message.strip()

    def _document_id_from_context(self, context: dict, position: int | None) -> int | None:
        if not position:
            return None
        for item in context.get("last_results", []):
            if int(item.get("position", 0)) == int(position):
                return int(item["document_id"])
        return None

    def _context_results(self, results: list[dict]) -> list[dict]:
        return [
            {
                "position": index,
                "document_id": item.get("id") or item.get("documentId"),
                "title": item.get("title"),
            }
            for index, item in enumerate(results, start=1)
            if item.get("id") or item.get("documentId")
        ]

    def _is_rate_limited(self, db: Session, *, channel: str, external_user_id: str) -> bool:
        if settings.BOT_RATE_LIMIT_PER_MINUTE <= 0:
            return False
        return (
            self.repository.count_recent_interactions(
                db,
                channel=channel,
                external_user_id=external_user_id,
                seconds=60,
            )
            >= settings.BOT_RATE_LIMIT_PER_MINUTE
        )

    def _record(self, db: Session, *, message: str, response: dict) -> None:
        self.repository.create_interaction(
            db,
            channel=response["channel"],
            external_user_id=response["external_user_id"],
            message=message,
            intent=response["intent"],
            entities=response.get("entities", {}),
            response_text=response["response_text"],
            success=response["success"],
        )

    def _response(
        self,
        *,
        channel: str,
        external_user_id: str,
        intent: str,
        entities: dict,
        response_text: str,
        results: list[dict] | None = None,
        success: bool = True,
        extra: dict | None = None,
    ) -> dict:
        response = {
            "channel": channel,
            "external_user_id": external_user_id,
            "intent": intent,
            "entities": entities,
            "response_text": response_text,
            "results": results or [],
            "success": success,
        }
        if extra:
            response.update(extra)
        return response


bot_service = BotService(
    BotRepository(),
    IntentDetector(),
    EntityExtractor(),
    MessageFormatter(),
)
