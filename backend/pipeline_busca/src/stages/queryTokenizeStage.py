from pipeline_busca.src.pipeline.pipeline_stage import PipelineStage

class QueryTokenizeStage(PipelineStage):

    """
    Etapa responsável por quebrar a consulta em palavras (tokens).
    E converter a consulta do usuário em termos pesquisáveis
    """

    def execute(self, context: dict) -> dict:

        # Recupera o texto normalizado
        query = context.get("processed_query", "")

         # Divide o texto em palavras
        tokens = query.split()

        # Armazena os tokens no contexto
        context["tokens"] = tokens

        # Retorna o contexto atualizado
        return context
    
    
    ''' Exemplo: "carro vermelho"
       
    Resultado: 

    ["carro", "vermelho"]
    '''
