from pipeline_busca.src.pipeline.pipeline_stage import PipelineStage
import re

class QueryPreprocessStage(PipelineStage):

    '''
    Etapa responsável por normalizar a consulta do usuário.
    
    '''
    def execute(self, context: dict) -> dict:
        if context.get("processed_query"):
            return context

        # Obtém a consulta digitada pelo usuário
        query = context.get("query", "")
        
        # Remove pontuação e converte para minúsculas
        query = re.sub(r"[^\w\s]", "", query.lower())

        # Salva o resultado no contexto
        context["processed_query"] = query

        # Retorna o contexto atualizado
        return context
