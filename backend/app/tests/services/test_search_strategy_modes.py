from app.adapters.embedding_adapter import MockEmbeddingAdapter
from app.strategies.bm25_strategy import BM25RankingStrategy
from app.strategies.frequency_strategy import FrequencyRankingStrategy
from app.strategies.hybrid_strategy import HybridRankingStrategy
from app.strategies.semantic_strategy import SemanticRankingStrategy
from app.strategies.tfidf_strategy import TFIDFRankingStrategy
from app.utils.vector_math import cosine_similarity


DOCUMENTS = [
    {
        "document_id": 1,
        "content": "plano plano institucional desenvolvimento",
        "document_length": 4,
    },
    {
        "document_id": 2,
        "content": "plano ensino",
        "document_length": 2,
    },
    {
        "document_id": 3,
        "content": "assistencia estudantil permanencia discente",
        "document_length": 4,
    },
]


def test_frequency_ranks_more_term_occurrences_first():
    ranked = FrequencyRankingStrategy().rank(["plano"], DOCUMENTS)

    assert ranked[0]["document_id"] == 1
    assert ranked[0]["score"] > ranked[1]["score"]


def test_tfidf_values_rarer_terms():
    ranked = TFIDFRankingStrategy().rank(
        ["institucional"],
        DOCUMENTS,
        index_data={"total_documents": len(DOCUMENTS)},
    )

    assert ranked[0]["document_id"] == 1
    assert ranked[0]["score"] > 0


def test_bm25_ranks_more_relevant_document_first():
    ranked = BM25RankingStrategy().rank(
        ["plano", "institucional"],
        DOCUMENTS,
        index_data={"total_documents": len(DOCUMENTS), "average_document_length": 3},
    )

    assert ranked[0]["document_id"] == 1


def test_cosine_similarity_handles_identical_and_orthogonal_vectors():
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_semantic_ranking_with_mock_embeddings():
    adapter = MockEmbeddingAdapter(dimension=64)
    query_embedding = adapter.encode_text("permanencia estudantil")
    documents = [
        {
            "document_id": 1,
            "embedding": adapter.encode_text("assistencia ao estudante e permanencia discente"),
        },
        {
            "document_id": 2,
            "embedding": adapter.encode_text("compras administrativas e contratos"),
        },
    ]

    ranked = SemanticRankingStrategy().rank(
        [],
        documents,
        index_data={"query_embedding": query_embedding},
    )

    assert ranked
    assert ranked[0]["document_id"] == 1
    assert ranked[0]["semantic_score"] > 0


def test_hybrid_combines_textual_and_semantic_scores():
    ranked = HybridRankingStrategy().rank(
        ["plano"],
        [],
        index_data={
            "textual_scores": {1: 10.0, 2: 1.0},
            "semantic_scores": {1: 0.2, 2: 0.9},
            "matched_terms": {1: {"plano"}, 2: set()},
        },
        options={"text_weight": 0.6, "semantic_weight": 0.4},
    )

    assert ranked[0]["document_id"] == 1
    assert ranked[0]["final_score"] > ranked[1]["final_score"]
