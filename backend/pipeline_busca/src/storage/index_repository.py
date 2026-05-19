import json
import os

class IndexRepository:
    """
    Repositório responsável por armazenar o índice invertido com persistência em arquivo.
    O índice invertido é uma estrutura onde cada termo (palavra)
    aponta para uma lista de documentos que contêm esse termo.
    """

    def __init__(self, storage_path="data/index.json"):
        """
        Construtor da classe.
        Carrega o índice do arquivo se existir.
        """
        self.storage_path = storage_path
        self.index = {}
        self.forward_index = {}
        
        self._load()

    def _load(self):
        """Carrega o índice do armazenamento persistente."""
        # Se estivermos rodando de dentro de pipeline_busca/src, talvez precisemos subir um nível
        # Mas vamos assumir que o comando é rodado da raiz do backend
        path = self.storage_path
        if not os.path.exists(path) and os.path.exists(os.path.join("..", "..", path)):
             path = os.path.join("..", "..", path)

        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.index = data.get("inverted_index", {})
                    self.forward_index = data.get("forward_index", {})
            except Exception as e:
                print(f"Erro ao carregar índice: {e}")

    def add_tokens(self, document_id: str, tokens: list):
        """
        Adiciona tokens ao índice. 
        Nota: Em produção, este repositório seria compartilhado ou leria de uma base comum.
        """
        # A implementação de escrita aqui é para manter paridade, 
        # embora o foco da busca seja leitura.
        unique_tokens = list(set(tokens))
        for token in unique_tokens:
            if token not in self.index:
                self.index[token] = []
            if document_id not in self.index[token]:
                self.index[token].append(document_id)
        
        self.forward_index[document_id] = unique_tokens

    def search(self, term: str):
        """       
        Busca documentos que contêm um termo específico.
        """
        return self.index.get(term, [])

    def search_tokens(self, tokens: list):
        """       
        Busca documentos para vários tokens (palavras).
        """
        documents = []
        for token in tokens:
            docs = self.index.get(token, [])
            documents.extend(docs)
        return list(set(documents)) # Remove duplicatas na busca multi-termo
