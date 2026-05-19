from pipeline_busca.src.pipeline.pipeline_stage import PipelineStage


class SearchIndexStage(PipelineStage):

    """
    Etapa responsável por consultar o índice invertido
    e recuperar documentos que contêm os termos buscados.
    """
    
    def __init__(self, repository):
        
        # Repositório que armazena o índice invertido
        self.repository = repository

    def execute(self, context: dict) -> dict:
        
        # Obtém os tokens da consulta
        tokens = context.get("tokens", [])

        documents = self.repository.search_tokens(tokens)

        # Armazena os documentos encontrados no contexto
        context["documents"] = documents

        return context
    
    ''' Exemplo de índice invertido:
       
       indice = {
       "carro": ["doc1", "doc2"],
       "vermelho": ["doc2"]
    
    '''
