import re
import unicodedata

from pipeline_busca.src.pipeline.pipeline_stage import PipelineStage

try:
    from app.services.query_analyzer_service import query_analyzer
except ImportError:
    query_analyzer = None


class QueryAnalyzeStage(PipelineStage):
    """
    Etapa explicita de Parser de query + Analise no pipeline de busca.
    """

    def execute(self, context: dict) -> dict:
        query = context.get("query", "")
        if query_analyzer is not None:
            analysis = query_analyzer.analyze(query).model_dump()
            context["analysis"] = analysis
            context["processed_query"] = analysis["normalized_query"]
            context["tokens"] = analysis["terms"]
            return context

        normalized_query = self._normalize(query)
        tokens = [token for token in normalized_query.split(" ") if token]
        context["analysis"] = {
            "raw_query": query,
            "normalized_query": normalized_query,
            "tokens": tokens,
            "terms": tokens,
            "filters": {},
            "phrases": [],
            "excluded_terms": [],
            "operators": [],
            "intent": "search_documents",
            "is_valid": bool(normalized_query),
            "warnings": [] if normalized_query else ["Consulta vazia."],
        }
        context["processed_query"] = normalized_query
        context["tokens"] = tokens
        return context

    def _normalize(self, text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text or "")
        normalized = normalized.encode("ascii", "ignore").decode("ascii")
        normalized = normalized.lower()
        normalized = re.sub(r"[^\w\s]", " ", normalized)
        return re.sub(r"\s+", " ", normalized).strip()
