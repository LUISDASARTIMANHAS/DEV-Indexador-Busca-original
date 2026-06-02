import json
import os
from collections import Counter

class IndexRepository:
    """
    Repositório responsável por armazenar o índice invertido com persistência em arquivo.
    Suporta atualizações incrementais.
    """

    def __init__(self, storage_path="data/index.json"):
        self.storage_path = storage_path
        # Índice Invertido: termo -> lista de document_ids
        self.index = {}
        # Índice Direto (Forward Index): document_id -> lista de tokens
        # Necessário para limpeza incremental eficiente
        self.forward_index = {}
        self.term_frequencies = {}
        self.document_lengths = {}
        self.document_frequencies = {}
        self.total_documents = 0
        self.average_document_length = 0.0

        self._load()

    def _load(self):
        """Carrega o índice do armazenamento persistente."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
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
                self.index = {}
                self.forward_index = {}
                self.term_frequencies = {}
                self.document_lengths = {}
                self.document_frequencies = {}
                self.total_documents = 0
                self.average_document_length = 0.0

    def _save(self):
        """Salva o índice no armazenamento persistente."""
        self._refresh_statistics()
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "inverted_index": self.index,
                    "forward_index": self.forward_index,
                    "term_frequencies": self.term_frequencies,
                    "document_lengths": self.document_lengths,
                    "document_frequencies": self.document_frequencies,
                    "total_documents": self.total_documents,
                    "average_document_length": self.average_document_length
                }, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Erro ao salvar índice: {e}")

    def _refresh_statistics(self):
        """Atualiza estatísticas usadas por TF-IDF e BM25."""
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

    def remove_document(self, document_id: str):
        """
        Remove um documento do índice.
        
        :param document_id: id do documento a ser removido
        """
        if document_id in self.forward_index:
            tokens = self.forward_index[document_id]
            for token in set(tokens):
                if token in self.index and document_id in self.index[token]:
                    self.index[token].remove(document_id)
                    # Limpa o token se não houver mais documentos
                    if not self.index[token]:
                        del self.index[token]
            del self.forward_index[document_id]
        self.term_frequencies.pop(document_id, None)
        self.document_lengths.pop(document_id, None)

    def add_tokens(self, document_id: str, tokens: list):
        """
        Adiciona tokens ao índice, removendo versões anteriores se existirem.

        :param document_id: id do documento
        :param tokens: lista de termos
        """
        # Garante atualização incremental removendo o estado anterior do documento
        self.remove_document(document_id)

        # Adiciona ao índice invertido
        unique_tokens = list(set(tokens))
        for token in unique_tokens:
            if token not in self.index:
                self.index[token] = []
            if document_id not in self.index[token]:
                self.index[token].append(document_id)

        # Adiciona ao índice direto para futuras atualizações/remoções
        self.forward_index[document_id] = tokens
        self.term_frequencies[document_id] = dict(Counter(tokens))

        self._save()

    def search(self, term: str):
        """
        Busca documentos que contém o termo.

        :param term: termo de busca
        :return: lista de documentos
        """
        return self.index.get(term, [])

    def collection_statistics(self):
        """Retorna estatísticas globais para estratégias de ranking."""
        self._refresh_statistics()
        return {
            "term_frequencies": self.term_frequencies,
            "document_lengths": self.document_lengths,
            "document_frequencies": self.document_frequencies,
            "total_documents": self.total_documents,
            "average_document_length": self.average_document_length,
        }
