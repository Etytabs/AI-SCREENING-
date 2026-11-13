from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from services.auth.demo_auth import DemoAuthentication


@pytest.fixture
def authenticated_client():
    previous_auth = app.state.demo_auth
    app.state.demo_auth = DemoAuthentication(enabled=True)
    test_client = TestClient(app)
    login = test_client.post("/api/v1/auth/login", json={
        "workspace": "GRANT_ADMINISTRATOR",
        "email": "admin@shakahive.demo",
        "password": "Admin123!",
    })
    assert login.status_code == 200
    test_client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"
    yield test_client
    app.state.demo_auth = previous_auth


def test_grant_document_endpoint_rejects_unsupported_type(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/grants/screen-document",
        files={"file": ("proposal.txt", BytesIO(b"demo"), "text/plain")},
    )
    assert response.status_code == 415


def test_grant_document_endpoint_rejects_empty_file(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/grants/screen-document",
        files={"file": ("proposal.pdf", BytesIO(b""), "application/pdf")},
    )
    assert response.status_code == 400
