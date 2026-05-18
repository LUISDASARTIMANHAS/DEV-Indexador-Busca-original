import json
import os

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
        
        self._load()

    def _load(self):
        """Carrega o índice do armazenamento persistente."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.index = data.get("inverted_index", {})
                    self.forward_index = data.get("forward_index", {})
            except Exception as e:
                print(f"Erro ao carregar índice: {e}")
                self.index = {}
                self.forward_index = {}

    def _save(self):
        """Salva o índice no armazenamento persistente."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "inverted_index": self.index,
                    "forward_index": self.forward_index
                }, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Erro ao salvar índice: {e}")

    def remove_document(self, document_id: str):
        """
        Remove um documento do índice.
        
        :param document_id: id do documento a ser removido
        """
        if document_id in self.forward_index:
            tokens = self.forward_index[document_id]
            for token in tokens:
                if token in self.index and document_id in self.index[token]:
                    self.index[token].remove(document_id)
                    # Limpa o token se não houver mais documentos
                    if not self.index[token]:
                        del self.index[token]
            del self.forward_index[document_id]

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
        self.forward_index[document_id] = unique_tokens
        
        self._save()

    def search(self, term: str):
        """
        Busca documentos que contém o termo.

        :param term: termo de busca
        :return: lista de documentos
        """
        return self.index.get(term, [])
