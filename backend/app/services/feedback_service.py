from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.document import Document
from app.domain.relevance_feedback import RelevanceFeedback
from app.domain.search_history import SearchHistory
from app.domain.user import User
from app.schemas.feedback_schema import RelevanceFeedbackCreate


class FeedbackService:
    def submit(
        self,
        db: Session,
        *,
        payload: RelevanceFeedbackCreate,
        current_user: User,
    ) -> dict:
        search = (
            db.query(SearchHistory)
            .filter(
                SearchHistory.cod_historico_busca == payload.searchId,
                SearchHistory.cod_usuario == current_user.cod_usuario,
            )
            .first()
        )
        if search is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consulta não encontrada para o usuário autenticado.",
            )

        document = (
            db.query(Document)
            .filter(
                Document.cod_documento == payload.documentId,
                Document.ativo.is_(True),
            )
            .first()
        )
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Documento não encontrado.",
            )

        feedback = (
            db.query(RelevanceFeedback)
            .filter(
                RelevanceFeedback.cod_usuario == current_user.cod_usuario,
                RelevanceFeedback.cod_historico_busca == payload.searchId,
                RelevanceFeedback.cod_documento == payload.documentId,
            )
            .first()
        )
        if feedback is None:
            feedback = RelevanceFeedback(
                cod_usuario=current_user.cod_usuario,
                cod_historico_busca=payload.searchId,
                cod_documento=payload.documentId,
            )
            db.add(feedback)

        feedback.nota = payload.rating
        feedback.comentario = payload.comment.strip() if payload.comment else None
        db.commit()
        db.refresh(feedback)
        return {
            "id": feedback.cod_feedback_relevancia,
            "searchId": feedback.cod_historico_busca,
            "documentId": feedback.cod_documento,
            "rating": feedback.nota,
            "comment": feedback.comentario,
            "createdAt": feedback.criado_em,
        }


feedback_service = FeedbackService()
