from pipeline_indexador.src.pipeline.pipeline_stage import PipelineStage


class TokenizeStage(PipelineStage):
    """
    Etapa responsável por dividir o texto em tokens.
    """

    def execute(self, context: dict) -> dict:
        """
        Divide o texto em palavras.

        :param context: contexto do documento
        :return: contexto atualizado
        """

        processed_text = context.get("processed_text", "")

        tokens = processed_text.split()

        context["tokens"] = tokens

        return context
