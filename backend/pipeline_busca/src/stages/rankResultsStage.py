from collections import Counter

from app.strategies.bm25_strategy import BM25RankingStrategy
from app.strategies.frequency_strategy import FrequencyRankingStrategy
from app.strategies.tfidf_strategy import TFIDFRankingStrategy
from pipeline_busca.src.pipeline.pipeline_stage import PipelineStage


TEXTUAL_STRATEGIES = {
    "frequency": FrequencyRankingStrategy(),
    "tfidf": TFIDFRankingStrategy(),
    "bm25": BM25RankingStrategy(),
}

class RankResultsStage(PipelineStage):

    """
    Etapa responsável por ordenar os documentos
    de acordo com a relevância e limitar os resultados.
    """

    def execute(self, context: dict) -> dict:

        # Recupera a lista de documentos encontrados
        documents = context.get("documents", [])

        # Recupera o limite de resultados (padrão 10)
        limit = context.get("limit", 10)
        mode = context.get("mode", "frequency")
        tokens = context.get("tokens", [])

        if documents and isinstance(documents[0], dict):
            strategy = TEXTUAL_STRATEGIES.get(mode, TEXTUAL_STRATEGIES["frequency"])
            ranked = strategy.rank(
                tokens,
                documents,
                index_data=context.get("index_data", {}),
            )
            context["results"] = [
                (item["document_id"], item["score"])
                for item in ranked[:limit]
            ]
            return context

        # Conta quantas vezes cada documento apareceu (frequência do termo)
        # Em um sistema real, aqui entrariam outros pesos (TF-IDF, posição, etc.)
        ranking = Counter(documents)

        # Ordena os documentos pela frequência (relevância simples)
        ordered_results = sorted(
            ranking.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Limita a quantidade de resultados retornados
        limited_results = ordered_results[:limit]

        # Salva os resultados ordenados e limitados
        context["results"] = limited_results

        return context
