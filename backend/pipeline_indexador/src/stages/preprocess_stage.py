import re
import unicodedata
from pipeline_indexador.src.pipeline.pipeline_stage import PipelineStage


class PreprocessStage(PipelineStage):
    """
    Etapa de pré-processamento do texto.
    """

    def execute(self, context: dict) -> dict:
        """
        Normaliza o texto.

        :param context: contexto do documento
        :return: contexto atualizado
        """

        text = context.get("text", "")

        # 1. Lowercase the text
        lower_text = text.lower()

        # 2. Remove accents (diacritics)
        normalized_text = unicodedata.normalize('NFKD', lower_text).encode('ascii', 'ignore').decode('utf-8')

        # 3. Remove non-alphanumeric characters (keeping spaces)
        clean_text = re.sub(r"[^\w\s]", "", normalized_text)

        context["processed_text"] = clean_text

        return context
