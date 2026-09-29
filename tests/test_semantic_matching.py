from ml.semantic_matching.service import compare_texts

def test_identical_text_has_full_baseline_similarity():
    result = compare_texts("AI research grant", "AI research grant")
    assert result.score == 1.0
