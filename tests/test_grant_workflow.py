import io
import zipfile

import pytest

from ml.evidence.state import RunState
from ml.novelty import engine as novelty_engine
from ml.plagiarism.overlap import shared_passages
from services.grant_workflow.demo_data import (
    DEMO_APPLICATION_FILES,
    DEMO_RFP_FILENAME,
    DEMO_RFP_TEXT,
)
from services.grant_workflow.documents import UploadedFile
from services.grant_workflow.jobs import InlineJobRunner
from services.grant_workflow.models import (
    Application,
    CriterionCategory,
    CriterionStatus,
    DataOrigin,
    FindingStatus,
    FindingType,
    GrantCallStatus,
    ReviewerAction,
    ReviewState,
    Role,
    ScreeningStatus,
    StageName,
    StageStatus,
)
from services.grant_workflow.providers import (
    MockGrantDataProvider,
    ProviderUnavailable,
    RIGMSGrantDataProvider,
)
from services.grant_workflow.screening import orchestrator
from services.grant_workflow.seed import demo_applications_zip, seed_demo
from services.grant_workflow.service import (
    Actor,
    ConflictError,
    GrantWorkflowService,
    PermissionDeniedError,
    ValidationFailedError,
)
from services.grant_workflow.text_utils import normalize_for_match
from services.grant_workflow.views import WorkflowViews
from services.sources.registry import SourceAccessStatus

ADMIN = Actor("admin-1", Role.GRANT_ADMINISTRATOR)
REVIEWER = Actor("reviewer-1", Role.REVIEWER)
SYSADMIN = Actor("sysadmin-1", Role.SYSTEM_ADMINISTRATOR)
CALL = {"name": "Test call", "organization": "Test fund", "funding_max": 50_000_000, "currency": "RWF"}

PROPOSAL = """Title: Wetland monitoring for flood early warning
Applicant: Dr. Test Person
Institution: Test University
Institution type: University
Country: Rwanda
Requested amount: RWF 30,000,000
Duration: 12 months
Summary
This project addresses early warning systems for extreme weather in wetland communities.
The principal investigator holds a PhD in hydrology.
A committed partner organisation from the district will co-design the alerts.
"""
UNREADABLE_PDF = b"%PDF-1.4\nthis is not a real pdf body"


class FailingProvider:
    provider_id = "failing_external_source"

    def status(self):
        return SourceAccessStatus.UNAVAILABLE

    def historical_records(self):
        raise RuntimeError("connection refused")


def make_service(**kwargs) -> GrantWorkflowService:
    kwargs.setdefault("providers", [MockGrantDataProvider(), RIGMSGrantDataProvider(base_url="")])
    return GrantWorkflowService(jobs=InlineJobRunner(), **kwargs)


def ready_call(service: GrantWorkflowService):
    call = service.create_call(ADMIN, dict(CALL))
    _, criteria = service.upload_rfp(ADMIN, call.id, DEMO_RFP_FILENAME, DEMO_RFP_TEXT.encode())
    for criterion in criteria:
        service.verify_requirement(ADMIN, criterion.id)
    return service.confirm_requirements(ADMIN, call.id)


def files(**named: str | bytes) -> list[UploadedFile]:
    return [UploadedFile(name.replace("__", "."), value if isinstance(value, bytes) else value.encode()) for name, value in named.items()]


def findings_by_code(service, application_id):
    return {f.details.get("criterion_code", f.type.value): f for f in service.list_findings(application_id)}


@pytest.fixture(scope="module")
def seeded():
    service = make_service()
    call = seed_demo(service)
    apps = {a.application_reference: a for a in service.repo.list(Application, grant_call_id=call.id)}
    return service, call, apps


# -- grant calls & RFP ---------------------------------------------------------------
def test_create_call_requires_admin_and_is_audited():
    service = make_service()
    with pytest.raises(PermissionDeniedError):
        service.create_call(REVIEWER, dict(CALL))
    with pytest.raises(ValidationFailedError):
        service.create_call(ADMIN, {**CALL, "funding_min": 10, "funding_max": 5})
    call = service.create_call(ADMIN, dict(CALL))
    assert call.status == GrantCallStatus.DRAFT
    assert [e.event_type for e in service.audit.entries(grant_call_id=call.id)] == ["grant_call.created"]


