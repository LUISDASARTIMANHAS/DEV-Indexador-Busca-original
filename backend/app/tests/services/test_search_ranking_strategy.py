from collections import namedtuple
from datetime import datetime

from app.strategies.search_ranking_strategy import SearchRankingStrategy


Row = namedtuple(
    "Row",
    [
        "document_id",
        "title",
        "document_date",
        "field_type",
        "term",
        "idf",
        "tf",
        "posicao_inicial",
    ],
)


def test_ranking_strategy_prioritizes_coverage_and_position():
    strategy = SearchRankingStrategy()
    rows = [
        Row(1, "Portaria IFES", datetime.utcnow(), "conteudo", "ifes", 1000, 1, 40),
        Row(2, "Relatório de Pesquisa IFES", datetime.utcnow(), "conteudo", "ifes", 1000, 1, 0),
        Row(2, "Relatório de Pesquisa IFES", datetime.utcnow(), "conteudo", "pesquisa", 1000, 1, 2),
    ]

    ranked = strategy.rank(rows, ["ifes", "pesquisa"])

    assert ranked[0]["document_id"] == 2
    assert ranked[0]["score"] > ranked[1]["score"]


def test_ranking_strategy_prioritizes_title_matches():
    strategy = SearchRankingStrategy()
    rows = [
        Row(1, "Portaria Especial IFES", datetime.utcnow(), "titulo", "portaria", 1000, 1, 0),
        Row(2, "Documento Institucional", datetime.utcnow(), "conteudo", "portaria", 1000, 1, 0),
    ]

    ranked = strategy.rank(rows, ["portaria"], raw_query="portaria especial")

    assert ranked[0]["document_id"] == 1
    assert ranked[0]["score"] > ranked[1]["score"]
