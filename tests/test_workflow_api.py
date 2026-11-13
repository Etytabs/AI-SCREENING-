import logging
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from fastapi.testclient import TestClient

import apps.api.routes.publications as publication_routes
from apps.api.dependencies import get_service
from apps.api.main import app
from services.grant_workflow.demo_data import DEMO_RFP_TEXT
from services.grant_workflow.jobs import InlineJobRunner
from services.grant_workflow.providers import MockGrantDataProvider, RIGMSGrantDataProvider
from services.grant_workflow.seed import demo_applications_zip
from services.grant_workflow.service import GrantWorkflowService

ADMIN = {"X-User-Role": "GRANT_ADMINISTRATOR", "X-User-Id": "admin-1"}
REVIEWER = {"X-User-Role": "REVIEWER", "X-User-Id": "reviewer-1"}
SYSADMIN = {"X-User-Role": "SYSTEM_ADMINISTRATOR", "X-User-Id": "sys-1"}


@pytest.fixture
def client():
    service = GrantWorkflowService(
        jobs=InlineJobRunner(), providers=[MockGrantDataProvider(), RIGMSGrantDataProvider(base_url="")],
    )
    app.dependency_overrides[get_service] = lambda: service
    yield TestClient(app)
    app.dependency_overrides.clear()


def create_ready_call(client) -> str:
    call = client.post("/api/v1/grants", json={"name": "API call", "organization": "Fund"}, headers=ADMIN)
    assert call.status_code == 201
    call_id = call.json()["id"]
    upload = client.post(f"/api/v1/grants/{call_id}/rfp", files={"file": ("call.txt", DEMO_RFP_TEXT.encode(), "text/plain")}, headers=ADMIN)
    assert upload.status_code == 201
    for requirement in upload.json()["requirements"]:
        response = client.post(f"/api/v1/requirements/{requirement['id']}/verify", json={"decision": "VERIFY"}, headers=ADMIN)
        assert response.status_code == 200 and response.json()["is_confirmed"]
    confirmed = client.post(f"/api/v1/grants/{call_id}/requirements/confirm", headers=ADMIN)
    assert confirmed.json()["status"] == "READY_FOR_SUBMISSIONS"
    return call_id


def test_identity_headers_and_roles(client):
    assert client.post("/api/v1/grants", json={"name": "x", "organization": "y"}).status_code == 401
    assert client.post("/api/v1/grants", json={"name": "x", "organization": "y"}, headers=REVIEWER).status_code == 403
    secret_role = "SYNTHETIC_ROLE_SECRET_0cf2"
    unknown_role = client.post("/api/v1/grants", json={"name": "x", "organization": "y"}, headers={"X-User-Role": secret_role})
    assert unknown_role.status_code == 400
    assert secret_role not in unknown_role.text
    session = client.get("/api/v1/session", headers=REVIEWER).json()
    assert session["role"] == "REVIEWER" and "not authenticated" in session["notice"]


def test_not_found_and_validation(client):
    assert client.get("/api/v1/grants/missing").status_code == 404
    assert client.post("/api/v1/grants", json={"name": "", "organization": "y"}, headers=ADMIN).status_code == 422


def test_validation_and_unhandled_errors_redact_sensitive_values(client, monkeypatch, caplog):
    secret = "SYNTHETIC_ERROR_SECRET_9f38"
    invalid = client.post(
        "/api/v1/grants",
        json={"name": {"private": secret}, "organization": "Fund"},
        headers=ADMIN,
    )
    assert invalid.status_code == 422
    assert secret not in invalid.text

    service = app.dependency_overrides[get_service]()

    def fail_create(*_args, **_kwargs):
        raise RuntimeError(secret)

    monkeypatch.setattr(service, "create_call", fail_create)
    with caplog.at_level(logging.ERROR):
        failed = client.post("/api/v1/grants", json={"name": "Test", "organization": "Fund"}, headers=ADMIN)
    assert failed.status_code == 500
    assert failed.json() == {"detail": "Internal server error"}
    assert secret not in failed.text
    assert secret not in caplog.text
    assert "RuntimeError" in caplog.text