def test_rfp_requirements_are_verbatim_and_cited():
    service = make_service()
    call = service.create_call(ADMIN, dict(CALL))
    rfp, criteria = service.upload_rfp(ADMIN, call.id, DEMO_RFP_FILENAME, DEMO_RFP_TEXT.encode())
    assert rfp.version == 1 and rfp.extraction_status == "success"
    assert service.get_call(call.id).status == GrantCallStatus.REQUIREMENTS_PENDING
    source = normalize_for_match(DEMO_RFP_TEXT)
    for criterion in criteria:
        assert normalize_for_match(criterion.requirement_text) in source
        assert criterion.citation_locator and criterion.source_page
    by_category = {}
    for criterion in criteria:
        by_category.setdefault(criterion.category, []).append(criterion)
    assert by_category[CriterionCategory.BUDGET_LIMIT][0].parameters["max_amount"] == 50_000_000
    assert by_category[CriterionCategory.PROJECT_DURATION][0].parameters["max_months"] == 24
    assert by_category[CriterionCategory.GEOGRAPHIC_ELIGIBILITY][0].parameters["country"] == "Rwanda"
    documents = {c.parameters["document_type"] for c in by_category[CriterionCategory.MANDATORY_DOCUMENT]}
    assert documents == {"proposal", "budget", "cv", "partner_letter", "ethics"}
    ethics = next(c for c in by_category[CriterionCategory.MANDATORY_DOCUMENT] if c.parameters["document_type"] == "ethics")
    assert ethics.parameters.get("conditional") is True


def test_rfp_unsupported_file_and_empty_extraction():
    service = make_service()
    call = service.create_call(ADMIN, dict(CALL))
    with pytest.raises(ValidationFailedError):
        service.upload_rfp(ADMIN, call.id, "call.odt", b"content")
    _, criteria = service.upload_rfp(ADMIN, call.id, "call.txt", b"Background information about the fund.")
    assert criteria == []
    with pytest.raises(ConflictError):
        service.confirm_requirements(ADMIN, call.id)


def test_confirmation_requires_every_requirement_verified_or_rejected():
    service = make_service()
    call = service.create_call(ADMIN, dict(CALL))
    _, criteria = service.upload_rfp(ADMIN, call.id, DEMO_RFP_FILENAME, DEMO_RFP_TEXT.encode())
    with pytest.raises(ConflictError, match="awaiting verification"):
        service.confirm_requirements(ADMIN, call.id)
    with pytest.raises(ValidationFailedError):
        service.verify_requirement(ADMIN, criteria[0].id, decision="REJECT")
    service.verify_requirement(ADMIN, criteria[0].id, decision="REJECT", note="Not applicable")
    for criterion in criteria[1:]:
        service.verify_requirement(ADMIN, criterion.id)
    assert service.confirm_requirements(ADMIN, call.id).status == GrantCallStatus.READY_FOR_SUBMISSIONS
    assert criteria[0].id not in {c.id for c in orchestrator.active_criteria(service.repo, call.id)}


def test_edit_add_and_deactivate_requirements():
    service = make_service()
    call = ready_call(service)
    criterion = service.list_requirements(call.id)[0]
    edited = service.update_requirement(ADMIN, criterion.id, {"requirement_text": "Edited requirement text."})
    assert edited.status == CriterionStatus.EDITED and edited.source_type == "administrator_edit"
    added = service.add_requirement(ADMIN, call.id, {"title": "Gender plan", "requirement_text": "Include a gender plan."})
    assert added.status == CriterionStatus.VERIFIED and added.source_type == "administrator"
    service.set_requirement_active(ADMIN, added.id, False)
    assert added.id not in {c.id for c in orchestrator.active_criteria(service.repo, call.id)}
    with pytest.raises(PermissionDeniedError):
        service.update_requirement(REVIEWER, criterion.id, {"title": "x"})
    with pytest.raises(ValidationFailedError):
        service.update_requirement(ADMIN, criterion.id, {"criterion_code": "R99"})


def test_rfp_reupload_supersedes_unconfirmed_requirements():
    service = make_service()
    call = service.create_call(ADMIN, dict(CALL))
    _, first = service.upload_rfp(ADMIN, call.id, DEMO_RFP_FILENAME, DEMO_RFP_TEXT.encode())
    service.verify_requirement(ADMIN, first[0].id)
    rfp2, second = service.upload_rfp(ADMIN, call.id, "v2.txt", DEMO_RFP_TEXT.encode())
    assert rfp2.version == 2
    active_old = [c for c in service.list_requirements(call.id) if c.rfp_document_id == first[0].rfp_document_id and c.active]
    assert [c.id for c in active_old] == [first[0].id]
    assert len({c.criterion_code for c in service.list_requirements(call.id)}) == len(first) + len(second)


