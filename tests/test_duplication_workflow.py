"""Duplication integration, persistent history, and eligibility isolation."""
from datetime import timedelta

from services.grant_workflow.documents import UploadedFile
from services.grant_workflow.jobs import InlineJobRunner
from services.grant_workflow.models import (
    Application,
    CriterionCategory,
    DataOrigin,
    FindingType,
    Role,
)
from services.grant_workflow.service import Actor, GrantWorkflowService

ADMIN = Actor("duplication-admin", Role.GRANT_ADMINISTRATOR)
PROPOSAL = """Title: Wetland sensor networks for flood warning
Country: Rwanda
Research objectives
We will install solar powered water level sensors along the Nyabarongo wetlands to predict
flood inundation of downstream settlements. Hourly measurements will calibrate a distributed
hydrological model, combining rainfall observations and satellite radar estimates of soil moisture.
Methods
Community volunteers will validate river gauge observations during the rainy season. Forecasts
will be evaluated against independent flood maps and disseminated through district emergency
response teams. A controlled field trial will measure warning lead time and evacuation uptake.
"""
UNRELATED = """Title: Ceramic kiln energy study
Country: Rwanda
Research objectives
The laboratory will measure fracture propagation in recycled ceramic composites using electron
microscopy and tensile testing. Kiln temperature schedules will be varied to quantify thermal
resistance, material porosity and structural strength of construction bricks. Specimens prepared
from industrial slag will undergo accelerated weathering in sealed chambers. The resulting
materials database will guide affordable insulation panel manufacturing and reduce waste from
demolition sites while maintaining structural integrity under compression and bending loads.
"""


def service(archive=None):
    return GrantWorkflowService(jobs=InlineJobRunner(), providers=[], duplication_archive=archive)


def ready_call(workflow):
    call = workflow.create_call(ADMIN, {"name": "Research call", "organization": "Research fund"})
    requirement = workflow.add_requirement(ADMIN, call.id, {
        "title": "Country", "requirement_text": "Applicant must be based in Rwanda",
        "category": CriterionCategory.GEOGRAPHIC_ELIGIBILITY,
        "parameters": {"country": "Rwanda"},
    })
    workflow.verify_requirement(ADMIN, requirement.id)
    return workflow.confirm_requirements(ADMIN, call.id)


def submit(workflow, call, text=PROPOSAL, filename="proposal.txt", **kwargs):
    return workflow.create_application(ADMIN, call.id, [UploadedFile(filename, text.encode())], **kwargs)[0]


def screen(workflow, application):
    workflow.start_screening(ADMIN, application.grant_call_id, [application.id])
    return next(f for f in workflow.list_findings(application.id) if f.type == FindingType.DUPLICATION)


def eligibility(workflow, application):
    return [
        {
            "status": f.status, "signal": f.signal, "confidence": f.confidence,
            "explanation": f.explanation, "method": f.method, "details": f.details,
            "evidence": [e.model_dump(exclude={"evidence_id", "finding_id", "created_at"}) for e in f.evidence],
        }
        for f in workflow.list_findings(application.id) if f.type == FindingType.ELIGIBILITY
    ]


def test_compares_previous_calls_and_excludes_self():
    workflow = service()
    previous = submit(workflow, ready_call(workflow), reference="REUSED-REF")
    application = submit(workflow, ready_call(workflow), reference="REUSED-REF")
    finding = screen(workflow, application)
    assert finding.signal == "POSSIBLE_DUPLICATION"
    assert finding.details["match_type"] == "EXACT_DUPLICATE"
    assert {m.application_id for m in finding.matches} == {previous.id}
    assert finding.matches[0].source_type == "historical_application"
    assert finding.matches[0].query_passage and finding.matches[0].matched_passage
    assert finding.matches[0].query_page == finding.matches[0].matched_page == 1


def test_same_call_identical_submissions_are_compared():
    workflow = service()
    call = ready_call(workflow)
    first, second = submit(workflow, call), submit(workflow, call)
    result = screen(workflow, first)
    assert result.details["match_type"] == "EXACT_DUPLICATE"
    assert {m.application_id for m in result.matches} == {second.id}


