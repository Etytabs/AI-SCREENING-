from io import BytesIO

from fastapi.testclient import TestClient

from apps.api.main import app


def test_grant_document_endpoint_rejects_unsupported_type():
    response = TestClient(app).post(
        "/api/v1/grants/screen-document",
        files={"file": ("proposal.txt", BytesIO(b"demo"), "text/plain")},
    )
    assert response.status_code == 415


def test_grant_document_endpoint_rejects_empty_file():
    response = TestClient(app).post(
        "/api/v1/grants/screen-document",
        files={"file": ("proposal.pdf", BytesIO(b""), "application/pdf")},
    )
    assert response.status_code == 400
