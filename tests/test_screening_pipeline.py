from tempfile import NamedTemporaryFile

from services.screening.pipeline import screen_document


def test_screening_rejects_unsupported_documents():
    with NamedTemporaryFile(suffix=".txt") as tmp:
        tmp.write(b"demo")
        tmp.flush()
        result = screen_document(tmp.name, "TEST-001")
    assert result["status"] == "unsupported_type"
    assert result["extraction"]["extraction_status"] == "unsupported_type"
