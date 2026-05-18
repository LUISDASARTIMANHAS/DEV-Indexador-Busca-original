from sqlalchemy.orm import Session

from app.domain.user_session import UserSession


class SessionRepository:
    @staticmethod
    def create(db: Session, session: UserSession) -> UserSession:
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_by_identifier(db: Session, session_id: str) -> UserSession | None:
        return (
            db.query(UserSession)
            .filter(UserSession.identificador_sessao == session_id)
            .first()
        )

    @staticmethod
    def save(db: Session, session: UserSession) -> UserSession:
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
