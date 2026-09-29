from ml.text_normalization.service import normalize_text


def test_normalize_text_collapses_whitespace():
    assert normalize_text("  AI\n research\tplatform  ") == "AI research platform"
