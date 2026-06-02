import re

from app.schemas.query_schema import DetectedFields, QueryAnalysisResult, QueryFilters
from app.utils.text_processing import STOPWORDS_PT_BR, normalize_text, tokenize_text


class QueryAnalyzer:
    MAX_QUERY_LENGTH = 300
    MIN_NORMALIZED_LENGTH = 2
    FILE_TYPES = {"pdf", "txt", "csv", "doc", "docx", "xls", "xlsx"}
    GENERIC_TERMS = {"arquivo", "arquivos"}
    KNOWN_CATEGORIES = {
        "academico",
        "administrativo",
        "estagio",
        "pesquisa",
        "extensao",
        "ensino",
        "resolucao",
        "edital",
        "portaria",
    }
    OPERATOR_WORDS = {"and", "or", "not"}
    DATE_FROM_WORDS = {"depois", "apos", "desde", "partir"}
    DATE_TO_WORDS = {"antes", "ate"}

    def analyze(self, query: str | None) -> QueryAnalysisResult:
        raw_query = query or ""
        warnings: list[str] = []
        is_valid = True

        if not raw_query.strip():
            return QueryAnalysisResult(
                raw_query=raw_query,
                normalized_query="",
                is_valid=False,
                warnings=["Consulta vazia."],
            )

        if len(raw_query) > self.MAX_QUERY_LENGTH:
            is_valid = False
            warnings.append(f"Consulta excede o limite de {self.MAX_QUERY_LENGTH} caracteres.")

        if self._has_invalid_characters(raw_query):
            warnings.append("Caracteres inválidos foram removidos da consulta.")

        phrases = self._extract_phrases(raw_query)
        normalized_query = normalize_text(raw_query)
        tokens = tokenize_text(normalized_query)
        detected_fields = self._detect_fields(tokens)
        excluded_terms = self._extract_excluded_terms(raw_query)
        operators = self._detect_operators(raw_query, phrases)
        filters = self._build_filters(normalized_query, tokens, detected_fields)
        terms = self._extract_terms(tokens, phrases, excluded_terms)

        if len(normalized_query) < self.MIN_NORMALIZED_LENGTH:
            warnings.append("Consulta muito curta.")

        if not terms and not phrases and is_valid:
            warnings.append("Nenhum termo relevante foi identificado após a análise.")

        return QueryAnalysisResult(
            raw_query=raw_query,
            normalized_query=normalized_query,
            tokens=tokens,
            terms=terms,
            filters=filters,
            phrases=phrases,
            excluded_terms=excluded_terms,
            operators=operators,
            detected_fields=detected_fields,
            intent=self._detect_intent(normalized_query, filters),
            is_valid=is_valid,
            warnings=warnings,
        )

    def _has_invalid_characters(self, query: str) -> bool:
        sanitized = re.sub(r'[\w\s"()+\-./,;:]', "", query, flags=re.UNICODE)
        return bool(sanitized.strip())

    def _extract_phrases(self, query: str) -> list[str]:
        phrases: list[str] = []
        for match in re.finditer(r'"([^"]+)"', query):
            normalized_phrase = normalize_text(match.group(1))
            if normalized_phrase:
                phrases.append(normalized_phrase)
        return self._unique(phrases)

    def _extract_excluded_terms(self, query: str) -> list[str]:
        excluded_terms = [
            normalize_text(match.group(1))
            for match in re.finditer(r"(?<!\w)-([A-Za-zÀ-ÿ0-9_]+)", query)
        ]
        return self._unique([term for term in excluded_terms if term])

    def _detect_fields(self, tokens: list[str]) -> DetectedFields:
        years = [int(token) for token in tokens if self._is_year(token)]
        file_types = [token for token in tokens if token in self.FILE_TYPES]
        categories = [token for token in tokens if token in self.KNOWN_CATEGORIES]
        authors = self._detect_authors(tokens)
        return DetectedFields(
            years=self._unique(years),
            file_types=self._unique(file_types),
            categories=self._unique(categories),
            authors=self._unique(authors),
        )

    def _detect_authors(self, tokens: list[str]) -> list[str]:
        if "autor" not in tokens and "autora" not in tokens:
            return []
        authors: list[str] = []
        for marker in ("autor", "autora"):
            if marker not in tokens:
                continue
            start = tokens.index(marker) + 1
            author_tokens = []
            for token in tokens[start:start + 4]:
                if token in STOPWORDS_PT_BR or token in self.OPERATOR_WORDS or self._is_year(token):
                    continue
                if token in self.FILE_TYPES:
                    break
                author_tokens.append(token)
            if author_tokens:
                authors.append(" ".join(author_tokens))
        return authors

    def _build_filters(
        self,
        normalized_query: str,
        tokens: list[str],
        detected_fields: DetectedFields,
    ) -> QueryFilters:
        year = detected_fields.years[0] if detected_fields.years else None
        date_from = None
        date_to = None
        for index, token in enumerate(tokens):
            next_token = tokens[index + 1] if index + 1 < len(tokens) else None
            if next_token and self._is_year(next_token):
                if token in self.DATE_FROM_WORDS:
                    date_from = f"{next_token}-01-01"
                if token in self.DATE_TO_WORDS:
                    date_to = f"{next_token}-12-31"
            if token == "entre" and index + 2 < len(tokens):
                first = tokens[index + 1]
                second = tokens[index + 2]
                if self._is_year(first) and self._is_year(second):
                    date_from = f"{first}-01-01"
                    date_to = f"{second}-12-31"

        category = self._detect_category_from_expression(normalized_query, detected_fields)
        range_dates = self._detect_range_dates(tokens)
        date_from = date_from or range_dates[0]
        date_to = date_to or range_dates[1]
        return QueryFilters(
            year=year,
            type=detected_fields.file_types[0] if detected_fields.file_types else None,
            category=category,
            author=detected_fields.authors[0] if detected_fields.authors else None,
            date_from=date_from,
            date_to=date_to,
        )

    def _detect_category_from_expression(
        self,
        normalized_query: str,
        detected_fields: DetectedFields,
    ) -> str | None:
        match = re.search(r"\bcategoria\s+([a-z0-9_]+)", normalized_query)
        if match:
            return match.group(1)
        return None

    def _detect_range_dates(self, tokens: list[str]) -> tuple[str | None, str | None]:
        if "entre" not in tokens:
            return None, None
        start = tokens.index("entre") + 1
        years_after_marker = [
            token
            for token in tokens[start:]
            if self._is_year(token)
        ]
        if len(years_after_marker) < 2:
            return None, None
        return f"{years_after_marker[0]}-01-01", f"{years_after_marker[1]}-12-31"

    def _extract_terms(
        self,
        tokens: list[str],
        phrases: list[str],
        excluded_terms: list[str],
    ) -> list[str]:
        phrase_tokens = {
            token
            for phrase in phrases
            for token in tokenize_text(phrase)
        }
        excluded_set = set(excluded_terms)
        terms = []
        for token in tokens:
            if token in STOPWORDS_PT_BR:
                continue
            if token in self.FILE_TYPES or token in self.OPERATOR_WORDS:
                continue
            if self._is_year(token) or token in excluded_set or token in phrase_tokens:
                continue
            if token in self.GENERIC_TERMS:
                continue
            terms.append(token)
        return self._unique(terms)

    def _detect_operators(self, query: str, phrases: list[str]) -> list[dict]:
        normalized_query = normalize_text(query)
        tokens = tokenize_text(normalized_query)
        operators: list[dict] = []

        for operator_type in ("and", "or", "not"):
            if operator_type in tokens:
                operator_terms = [
                    token for token in tokens
                    if token not in self.OPERATOR_WORDS
                    and token not in STOPWORDS_PT_BR
                    and not self._is_year(token)
                    and token not in self.FILE_TYPES
                ]
                operators.append({"type": operator_type.upper(), "terms": self._unique(operator_terms)})

        for phrase in phrases:
            operators.append({"type": "PHRASE", "terms": [phrase]})

        excluded_terms = self._extract_excluded_terms(query)
        if excluded_terms:
            operators.append({"type": "NOT", "terms": excluded_terms})

        if re.search(r"(?<!\w)\+", query):
            operators.append({"type": "REQUIRED", "terms": self._extract_required_terms(query)})

        return operators

    def _extract_required_terms(self, query: str) -> list[str]:
        required_terms = [
            normalize_text(match.group(1))
            for match in re.finditer(r"(?<!\w)\+([A-Za-zÀ-ÿ0-9_]+)", query)
        ]
        return self._unique([term for term in required_terms if term])

    def _detect_intent(self, normalized_query: str, filters: QueryFilters) -> str:
        if any(term in normalized_query for term in ("gerar relatorio", "relatorio das buscas", "metricas")):
            return "generate_report"
        if any(term in normalized_query for term in ("historico", "consultas realizadas", "buscas realizadas")):
            return "view_history"
        if any(term in normalized_query for term in ("reindexar", "reindexacao", "reindexe")):
            return "reindex_document"
        if any(term in normalized_query for term in ("abrir documento", "visualizar documento", "mostrar documento")):
            return "open_document"
        if filters.year or filters.type or filters.category or filters.author or filters.date_from or filters.date_to:
            return "search_with_filters"
        if any(term in normalized_query for term in ("buscar", "busca", "mostrar", "listar", "documento", "documentos")):
            return "search_documents"
        return "unknown"

    def _is_year(self, token: str) -> bool:
        return bool(re.fullmatch(r"20\d{2}", token))

    def _unique(self, values: list):
        unique_values = []
        seen = set()
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            unique_values.append(value)
        return unique_values


query_analyzer = QueryAnalyzer()
