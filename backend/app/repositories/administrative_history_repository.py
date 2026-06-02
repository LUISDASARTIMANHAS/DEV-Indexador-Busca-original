from datetime import datetime

from sqlalchemy.orm import Session

from app.domain.administrative_history import AdministrativeHistory


class AdministrativeHistoryRepository:
    @staticmethod
    def create(db: Session, history: AdministrativeHistory) -> AdministrativeHistory:
        db.add(history)
        db.commit()
        db.refresh(history)
        return history

    @staticmethod
    def list_recent(
        db: Session,
        *,
        limit: int = 100,
        user_id: int | None = None,
        performed_from: datetime | None = None,
        performed_to: datetime | None = None,
    ) -> list[AdministrativeHistory]:
        query = db.query(AdministrativeHistory)
        if user_id is not None:
            query = query.filter(AdministrativeHistory.cod_usuario == user_id)
        if performed_from is not None:
            query = query.filter(AdministrativeHistory.criado_em >= performed_from)
        if performed_to is not None:
            query = query.filter(AdministrativeHistory.criado_em <= performed_to)
        return (
            query.order_by(
                AdministrativeHistory.criado_em.desc(),
                AdministrativeHistory.cod_historico_administrativo.desc(),
            )
            .limit(limit)
            .all()
        )
