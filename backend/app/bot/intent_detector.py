from app.utils.text_processing import normalize_text


class IntentDetector:
    SEARCH_TERMS = ("buscar", "busca", "mostrar", "listar", "procurar", "documento", "documentos")
    DETAILS_TERMS = ("detalhe", "detalhes", "abrir", "ver documento", "documento")
    REPORT_TERMS = ("gerar relatorio", "relatorio das buscas", "buscas sem resultado", "metricas")
    HISTORY_TERMS = ("historico", "minhas consultas", "consultas realizadas", "ver consultas")
    HELP_TERMS = ("ajuda", "help", "comandos", "o que voce faz")

    def detect(self, message: str) -> str:
        normalized = normalize_text(message or "")
        if not normalized:
            return "unknown"

        if any(term in normalized for term in self.HELP_TERMS):
            return "help"
        if any(term in normalized for term in self.REPORT_TERMS):
            return "generate_search_report"
        if any(term in normalized for term in self.HISTORY_TERMS):
            return "view_search_history"
        if self._looks_like_details_request(normalized):
            return "get_document_details"
        if self._looks_like_filtered_search(normalized):
            return "search_with_filters"
        if any(term in normalized for term in self.SEARCH_TERMS):
            return "search_documents"
        return "unknown"

    def _looks_like_details_request(self, normalized: str) -> bool:
        if normalized.startswith(("detalhes ", "detalhe ", "abrir ")):
            return True
        return "documento " in normalized and any(term in normalized for term in self.DETAILS_TERMS)

    def _looks_like_filtered_search(self, normalized: str) -> bool:
        file_types = ("pdf", "txt", "csv", "doc", "docx", "xls", "xlsx")
        has_year = any(token.isdigit() and token.startswith("20") for token in normalized.split())
        has_type = any(file_type in normalized.split() for file_type in file_types)
        has_filter_word = any(term in normalized for term in ("categoria", "autor", "antes", "depois", "entre"))
        return has_year or has_type or has_filter_word
