from datetime import date, datetime, time

from sqlalchemy.orm import Session

from app.domain.administrative_history import AdministrativeHistory
from app.domain.user import User
from app.repositories.administrative_history_repository import (
    AdministrativeHistoryRepository,
)
from app.repositories.user_repository import UserRepository


class AdministrativeHistoryService:
    def __init__(self, repository: AdministrativeHistoryRepository):
        self.repository = repository

    def log_action(
        self,
        db: Session,
        *,
        actor: User,
        description: str,
        action_type: str,
        entity_type: str,
        entity_id: int,
    ) -> AdministrativeHistory:
        history = AdministrativeHistory(
            cod_usuario=actor.cod_usuario,
            descricao=description[:255],
            tipo_acao=action_type[:255],
            entidade_tipo=entity_type[:255],
            cod_entidade=entity_id,
        )
        return self.repository.create(db, history)

    def list_history(
        self,
        db: Session,
        *,
        limit: int = 100,
        user_id: int | None = None,
        performed_from: date | None = None,
        performed_to: date | None = None,
    ) -> list[dict]:
        entries = self.repository.list_recent(
            db,
            limit=limit,
            user_id=user_id,
            performed_from=datetime.combine(performed_from, time.min) if performed_from else None,
            performed_to=datetime.combine(performed_to, time.max) if performed_to else None,
        )
        results: list[dict] = []
        for entry in entries:
            user = UserRepository.get_by_id(db, entry.cod_usuario)
            results.append(
                {
                    "date": entry.criado_em.strftime("%Y-%m-%d %H:%M") if entry.criado_em else "",
                    "user": user.email if user else f"usuario:{entry.cod_usuario}",
                    "action": entry.tipo_acao,
                    "details": entry.descricao,
                    "status": "success",
                }
            )
        return results


administrative_history_service = AdministrativeHistoryService(
    AdministrativeHistoryRepository()
)
