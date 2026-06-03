import re

from app.services.query_analyzer_service import query_analyzer
from app.utils.text_processing import normalize_text


class EntityExtractor:
    COMMAND_TERMS = {
        "buscar",
        "busca",
        "mostrar",
        "listar",
        "procurar",
        "documento",
        "documentos",
        "sobre",
    }

    def extract(self, message: str) -> dict:
        analysis = query_analyzer.analyze(message)
        normalized = normalize_text(message or "")
        terms = [term for term in analysis.terms if term not in self.COMMAND_TERMS]
        return {
            "terms": terms,
            "filters": analysis.filters.model_dump(),
            "document_id": self._extract_document_id(normalized),
            "result_position": self._extract_result_position(normalized),
            "phrases": analysis.phrases,
            "excluded_terms": analysis.excluded_terms,
            "operators": analysis.operators,
            "analysis": analysis.model_dump(),
        }

    def _extract_document_id(self, normalized: str) -> int | None:
        match = re.search(r"\bdocumento\s+(\d+)\b", normalized)
        if match:
            return int(match.group(1))
        match = re.search(r"\bdoc\s+(\d+)\b", normalized)
        if match:
            return int(match.group(1))
        return None

    def _extract_result_position(self, normalized: str) -> int | None:
        match = re.search(r"\b(?:detalhes?|abrir|ver)\s+(?:o\s+)?(\d+)\b", normalized)
        if match:
            return int(match.group(1))
        return None