def test_publication_source_errors_do_not_expose_exception_text(client, monkeypatch, caplog):
    secret = "SYNTHETIC_SOURCE_SECRET_3b17"

    def fail_search(*_args, **_kwargs):
        raise RuntimeError(secret)

    monkeypatch.setattr(publication_routes, "search_source", fail_search)
    with caplog.at_level(logging.WARNING):
        failed_search = client.get("/api/v1/publications/search", params={"q": "grant research"})
        compared = client.get(
            "/api/v1/publications/compare",
            params={"q": "grant research", "sources": "crossref"},
        )
    assert failed_search.status_code == 502
    assert secret not in failed_search.text
    assert compared.status_code == 200
    assert compared.json()["sources_with_errors"] == [{"source": "crossref", "error": "Search failed"}]
    assert secret not in compared.text
    assert secret not in caplog.text
    assert "RuntimeError" in caplog.text


def test_document_extraction_error_is_redacted_from_upload_response(client, monkeypatch):
    import services.ingestion.document as document_module

    secret = "SYNTHETIC_DOCUMENT_SECRET_a82d"
    filename_secret = "SYNTHETIC_FILENAME_SECRET.zip"
    call_id = create_ready_call(client)
    invalid_archive = client.post(
        f"/api/v1/grants/{call_id}/applications/batch",
        files=[("files", (filename_secret, b"not a zip archive", "application/zip"))],
        headers=ADMIN,
    )
    assert invalid_archive.status_code == 422
    assert filename_secret not in invalid_archive.text

    def fail_hash(_path):
        raise OSError(secret)

    monkeypatch.setattr(document_module, "_file_sha256", fail_hash)
    response = client.post(
        f"/api/v1/grants/{call_id}/applications",
        files=[("files", ("proposal.txt", b"proposal content", "text/plain"))],
        headers=ADMIN,
    )
    assert response.status_code == 201
    assert secret not in response.text
    assert response.json()["errors"] == ["An uploaded document could not be processed: Document extraction failed"]
    application_id = response.json()["applications_created"][0]
    detail = client.get(f"/api/v1/applications/{application_id}")
    assert detail.status_code == 200
    assert secret not in detail.text


def test_full_workflow_over_http(client):
    call_id = create_ready_call(client)
    requirements = client.get(f"/api/v1/grants/{call_id}/requirements").json()
    assert requirements and all(r["citation_locator"] for r in requirements)

    upload = client.post(
        f"/api/v1/grants/{call_id}/applications/batch",
        files=[("files", ("apps.zip", demo_applications_zip(), "application/zip"))], headers=ADMIN,
    )
    assert upload.status_code == 201
    body = upload.json()
    assert len(body["applications_created"]) == 5 and body["duplicates"] == []
    uploaded_rows = client.get(f"/api/v1/grants/{call_id}/applications").json()
    assert len(uploaded_rows) == 5
    assert all(row["data_origin"] == "SYNTHETIC" for row in uploaded_rows)

    batch = client.post(f"/api/v1/grants/{call_id}/screen", headers=ADMIN)
    assert batch.status_code == 202
    progress = client.get(f"/api/v1/screening-batches/{batch.json()['id']}").json()
    assert progress["status"] == "COMPLETE" and progress["finished"] == 5

    dashboard = client.get(f"/api/v1/grants/{call_id}/dashboard").json()
    assert dashboard["applications_total"] == 5 and dashboard["grant_call"]["status"] == "REVIEW"

    rows = client.get(f"/api/v1/grants/{call_id}/applications", params={"eligibility": "FAIL"}).json()
    assert [r["application_reference"] for r in rows] == ["DEMO-APP-003"]

    detail = client.get(f"/api/v1/applications/{rows[0]['id']}").json()
    assert detail["latest_run"]["status"] == "COMPLETE" and len(detail["documents"]) == 4

    findings = client.get(f"/api/v1/applications/{rows[0]['id']}/findings").json()
    failing = next(f for f in findings if f["status"] == "FAIL")
    evidence = client.get(f"/api/v1/findings/{failing['finding_id']}/evidence").json()
    assert any(e["source_type"] == "application_document" and e["citation_valid"] for e in evidence)

    document = client.get(f"/api/v1/documents/{detail['documents'][0]['id']}/content").json()
    assert document["pages"] and document["owner_type"] == "application"

    assert client.post(f"/api/v1/findings/{failing['finding_id']}/decision", json={"action": "CONFIRM", "note": "ok"}, headers=SYSADMIN).status_code == 403
    decision = client.post(f"/api/v1/findings/{failing['finding_id']}/decision", json={"action": "CONFIRM", "note": "Verified against page 1"}, headers=REVIEWER)
    assert decision.status_code == 201 and decision.json()["new_state"] == "CONFIRMED"
    assert client.post(f"/api/v1/findings/{failing['finding_id']}/notes", json={"note": "Follow up"}, headers=REVIEWER).status_code == 201
    finding = client.get(f"/api/v1/findings/{failing['finding_id']}").json()
    assert finding["finding"]["review_state"] == "CONFIRMED" and len(finding["notes"]) == 1

    assert client.get(f"/api/v1/grants/{call_id}/audit", headers=REVIEWER).status_code == 403
    audit = client.get(f"/api/v1/grants/{call_id}/audit", headers=SYSADMIN).json()
    assert audit[0]["event_type"] == "finding.note_added"

    report = client.get(f"/api/v1/grants/{call_id}/report").json()
    assert len(report["applications"]) == 5 and "not funding decisions" in report["disclaimer"]
    assert report["synthetic_notice"]
    assert all(application["row"]["data_origin"] == "SYNTHETIC" for application in report["applications"])
    assert any(
        decision["finding_id"] == failing["finding_id"]
        and decision["action"] == "CONFIRM"
        and decision["note"] == "Verified against page 1"
        for decision in report["summary"]["decisions"]
    )
    reported_finding = next(
        finding
        for application in report["applications"]
        for finding in application["findings"]
        if finding["finding_id"] == failing["finding_id"]
    )
    assert reported_finding["review_state"] == "CONFIRMED"
    assert reported_finding["signal"] == failing["signal"]
    assert reported_finding["status"] == failing["status"]
    assert any(
        decision["action"] == "CONFIRM" and decision["note"] == "Verified against page 1"
        for decision in reported_finding["decisions"]
    )


