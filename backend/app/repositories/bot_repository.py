from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.domain.bot_conversation import BotConversation
from app.domain.bot_interaction import BotInteraction
from app.domain.bot_user_link import BotUserLink
from app.domain.user import User


class BotRepository:
    def get_or_create_conversation(
        self,
        db: Session,
        *,
        channel: str,
        external_user_id: str,
    ) -> BotConversation:
        conversation = (
            db.query(BotConversation)
            .filter(
                BotConversation.canal == channel,
                BotConversation.usuario_externo == external_user_id,
            )
            .first()
        )
        if conversation is not None:
            return conversation

        conversation = BotConversation(
            canal=channel,
            usuario_externo=external_user_id,
            ultimo_contexto={},
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    def update_conversation(
        self,
        db: Session,
        *,
        conversation: BotConversation,
        intent: str,
        context: dict,
    ) -> BotConversation:
        conversation.ultima_intencao = intent
        conversation.ultimo_contexto = context
        conversation.atualizado_em = datetime.utcnow()
        db.commit()
        db.refresh(conversation)
        return conversation

    def create_interaction(
        self,
        db: Session,
        *,
        channel: str,
        external_user_id: str,
        message: str,
        intent: str,
        entities: dict,
        response_text: str,
        success: bool,
    ) -> BotInteraction:
        interaction = BotInteraction(
            canal=channel,
            usuario_externo=external_user_id,
            mensagem_usuario=message,
            intencao_detectada=intent,
            entidades=entities,
            resposta_bot=response_text,
            sucesso=success,
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)
        return interaction

    def count_recent_interactions(
        self,
        db: Session,
        *,
        channel: str,
        external_user_id: str,
        seconds: int = 60,
    ) -> int:
        since = datetime.utcnow() - timedelta(seconds=seconds)
        return (
            db.query(BotInteraction)
            .filter(
                BotInteraction.canal == channel,
                BotInteraction.usuario_externo == external_user_id,
                BotInteraction.criado_em >= since,
            )
            .count()
        )

    def get_linked_user(
        self,
        db: Session,
        *,
        channel: str,
        external_user_id: str,
    ) -> User | None:
        return (
            db.query(User)
            .join(BotUserLink, BotUserLink.cod_usuario == User.cod_usuario)
            .filter(
                BotUserLink.canal == channel,
                BotUserLink.usuario_externo == external_user_id,
                BotUserLink.ativo.is_(True),
                User.ativo.is_(True),
            )
            .first()
        )

    def get_public_search_user(self, db: Session) -> User | None:
        return (
            db.query(User)
            .filter(User.ativo.is_(True))
            .order_by(User.cod_usuario.asc())
            .first()
        )

    def list_recent_interactions(
        self,
        db: Session,
        *,
        channel: str,
        external_user_id: str,
        limit: int = 5,
    ) -> list[BotInteraction]:
        return (
            db.query(BotInteraction)
            .filter(
                BotInteraction.canal == channel,
                BotInteraction.usuario_externo == external_user_id,
            )
            .order_by(BotInteraction.criado_em.desc(), BotInteraction.cod_interacao.desc())
            .limit(limit)
            .all()
        )
