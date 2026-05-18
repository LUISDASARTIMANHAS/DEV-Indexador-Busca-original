from __future__ import annotations

from collections import defaultdict

from sqlalchemy.orm import Session

from app.domain.document_history import DocumentHistory
from app.exceptions.document_exceptions import DocumentValidationException
from app.pipeline.pipeline_stage import PipelineStage
from app.services.inverted_index_service import inverted_index_service
from app.utils.text_processing import preprocess_for_indexing


class TextPreprocessStage(PipelineStage):
    def execute(self, db: Session, context: dict) -> dict:
        del db
        field_texts = context.get("field_texts")
        if field_texts:
            preprocessed_fields: list[dict] = []
            for field in field_texts:
                text = field.get("text", "")
                preprocessed = preprocess_for_indexing(text)
                if preprocessed["tokens"]:
                    preprocessed_fields.append(
                        {
                            "field_type": field["field_type"],
                            **preprocessed,
                        }
                    )

            if not preprocessed_fields:
                raise DocumentValidationException(
                    "Não foi possível gerar conteúdo processável para indexação."
                )

            context["preprocessed_fields"] = preprocessed_fields
            return context

        extracted_text = context.get("extracted_text", "")
        preprocessed = preprocess_for_indexing(extracted_text)
        if not preprocessed["normalized_text"]:
            raise DocumentValidationException(
                "Não foi possível gerar conteúdo processável para indexação."
            )
        context["normalized_text"] = preprocessed["normalized_text"]
        context["preprocessed_output"] = preprocessed
        return context


class TextTokenizeStage(PipelineStage):
    def execute(self, db: Session, context: dict) -> dict:
        del db
        preprocessed_fields = context.get("preprocessed_fields")
        if preprocessed_fields:
            total_tokens = sum(field["token_count"] for field in preprocessed_fields)
            if total_tokens <= 0:
                raise DocumentValidationException(
                    "O documento não contém termos válidos para indexação."
                )
            context["index_fields"] = preprocessed_fields
            context["processed_text"] = "\n".join(
                field["processed_text"] for field in preprocessed_fields if field["processed_text"]
            )
            return context

        preprocessed = context.get("preprocessed_output") or preprocess_for_indexing(
            context.get("extracted_text", "")
        )
        tokens = preprocessed["tokens"]
        if not tokens:
            raise DocumentValidationException(
                "O documento não contém termos válidos para indexação."
            )
        context["processed_text"] = preprocessed["processed_text"]
        context["tokens"] = tokens
        context["index_payload"] = preprocessed
        return context


class RelationalIndexPersistStage(PipelineStage):
    def execute(self, db: Session, context: dict) -> dict:
        history: DocumentHistory = context["document_history"]
        index_fields = context.get("index_fields")
        if index_fields:
            result = inverted_index_service.persist_document_fields(
                db,
                history=history,
                fields=index_fields,
            )
            context["term_count"] = result["term_count"]
            context["token_count"] = result["token_count"]
            return context

        processed_text: str = context["processed_text"]

        index_payload = context.get("index_payload") or {
            "positions_by_term": defaultdict(list)
        }
        positions_by_term: dict[str, list[int]] = index_payload["positions_by_term"]
        result = inverted_index_service.persist_document_terms(
            db,
            history=history,
            processed_text=processed_text,
            positions_by_term=positions_by_term,
        )

        context["term_count"] = index_payload.get("term_count", result["term_count"])
        context["token_count"] = index_payload.get("token_count", result["token_count"])
        return context
