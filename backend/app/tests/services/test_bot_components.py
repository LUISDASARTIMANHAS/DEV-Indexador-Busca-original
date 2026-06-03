from app.bot.entity_extractor import EntityExtractor
from app.bot.intent_detector import IntentDetector
from app.bot.message_formatter import MessageFormatter


def test_bot_detects_search_with_filters_intent():
    detector = IntentDetector()

    assert detector.detect("mostrar PDFs de 2025 sobre estágio") == "search_with_filters"


def test_bot_detects_help_intent():
    detector = IntentDetector()

    assert detector.detect("ajuda") == "help"


def test_bot_extracts_entities_with_query_analyzer():
    entities = EntityExtractor().extract("mostrar PDFs de 2025 sobre estágio supervisionado")

    assert entities["terms"] == ["estagio", "supervisionado"]
    assert entities["filters"]["year"] == 2025
    assert entities["filters"]["type"] == "pdf"
    assert entities["document_id"] is None


def test_bot_extracts_document_id_and_result_position():
    extractor = EntityExtractor()

    assert extractor.extract("detalhes do documento 15")["document_id"] == 15
    assert extractor.extract("detalhes 1")["result_position"] == 1


def test_bot_formats_help_message():
    text = MessageFormatter().format_help()

    assert "buscar documentos" in text.lower()
    assert "mostrar pdfs" in text.lower()