# -- applications ------------------------------------------------------------------
def test_applications_need_confirmed_requirements():
    service = make_service()
    call = service.create_call(ADMIN, dict(CALL))
    with pytest.raises(ConflictError):
        service.create_application(ADMIN, call.id, files(proposal__txt=PROPOSAL))


def test_single_application_reads_explicit_metadata_only():
    service = make_service()
    call = ready_call(service)
    application, result = service.create_application(ADMIN, call.id, files(proposal__txt=PROPOSAL))
    assert result.documents_associated == 1
    assert application.title == "Wetland monitoring for flood early warning"
    assert application.requested_amount == 30_000_000 and application.currency == "RWF"
    assert application.domain is None
    row = WorkflowViews(service).row(application)
    assert row.country == "Rwanda" and row.applicant_name == "Dr. Test Person"


def test_empty_submission_is_rejected():
    service = make_service()
    call = ready_call(service)
    with pytest.raises(ValidationFailedError, match="Empty submission"):
        service.create_application(ADMIN, call.id, [])
    with pytest.raises(ValidationFailedError):
        service.upload_applications(ADMIN, call.id, [])


def test_unsupported_and_unreadable_files_are_kept_as_unreadable_documents():
    service = make_service()
    call = ready_call(service)
    application, result = service.create_application(
        ADMIN, call.id, files(proposal__txt=PROPOSAL, notes__odt="x", scan__pdf=UNREADABLE_PDF),
    )
    statuses = {d.filename: d.extraction_status for d in service.application_documents(application.id)}
    assert statuses == {"proposal.txt": "success", "notes.odt": "unsupported_type", "scan.pdf": "extraction_failed"}
    assert application.processing_status.value == "PARTIAL"
    assert len(result.errors) == 2


def test_batch_zip_groups_applications_and_detects_duplicates():
    service = make_service()
    call = ready_call(service)
    archive = demo_applications_zip()
    result = service.upload_applications(ADMIN, call.id, [UploadedFile("apps.zip", archive)])
    assert len(result.applications_created) == 5
    assert result.documents_associated == len(DEMO_APPLICATION_FILES)
    assert result.duplicates == []

    again = service.upload_applications(ADMIN, call.id, [UploadedFile("apps.zip", archive)])
    assert again.applications_created == [] and again.documents_associated == 0
    assert len(again.duplicates) == len(DEMO_APPLICATION_FILES)

    loose = service.upload_applications(ADMIN, call.id, [UploadedFile("orphan.txt", PROPOSAL.encode())])
    assert len(loose.applications_created) == 1
    assert loose.requires_manual_association == []
    created = service.get_application(loose.applications_created[0])
    assert created.application_reference.startswith("APP-")
    assert "orphan.txt" in {d.filename for d in service.application_documents(created.id)}
    assert service.list_pending_uploads(call.id) == []

def test_loose_duplicate_submission_is_screenable_and_comparable():
    service = make_service()
    call = ready_call(service)
    first = service.upload_applications(ADMIN, call.id, [UploadedFile("first.txt", PROPOSAL.encode())])
    second = service.upload_applications(ADMIN, call.id, [UploadedFile("second.txt", PROPOSAL.encode())])
    assert len(first.applications_created) == 1 and len(second.applications_created) == 1
    service.start_screening(ADMIN, call.id, second.applications_created)
    duplication = next(
        f for f in service.list_findings(second.applications_created[0])
        if f.type == FindingType.DUPLICATION
    )
    assert duplication.signal == "POSSIBLE_DUPLICATION"
    assert duplication.matches
    assert duplication.matches[0].application_id == first.applications_created[0]



def test_bad_zip_is_reported():
    service = make_service()
    call = ready_call(service)
    with pytest.raises(ValidationFailedError, match="Empty submission"):
        service.upload_applications(ADMIN, call.id, [UploadedFile("broken.zip", b"not a zip")])