@pytest.mark.parametrize(
    ("omit", "mutate"),
    [
        ("DEMO-APP-005/partner_letter.txt", None),
        (None, "DEMO-APP-001/proposal.txt"),
    ],
    ids=("partial-bundle", "altered-bundle"),
)
def test_partial_or_altered_demo_bundle_is_not_marked_synthetic(client, omit, mutate):
    source = BytesIO(demo_applications_zip())
    altered = BytesIO()
    with ZipFile(source) as original, ZipFile(altered, "w", ZIP_DEFLATED) as result:
        for name in original.namelist():
            if name == omit:
                continue
            content = original.read(name)
            if name == mutate:
                content += b"\nAltered demonstration content"
            result.writestr(name, content)

    call_id = create_ready_call(client)
    upload = client.post(
        f"/api/v1/grants/{call_id}/applications/batch",
        files=[("files", ("applications.zip", altered.getvalue(), "application/zip"))],
        headers=ADMIN,
    )
    assert upload.status_code == 201
    rows = client.get(f"/api/v1/grants/{call_id}/applications").json()
    assert len(rows) == 5
    assert all(row["data_origin"] == "UPLOADED" for row in rows)


def test_upload_edge_cases_over_http(client):
    call_id = create_ready_call(client)
    unsupported = client.post(
        f"/api/v1/grants/{call_id}/applications",
        files=[("files", ("proposal.txt", b"Title: T\nCountry: Rwanda", "text/plain")), ("files", ("notes.odt", b"x", "application/octet-stream"))],
        data={"reference": "REF-1"}, headers=ADMIN,
    )
    assert unsupported.status_code == 201 and unsupported.json()["errors"]
    uploaded_id = unsupported.json()["applications_created"][0]
    assert client.get(f"/api/v1/applications/{uploaded_id}").json()["application"]["data_origin"] == "UPLOADED"
    duplicate = client.post(
        f"/api/v1/grants/{call_id}/applications", files=[("files", ("proposal.txt", b"x", "text/plain"))],
        data={"reference": "REF-1"}, headers=ADMIN,
    )
    assert duplicate.status_code == 409


def test_screening_before_confirmation_is_conflict(client):
    call = client.post("/api/v1/grants", json={"name": "Draft", "organization": "Fund"}, headers=ADMIN).json()
    assert client.post(f"/api/v1/grants/{call['id']}/screen", headers=ADMIN).status_code == 409


def test_sources_and_demo_files(client):
    sources = {s["source_id"]: s for s in client.get("/api/v1/sources").json()}
    assert sources["rigms"]["access_status"] == "NOT_CONFIGURED"
    assert sources["crossref"]["required_for_core_workflow"] is False
    rfp = client.get("/api/v1/demo/rfp")
    assert rfp.status_code == 200 and b"synthetic" in rfp.content.lower()
    archive = client.get("/api/v1/demo/applications.zip")
    assert archive.headers["content-type"] == "application/zip"
