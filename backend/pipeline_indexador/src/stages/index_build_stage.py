from pipeline_indexador.src.pipeline.pipeline_stage import PipelineStage


class IndexBuildStage(PipelineStage):
    """
    Etapa responsável por atualizar o índice de busca.
    """

    def __init__(self, repository):
        self.repository = repository

    def execute(self, context: dict) -> dict:
        """
        Atualiza o índice.

        :param context: contexto do documento
        :return: contexto atualizado
        """

        document_id = context.get("document_id")
        tokens = context.get("tokens", [])

        self.repository.add_tokens(document_id, tokens)

        return context