# -- screening -----------------------------------------------------------------------
def test_screening_runs_every_stage_and_moves_call_to_review(seeded):
    service, call, apps = seeded
    assert call.status == GrantCallStatus.REVIEW
    for application in apps.values():
        run = service.get_run(application.latest_run_id)
        assert run.status == RunState.COMPLETE
        assert all(stage.status == StageStatus.COMPLETE for stage in run.stages)
        assert application.screening_status == ScreeningStatus.REVIEW_REQUIRED


def test_eligibility_outcomes(seeded):
    service, _, apps = seeded
    ok = findings_by_code(service, apps["DEMO-APP-001"].id)
    assert all(ok[code].status == FindingStatus.PASS for code in ("R01", "R02", "R03", "R04", "R05", "R06", "R07"))
    outside = findings_by_code(service, apps["DEMO-APP-003"].id)
    assert outside["R04"].status == FindingStatus.FAIL  # Kenya
    assert outside["R06"].status == FindingStatus.FAIL  # RWF 65M
    assert outside["R07"].status == FindingStatus.FAIL  # 30 months
    assert outside["R02"].status == FindingStatus.REVIEW_REQUIRED  # textual criterion never FAILs


def test_missing_evidence_is_review_required_not_fail(seeded):
    service, _, apps = seeded
    thin = findings_by_code(service, apps["DEMO-APP-005"].id)
    for code in ("R06", "R07"):
        assert thin[code].status == FindingStatus.REVIEW_REQUIRED
        assert thin[code].confidence is None
        assert [e.source_type for e in thin[code].evidence] == ["rfp"]


def test_completeness_missing_document_and_conditional(seeded):
    service, _, apps = seeded
    no_cv = findings_by_code(service, apps["DEMO-APP-004"].id)
    assert no_cv["R10"].status == FindingStatus.FAIL
    assert any(e.source_type == "submission_inventory" for e in no_cv["R10"].evidence)
    assert no_cv["R12"].status == FindingStatus.REVIEW_REQUIRED  # conditional ethics requirement
    assert findings_by_code(service, apps["DEMO-APP-003"].id)["R11"].status == FindingStatus.FAIL


def test_unreadable_required_document_is_review_not_fail():
    service = make_service()
    call = ready_call(service)
    application, _ = service.create_application(
        ADMIN, call.id, files(proposal__txt=PROPOSAL, cv__pdf=UNREADABLE_PDF),
    )
    service.start_screening(ADMIN, call.id)
    cv = findings_by_code(service, application.id)["R10"]
    assert cv.status == FindingStatus.REVIEW_REQUIRED
    assert "could not be extracted" in cv.explanation


def test_similarity_signals_never_fail(seeded):
    service, _, apps = seeded
    for application in apps.values():
        for finding in service.list_findings(application.id):
            if finding.type in {FindingType.DUPLICATION, FindingType.PLAGIARISM, FindingType.NOVELTY}:
                assert finding.status != FindingStatus.FAIL


def test_duplication_signal_against_synthetic_history(seeded):
    service, _, apps = seeded
    duplication = findings_by_code(service, apps["DEMO-APP-002"].id)["duplication"]
    assert duplication.signal == "POSSIBLE_DUPLICATION"
    match = duplication.matches[0]
    assert match.record_id == "HIST-2024-118" and match.data_origin == DataOrigin.SYNTHETIC
    assert match.matching_concepts
    assert "does not establish duplication" in duplication.explanation
    assert findings_by_code(service, apps["DEMO-APP-005"].id)["duplication"].status == FindingStatus.PASS


def test_text_similarity_finds_shared_passages(seeded):
    service, _, apps = seeded
    finding = findings_by_code(service, apps["DEMO-APP-004"].id)["plagiarism"]
    assert finding.signal == "SHARED_PASSAGES_FOUND"
    assert finding.matches[0].application_id == apps["DEMO-APP-001"].id
    assert "not proof of plagiarism" in finding.explanation
    assert findings_by_code(service, apps["DEMO-APP-003"].id)["plagiarism"].status == FindingStatus.PASS


def test_novelty_signals(seeded):
    service, _, apps = seeded
    signals = {ref: findings_by_code(service, a.id)["novelty"].signal for ref, a in apps.items()}
    assert signals["DEMO-APP-003"] == "HIGH"
    assert signals["DEMO-APP-002"] == "LOW"
    assert signals["DEMO-APP-005"] == "REVIEW_REQUIRED"
    for application in apps.values():
        novelty = findings_by_code(service, application.id)["novelty"]
        if novelty.signal != "REVIEW_REQUIRED":
            assert "not a determination of scientific novelty" in novelty.explanation


