from app.services.query_analyzer_service import QueryAnalyzer


def test_query_analyzer_rejects_empty_query():
    analysis = QueryAnalyzer().analyze("")

    assert analysis.is_valid is False
    assert analysis.warnings == ["Consulta vazia."]


def test_query_analyzer_normalizes_accents_case_and_punctuation():
    analysis = QueryAnalyzer().analyze("Relatórios de Estágio!!!")

    assert analysis.normalized_query == "relatorios de estagio"


def test_query_analyzer_tokenizes_and_removes_stopwords():
    analysis = QueryAnalyzer().analyze("documentos sobre estágio supervisionado")

    assert analysis.tokens == ["documentos", "sobre", "estagio", "supervisionado"]
    assert "estagio" in analysis.terms
    assert "supervisionado" in analysis.terms
    assert "sobre" not in analysis.terms


def test_query_analyzer_detects_file_type():
    analysis = QueryAnalyzer().analyze("relatórios de estágio pdf")

    assert analysis.filters.type == "pdf"
    assert analysis.detected_fields.file_types == ["pdf"]


def test_query_analyzer_detects_year():
    analysis = QueryAnalyzer().analyze("atas de reunião 2025")

    assert analysis.filters.year == 2025
    assert analysis.detected_fields.years == [2025]


def test_query_analyzer_detects_exact_phrase():
    analysis = QueryAnalyzer().analyze('"projeto pedagógico" estágio')

    assert analysis.phrases == ["projeto pedagogico"]
    assert "estagio" in analysis.terms
    assert "projeto" not in analysis.terms


def test_query_analyzer_detects_excluded_term():
    analysis = QueryAnalyzer().analyze("estágio -contrato")

    assert "estagio" in analysis.terms
    assert analysis.excluded_terms == ["contrato"]


def test_query_analyzer_detects_operational_intent():
    analysis = QueryAnalyzer().analyze("gerar relatório das buscas sem resultado")

    assert analysis.intent == "generate_report"


def test_query_analyzer_detects_date_range():
    analysis = QueryAnalyzer().analyze("relatórios entre 2024 2025 pdf")

    assert analysis.filters.date_from == "2024-01-01"
    assert analysis.filters.date_to == "2025-12-31"
    assert analysis.intent == "search_with_filters"
