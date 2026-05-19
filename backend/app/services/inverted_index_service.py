from __future__ import annotations

import math
from collections.abc import Iterable

from sqlalchemy import distinct, func
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.domain.document import Document
from app.domain.document_field import DocumentField
from app.domain.document_history import DocumentHistory
from app.domain.field_type import FieldType
from app.domain.inverted_index import InvertedIndex
from app.domain.term import Term


class InvertedIndexService:
    def persist_document_fields(
        self,
        db: Session,
        *,
        history: DocumentHistory,
        fields: list[dict],
    ) -> dict:
        logger.debug(
            "Persistindo campos do histórico %s: %s campo(s)",
            history.cod_historico_documento,
            len(fields),
        )
        affected_term_ids = self._remove_previous_index_entries(
            db,
            history_id=history.cod_historico_documento,
        )
        total_term_count = 0
        total_token_count = 0
        processed_segments: list[str] = []

        for field in fields:
            positions_by_term: dict[str, list[int]] = field["positions_by_term"]
            processed_text = field["processed_text"]
            field_type_name = field["field_type"]

            field_type = self._get_or_create_field_type(db, field_type_name)
            document_field = DocumentField(
                cod_historico_documento=history.cod_historico_documento,
                cod_tipo_campo=field_type.cod_tipo_campo,
                conteudo=processed_text,
            )
            db.add(document_field)
            db.flush()

            for token, positions in positions_by_term.items():
                if not positions:
                    continue

                term = self._get_or_create_term(db, token)
                db.add(
                    InvertedIndex(
                        cod_termo=term.cod_termo,
                        cod_campo_documento=document_field.cod_campo_documento,
                        tf=len(positions),
                        posicao_inicial=positions[0],
                    )
                )
                affected_term_ids.add(term.cod_termo)

            total_term_count += field.get("term_count", len(positions_by_term))
            total_token_count += field.get(
                "token_count",
                sum(len(positions) for positions in positions_by_term.values()),
            )
            if processed_text:
                processed_segments.append(processed_text)

        history.texto_processado = "\n".join(processed_segments)
        db.flush()
        self.refresh_all_term_statistics(db)

        return {
            "term_count": total_term_count,
            "token_count": total_token_count,
        }

    def remove_document_terms(self, db: Session, *, document_id: int) -> dict:
        existing_field_ids = [
            row.cod_campo_documento
            for row in db.query(DocumentField.cod_campo_documento)
            .join(
                DocumentHistory,
                DocumentHistory.cod_historico_documento == DocumentField.cod_historico_documento,
            )
            .filter(DocumentHistory.cod_documento == document_id)
            .all()
        ]
        if not existing_field_ids:
            logger.info(
                "Nenhum índice encontrado para remoção do documento %s",
                document_id,
            )
            return {
                "removed_postings": 0,
                "removed_fields": 0,
                "affected_terms": 0,
            }

        logger.info(
            "Removendo índice existente para documento %s: %s campo(s) encontrados",
            document_id,
            len(existing_field_ids),
        )
        affected_term_ids = {
            row.cod_termo
            for row in db.query(InvertedIndex.cod_termo)
            .filter(InvertedIndex.cod_campo_documento.in_(existing_field_ids))
            .distinct()
            .all()
        }
        removed_postings = (
            db.query(InvertedIndex)
            .filter(InvertedIndex.cod_campo_documento.in_(existing_field_ids))
            .delete(synchronize_session=False)
        )
        removed_fields = (
            db.query(DocumentField)
            .filter(DocumentField.cod_campo_documento.in_(existing_field_ids))
            .delete(synchronize_session=False)
        )
        self.refresh_all_term_statistics(db)
        logger.info(
            "Remoção indexada do documento %s concluída: %s postings apagados, %s campos apagados, %s termos afetados",
            document_id,
            removed_postings,
            removed_fields,
            len(affected_term_ids),
        )
        return {
            "removed_postings": removed_postings,
            "removed_fields": removed_fields,
            "affected_terms": len(affected_term_ids),
        }

    def persist_document_terms(
        self,
        db: Session,
        *,
        history: DocumentHistory,
        processed_text: str,
        positions_by_term: dict[str, list[int]],
    ) -> dict:
        return self.persist_document_fields(
            db,
            history=history,
            fields=[
                {
                    "field_type": "conteudo",
                    "processed_text": processed_text,
                    "positions_by_term": positions_by_term,
                    "term_count": len(positions_by_term),
                    "token_count": sum(len(positions) for positions in positions_by_term.values()),
                }
            ],
        )

    def find_document_ids_by_terms(self, db: Session, terms: Iterable[str]) -> list[int]:
        normalized_terms = [term for term in set(terms) if term]
        if not normalized_terms:
            return []

        rows = (
            db.query(distinct(Document.cod_documento))
            .select_from(InvertedIndex)
            .join(Term, Term.cod_termo == InvertedIndex.cod_termo)
            .join(
                DocumentField,
                DocumentField.cod_campo_documento == InvertedIndex.cod_campo_documento,
            )
            .join(
                DocumentHistory,
                DocumentHistory.cod_historico_documento == DocumentField.cod_historico_documento,
            )
            .join(Document, Document.cod_documento == DocumentHistory.cod_documento)
            .filter(Term.texto_termo.in_(normalized_terms))
            .filter(Document.ativo.is_(True))
            .filter(DocumentHistory.versao_ativa.is_(True))
            .order_by(Document.cod_documento.asc())
            .all()
        )
        return [row[0] for row in rows]

    def _get_or_create_field_type(self, db: Session, field_type_name: str) -> FieldType:
        field_type = (
            db.query(FieldType)
            .filter(FieldType.tipo_campo == field_type_name)
            .first()
        )
        if field_type is not None:
            return field_type

        field_type = FieldType(tipo_campo=field_type_name)
        db.add(field_type)
        db.flush()
        return field_type

    def _remove_previous_index_entries(self, db: Session, *, history_id: int) -> set[int]:
        existing_field_ids = [
            row.cod_campo_documento
            for row in db.query(DocumentField.cod_campo_documento)
            .filter(DocumentField.cod_historico_documento == history_id)
            .all()
        ]
        affected_term_ids: set[int] = set()

        if not existing_field_ids:
            return affected_term_ids

        affected_term_ids.update(
            row.cod_termo
            for row in db.query(InvertedIndex.cod_termo)
            .filter(InvertedIndex.cod_campo_documento.in_(existing_field_ids))
            .distinct()
            .all()
        )
        db.query(InvertedIndex).filter(
            InvertedIndex.cod_campo_documento.in_(existing_field_ids)
        ).delete(synchronize_session=False)
        db.query(DocumentField).filter(
            DocumentField.cod_campo_documento.in_(existing_field_ids)
        ).delete(synchronize_session=False)

        return affected_term_ids

    def _get_or_create_term(self, db: Session, token: str) -> Term:
        term = db.query(Term).filter(Term.texto_termo == token).first()
        if term is not None:
            return term

        term = Term(texto_termo=token, df=0, idf=0)
        db.add(term)
        db.flush()
        return term

    def _refresh_term_statistics(self, db: Session, term_ids: set[int]) -> None:
        active_document_count = (
            db.query(func.count(Document.cod_documento))
            .filter(Document.ativo.is_(True))
            .scalar()
            or 0
        )

        for term_id in term_ids:
            term = db.query(Term).filter(Term.cod_termo == term_id).first()
            if term is None:
                continue

            document_frequency = self._document_frequency(db, term.cod_termo)
            term.df = document_frequency
            if document_frequency > 0 and active_document_count > 0:
                scaled_idf = math.log((active_document_count + 1) / (document_frequency + 1) + 1)
                term.idf = max(int(round(scaled_idf * 1000)), 1)
            else:
                term.idf = 0

    def refresh_all_term_statistics(self, db: Session) -> int:
        """Atualiza df e idf para todos os termos existentes no sistema.

        Args:
            db: Sessão do banco de dados.

        Returns:
            Número de termos processados.
        """
        logger.info("Atualizando estatísticas de todos os termos no índice")
        active_document_count = (
            db.query(func.count(Document.cod_documento))
            .filter(Document.ativo.is_(True))
            .scalar()
            or 0
        )

        terms = db.query(Term).all()
        for term in terms:
            document_frequency = self._document_frequency(db, term.cod_termo)
            term.df = document_frequency
            if document_frequency > 0 and active_document_count > 0:
                scaled_idf = math.log((active_document_count + 1) / (document_frequency + 1) + 1)
                term.idf = max(int(round(scaled_idf * 1000)), 1)
            else:
                term.idf = 0

        db.flush()
        logger.info(
            "Estatísticas de termos atualizadas para %s termo(s)",
            len(terms),
        )
        return len(terms)

    def _document_frequency(self, db: Session, term_id: int) -> int:
        return (
            db.query(func.count(distinct(Document.cod_documento)))
            .select_from(InvertedIndex)
            .join(
                DocumentField,
                DocumentField.cod_campo_documento == InvertedIndex.cod_campo_documento,
            )
            .join(
                DocumentHistory,
                DocumentHistory.cod_historico_documento == DocumentField.cod_historico_documento,
            )
            .join(Document, Document.cod_documento == DocumentHistory.cod_documento)
            .filter(InvertedIndex.cod_termo == term_id)
            .filter(Document.ativo.is_(True))
            .filter(DocumentHistory.versao_ativa.is_(True))
            .scalar()
            or 0
        )


inverted_index_service = InvertedIndexService()