def test_application_evidence_is_verbatim_and_citation_validated(seeded):
    service, _, apps = seeded
    checked = 0
    for application in apps.values():
        for finding in service.list_findings(application.id):
            for evidence in finding.evidence:
                if evidence.source_type != "application_document":
                    continue
                content = service.document_content(evidence.document_id)
                page = next(p for p in content.pages if p.page_number == evidence.page)
                assert evidence.text in page.text
                assert evidence.citation_valid is True and evidence.citation_locator
                checked += 1
    assert checked > 50


def test_failed_ai_component_gives_partial_run(monkeypatch):
    def broken(ctx, run_id):
        raise RuntimeError("model crashed")

    monkeypatch.setitem(orchestrator._STAGE_FUNCTIONS, StageName.NOVELTY, broken)
    service = make_service()
    call = ready_call(service)
    application, _ = service.create_application(ADMIN, call.id, files(proposal__txt=PROPOSAL))
    service.start_screening(ADMIN, call.id)
    run = service.get_run(service.get_application(application.id).latest_run_id)
    assert run.status == RunState.PARTIAL
    assert next(s for s in run.stages if s.stage == StageName.NOVELTY).status == StageStatus.FAILED
    novelty = findings_by_code(service, application.id)["novelty"]
    assert novelty.status == FindingStatus.REVIEW_REQUIRED and novelty.signal == "NOT_ASSESSABLE"
    assert service.get_application(application.id).screening_status == ScreeningStatus.PARTIAL
    assert findings_by_code(service, application.id)["R04"].status == FindingStatus.PASS


def test_no_readable_documents_blocks_run():
    service = make_service()
    call = ready_call(service)
    application, _ = service.create_application(ADMIN, call.id, files(proposal__pdf=UNREADABLE_PDF))
    service.start_screening(ADMIN, call.id)
    run = service.get_run(service.get_application(application.id).latest_run_id)
    assert run.status == RunState.BLOCKED
    assert service.get_application(application.id).screening_status == ScreeningStatus.BLOCKED
    assert [f.title for f in service.list_findings(application.id)] == ["No readable documents"]


def test_external_source_failure_is_reported_not_zero_evidence():
    service = make_service(providers=[FailingProvider(), RIGMSGrantDataProvider(base_url="")])
    call = ready_call(service)
    application, _ = service.create_application(ADMIN, call.id, files(proposal__txt=PROPOSAL))
    service.start_screening(ADMIN, call.id)
    run = service.get_run(service.get_application(application.id).latest_run_id)
    states = {s["source_id"]: s["state"] for s in run.coverage["sources"]}
    assert states == {"same_call_applications": "COMPLETE", "failing_external_source": "FAILED", "rigms": "BLOCKED"}
    duplication = findings_by_code(service, application.id)["duplication"]
    assert duplication.status == FindingStatus.REVIEW_REQUIRED and duplication.signal == "NOT_ASSESSABLE"
    assert "not equivalent to zero evidence" in duplication.explanation
    assert findings_by_code(service, application.id)["novelty"].signal == "REVIEW_REQUIRED"


def test_rigms_unavailable_is_explicit():
    provider = RIGMSGrantDataProvider(base_url="")
    assert provider.status() == SourceAccessStatus.NOT_CONFIGURED
    assert RIGMSGrantDataProvider(base_url="https://rigms.example").status() == SourceAccessStatus.AUTH_REQUIRED
    with pytest.raises(ProviderUnavailable):
        provider.historical_records()
    sources = {s.source_id: s for s in make_service().sources()}
    assert sources["rigms"].access_status == "NOT_CONFIGURED"
    assert not sources["rigms"].required_for_core_workflow
    assert sources["same_call_applications"].required_for_core_workflow


def test_screening_permissions_and_rescreen():
    service = make_service()
    call = ready_call(service)
    application, _ = service.create_application(ADMIN, call.id, files(proposal__txt=PROPOSAL))
    with pytest.raises(PermissionDeniedError):
        service.start_screening(REVIEWER, call.id)
    first = service.start_screening(ADMIN, call.id)
    second = service.start_screening(ADMIN, call.id, [application.id])
    assert first.run_ids != second.run_ids
    assert service.get_application(application.id).latest_run_id == second.run_ids[0]
    assert service.batch_progress(second.id).status == RunState.COMPLETE