def test_later_other_call_submission_does_not_count_as_prior_history():
    workflow = service()
    application = submit(workflow, ready_call(workflow))
    later = submit(workflow, ready_call(workflow))
    workflow.repo.save(later.model_copy(update={"submitted_at": application.submitted_at + timedelta(days=1)}))
    assert screen(workflow, application).signal == "NOT_ASSESSABLE"


def test_no_proposal_does_not_compare_shared_declarations():
    workflow = service()
    call = ready_call(workflow)
    submit(workflow, call, filename="declaration.txt")
    application = submit(workflow, call, filename="declaration.txt")
    assert screen(workflow, application).signal == "NOT_ASSESSABLE"


def test_replaced_proposal_is_not_matched_against_its_old_version():
    workflow = service()
    previous = submit(workflow, ready_call(workflow))
    workflow.add_documents(ADMIN, previous.id, [UploadedFile("proposal.txt", UNRELATED.encode())])
    application = submit(workflow, ready_call(workflow))
    finding = screen(workflow, application)
    assert finding.signal == "NO_SIGNIFICANT_SIMILARITY"
    assert finding.details["compared_records"] == 1


def test_submissions_persist_for_future_comparison_without_duplicate_counts(tmp_path):
    from services.grant_workflow.duplication_archive import DuplicationArchive

    path = tmp_path / "library.sqlite3"
    first_service = service(DuplicationArchive(path))
    previous = submit(first_service, ready_call(first_service))
    current = submit(first_service, ready_call(first_service))
    finding = screen(first_service, current)
    assert finding.details["compared_records"] == 1
    assert {m.application_id for m in finding.matches} == {previous.id}

    restarted = service(DuplicationArchive(path))
    fresh = submit(restarted, ready_call(restarted))
    result = screen(restarted, fresh)
    assert result.details["match_type"] == "EXACT_DUPLICATE"
    assert {m.application_id for m in result.matches} == {previous.id, current.id}


def test_importing_funded_project_changes_duplication_but_not_eligibility(tmp_path):
    from services.grant_workflow.duplication_archive import DuplicationArchive

    archive = DuplicationArchive(tmp_path / "library.sqlite3")
    workflow = service(archive)
    application = submit(workflow, ready_call(workflow))
    assert screen(workflow, application).signal == "NOT_ASSESSABLE"
    before = eligibility(workflow, application)
    assert before
    archive.import_document(
        filename="funded.txt", data=PROPOSAL.encode(), title="Funded wetland research",
        source_type="funded_project", year=2024, reference="FUNDED-2024",
    )
    finding = screen(workflow, application)
    assert finding.details["match_type"] == "EXACT_DUPLICATE"
    assert finding.matches[0].source_type == "funded_project"
    assert finding.matches[0].year == 2024
    assert eligibility(workflow, application) == before


def test_synthetic_demo_submissions_are_not_persisted_as_real_history(tmp_path):
    from services.grant_workflow.duplication_archive import DuplicationArchive

    archive = DuplicationArchive(tmp_path / "library.sqlite3")
    workflow = service(archive)
    submit(workflow, ready_call(workflow), data_origin=DataOrigin.SYNTHETIC)
    assert archive.list_projects() == []


def test_archive_failure_preserves_upload_and_eligibility(tmp_path, monkeypatch):
    from services.grant_workflow.duplication_archive import DuplicationArchive

    archive = DuplicationArchive(tmp_path / "library.sqlite3")
    workflow = service(archive)

    def unavailable(*args, **kwargs):
        raise OSError("Library unavailable")

    monkeypatch.setattr(archive, "snapshot_application", unavailable)
    application = submit(workflow, ready_call(workflow))
    assert workflow.repo.get(Application, application.id) is not None
    monkeypatch.setattr(archive, "historical_records", unavailable)
    finding = screen(workflow, application)
    assert finding.signal == "NOT_ASSESSABLE"
    assert eligibility(workflow, application)
    run = workflow.get_run(workflow.get_application(application.id).latest_run_id)
    assert any(s["source_id"] == archive.provider_id and s["state"] == "FAILED" for s in run.coverage["duplication_sources"])
