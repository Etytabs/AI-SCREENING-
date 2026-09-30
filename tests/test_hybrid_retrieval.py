from ml.semantic_matching.hybrid import hybrid_compare, rank_candidates
from services.evidence.retrieval import select_evidence
from services.ingestion.document import ExtractedDocument, ExtractedPage


class FakeEmbedder:
    model_name = "fake-embedding-v1"

    def encode(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] if "maize" in text.lower() else [0.0, 1.0] for text in texts]


def test_hybrid_without_model_is_explicitly_lexical_only():
    result = hybrid_compare("maize disease", "maize disease")
    assert result.semantic_score is None
    assert result.fused_score == 1.0
    assert result.method == "lexical_only"


def test_hybrid_fuses_embedding_score():
    result = hybrid_compare(
        "maize disease",
        "crop health",
        embedder=FakeEmbedder(),
    )
    assert result.semantic_score == 0.0
    assert result.fused_score == 0.0
    assert result.method == "hybrid:fake-embedding-v1"


def test_rank_candidates_returns_reranked_results():
    results = rank_candidates(
        "maize disease",
        [
            ("a", "maize disease detection"),
            ("b", "water irrigation"),
        ],
        embedder=FakeEmbedder(),
    )
    assert [item.rank for item in results] == [1, 2]
    assert results[0].candidate_id == "a"


def test_evidence_selection_preserves_page_identity():
    document = ExtractedDocument(
        source_id="DOC-1",
        filename="proposal.pdf",
        content_type="application/pdf",
        text="maize disease\nwater irrigation",
        page_count=2,
        extraction_status="success",
        pages=(
            ExtractedPage(1, "maize disease detection"),
            ExtractedPage(2, "water irrigation"),
        ),
    )
    results = select_evidence("maize disease", document, embedder=FakeEmbedder(), top_k=1)
    assert len(results) == 1
    assert results[0].page_number == 1
    assert results[0].rank == 1
    assert results[0].score >= 0.0