# -- review, audit, views ------------------------------------------------------------
def test_reviewer_decisions_notes_and_audit():
    service = make_service()
    call = ready_call(service)
    application, _ = service.create_application(ADMIN, call.id, files(proposal__txt=PROPOSAL))
    service.start_screening(ADMIN, call.id)
    finding = service.list_findings(application.id)[0]
    with pytest.raises(ValidationFailedError):
        service.decide(REVIEWER, finding.finding_id, ReviewerAction.CONFIRM, "  ")
    with pytest.raises(PermissionDeniedError):
        service.decide(SYSADMIN, finding.finding_id, ReviewerAction.CONFIRM, "ok")
    decision = service.decide(REVIEWER, finding.finding_id, ReviewerAction.CONFIRM, "Evidence checked")
    assert decision.previous_state == ReviewState.PENDING and decision.new_state == ReviewState.CONFIRMED
    stored = service.get_finding(finding.finding_id)
    assert stored.review_state == ReviewState.CONFIRMED and stored.status == finding.status
    service.add_note(REVIEWER, finding.finding_id, "Looked at page 1")
    decisions, notes = service.finding_history(finding.finding_id)
    assert len(decisions) == 1 and len(notes) == 1
    assert service.decisions.history(finding.finding_id)
    with pytest.raises(PermissionDeniedError):
        service.audit_log(REVIEWER, call.id)
    events = [e.event_type for e in service.audit_log(SYSADMIN, call.id)]
    for expected in ("grant_call.created", "rfp.uploaded", "requirement.verified", "requirements.confirmed",
                     "application.created", "screening.batch_started", "screening.run_completed",
                     "finding.decision", "finding.note_added"):
        assert expected in events


def test_review_completes_when_every_finding_is_decided():
    service = make_service()
    call = ready_call(service)
    application, _ = service.create_application(ADMIN, call.id, files(proposal__txt=PROPOSAL))
    service.start_screening(ADMIN, call.id)
    for finding in service.list_findings(application.id):
        service.decide(REVIEWER, finding.finding_id, ReviewerAction.DISMISS, "Reviewed")
    assert service.get_application(application.id).status.value == "REVIEW_COMPLETE"
    assert WorkflowViews(service).row(service.get_application(application.id)).review_progress == "COMPLETE"


def test_dashboard_rows_and_report(seeded):
    service, call, _ = seeded
    views = WorkflowViews(service)
    summary = views.dashboard(call.id)
    assert summary.applications_total == 5
    assert summary.contains_synthetic_data
    assert summary.eligibility_counts.get("FAIL") == 1
    assert summary.duplication_flags >= 2 and summary.text_similarity_flags >= 2
    assert summary.latest_batch and summary.latest_batch.finished == 5
    flagged = {r.application_reference for r in views.application_rows(call.id, {"flagged": "true"})}
    assert {"DEMO-APP-002", "DEMO-APP-004"} <= flagged
    assert [r.application_reference for r in views.application_rows(call.id, {"eligibility": "FAIL"})] == ["DEMO-APP-003"]
    assert [r.application_reference for r in views.application_rows(call.id, {"q": "rainwater"})] == ["DEMO-APP-005"]
    report = views.report(call.id)
    assert report.synthetic_notice and "not funding decisions" in report.disclaimer
    assert len(report.applications) == 5


# -- ML primitives -------------------------------------------------------------------
def test_novelty_engine_without_universe_requires_review():
    result = novelty_engine.assess_novelty(PROPOSAL, [])
    assert result.signal == novelty_engine.REVIEW_REQUIRED and result.confidence is None


def test_shared_passages_reports_maximal_runs():
    left = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu unrelated words here"
    right = "prefix alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu suffix"
    overlap = shared_passages(left, right)
    assert len(overlap.passages) == 1 and overlap.passages[0].word_count == 12
    assert shared_passages("short text", right).passages == ()


def test_zip_hidden_and_macos_entries_are_skipped():
    service = make_service()
    call = ready_call(service)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("APP-X/proposal.txt", PROPOSAL)
        archive.writestr("__MACOSX/APP-X/._proposal.txt", "junk")
        archive.writestr("APP-X/.DS_Store", "junk")
    result = service.upload_applications(ADMIN, call.id, [UploadedFile("a.zip", buffer.getvalue())])
    assert result.files_received == 1 and len(result.applications_created) == 1
