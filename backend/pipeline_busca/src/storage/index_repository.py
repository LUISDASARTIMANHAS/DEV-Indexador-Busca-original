import json
import os
from collections import Counter

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
        self.term_frequencies = {}
        self.document_lengths = {}
        self.document_frequencies = {}
        self.total_documents = 0
        self.average_document_length = 0.0
        
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
                    self.term_frequencies = data.get("term_frequencies", {})
                    self.document_lengths = data.get("document_lengths", {})
                    self.document_frequencies = data.get("document_frequencies", {})
                    self.total_documents = data.get("total_documents", len(self.forward_index))
                    self.average_document_length = data.get("average_document_length", 0.0)
                    self._refresh_statistics()
            except Exception as e:
                print(f"Erro ao carregar índice: {e}")

    def _refresh_statistics(self):
        if not self.term_frequencies:
            self.term_frequencies = {
                document_id: dict(Counter(tokens))
                for document_id, tokens in self.forward_index.items()
            }
        self.document_lengths = {
            document_id: sum(frequencies.values())
            for document_id, frequencies in self.term_frequencies.items()
        }
        self.total_documents = len(self.term_frequencies)
        if self.total_documents:
            self.average_document_length = (
                sum(self.document_lengths.values()) / self.total_documents
            )
        else:
            self.average_document_length = 0.0
        document_frequencies = {}
        for frequencies in self.term_frequencies.values():
            for token in frequencies:
                document_frequencies[token] = document_frequencies.get(token, 0) + 1
        self.document_frequencies = document_frequencies

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

    def documents_for_tokens(self, tokens: list):
        """Monta documentos candidatos com estatísticas para ranking."""
        self._refresh_statistics()
        candidate_ids = self.search_tokens(tokens)
        documents = []
        for document_id in candidate_ids:
            frequencies = self.term_frequencies.get(document_id, {})
            documents.append({
                "document_id": document_id,
                "term_frequencies": frequencies,
                "terms": {
                    term: {
                        "tf": frequency,
                        "df": self.document_frequencies.get(term, 0),
                    }
                    for term, frequency in frequencies.items()
                },
                "document_length": self.document_lengths.get(document_id, 0),
            })
        return documents

    def collection_statistics(self):
        self._refresh_statistics()
        return {
            "total_documents": self.total_documents,
            "average_document_length": self.average_document_length,
            "document_frequencies": self.document_frequencies,
        }
