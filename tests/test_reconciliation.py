from services.reconciliation.engine import reconcile_publication


def test_publication_reconciliation_matches_title_and_author():
    result = reconcile_publication(
        "local-1",
        "AI for agriculture in Rwanda",
        "Jane Doe",
        "external-7",
        "AI for agriculture in Rwanda",
        "jane doe",
    )
    assert result["title_similarity"] == 1.0
    assert result["author_similarity"] == 1.0
