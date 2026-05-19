from pipeline_busca.src.pipeline.pipeline_stage import PipelineStage
from collections import Counter

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
