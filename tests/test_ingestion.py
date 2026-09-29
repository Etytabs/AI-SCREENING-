from services.ingestion.pipeline import ingest

def test_ingestion_normalizes_text_fields():
    result = ingest("demo", "publication", {"title": "  A\nB  ", "year": 2026})
    assert result.payload["title"] == "A B"
    assert result.payload["year"] == 2026
