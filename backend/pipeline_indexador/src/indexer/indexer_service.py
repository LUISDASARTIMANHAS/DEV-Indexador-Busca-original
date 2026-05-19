from pipeline_indexador.src.pipeline.index_pipeline import IndexPipeline
from pipeline_indexador.src.stages.preprocess_stage import PreprocessStage
from pipeline_indexador.src.stages.tokenize_stage import TokenizeStage
from pipeline_indexador.src.stages.index_build_stage import IndexBuildStage
from pipeline_indexador.src.storage.index_repository import IndexRepository


class IndexerService:
    """
    Serviço principal responsável por indexar documentos.
    """

    def __init__(self):

        self.repository = IndexRepository()

        self.pipeline = IndexPipeline(self.repository)

    def index_document(self, document_id: str, text: str):
        """
        Indexa um documento.

        :param document_id: id do documento
        :param text: conteúdo textual
        """

        self.pipeline.run({
            "document_id": document_id,
            "text": text
        })
