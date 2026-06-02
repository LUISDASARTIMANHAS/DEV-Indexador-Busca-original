from pipeline_busca.src.pipeline.search_pipeline import SearchPipeline
from pipeline_busca.src.stages.queryPreprocessStage import QueryPreprocessStage
from pipeline_busca.src.stages.queryAnalyzeStage import QueryAnalyzeStage
from pipeline_busca.src.stages.searchIndexStage import SearchIndexStage
from pipeline_busca.src.stages.rankResultsStage import RankResultsStage
from pipeline_busca.src.storage.index_repository import IndexRepository
from pipeline_busca.src.stages.queryTokenizeStage import QueryTokenizeStage


class SearchService:

    """
    Classe principal que inicializa o pipeline de busca.
    Serviço principal responsável por executar buscas.
    
    """
    def __init__(self):

        # Repositório que contém o índice invertido
        self.repository = IndexRepository()
        
        # Cria o pipeline de busca
        self.pipeline = SearchPipeline()

        # Adiciona as etapas ao pipeline
        self.pipeline.add_stage(QueryAnalyzeStage())
        self.pipeline.add_stage(QueryPreprocessStage())
        self.pipeline.add_stage(QueryTokenizeStage())
        self.pipeline.add_stage(SearchIndexStage(self.repository))
        self.pipeline.add_stage(RankResultsStage())

    def search(self, query: str, limit: int = 10, mode: str = "frequency"):

        """
        Executa uma busca no sistema.

        :param query: consulta do usuário
        :param limit: quantidade máxima de resultados
        :return: lista de documentos ordenados
        """

        # Executa o pipeline de busca
        result = self.pipeline.run({
            "query": query,
            "limit": limit,
            "mode": mode
        })

        # Retorna apenas os resultados
        return result.get("results", [])
