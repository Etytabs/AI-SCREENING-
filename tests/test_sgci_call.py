"""The SGCI STISA 2034 call is seeded as a real call awaiting human verification."""
from services.grant_workflow.jobs import InlineJobRunner
from services.grant_workflow.models import (
    CriterionCategory,
    CriterionStatus,
    DataOrigin,
    GrantCallStatus,
    RfpCriterion,
)
from services.grant_workflow.seed import seed_demo
from services.grant_workflow.service import GrantWorkflowService
from services.grant_workflow.sgci_call import SGCI_CALL, seed_sgci_call


def _service() -> GrantWorkflowService:
    return GrantWorkflowService(jobs=InlineJobRunner())


def test_call_carries_the_published_ceiling_and_themes():
    call = seed_sgci_call(_service())
    assert call.reference == "SGCI-STISA-2034"
    assert call.funding_max == 100_000_000 and call.currency == "RWF"
    assert "Artificial Intelligence and Digital Technologies" in call.domains
    # A real call, so it is never labelled synthetic demo content.
    assert call.data_origin == DataOrigin.UPLOADED
    # The source states no deadline or duration, so none is invented.
    assert call.open_date is None and call.close_date is None


def test_requirements_await_administrator_verification():
    service = _service()
    call = seed_sgci_call(service)
    criteria = service.repo.list(RfpCriterion, grant_call_id=call.id)
    assert criteria
    assert all(not c.is_confirmed for c in criteria)
    assert call.status == GrantCallStatus.REQUIREMENTS_PENDING


def test_ceiling_partnership_and_themes_are_extracted_as_structured_criteria():
    service = _service()
    call = seed_sgci_call(service)
    by_category: dict[CriterionCategory, list[RfpCriterion]] = {}
    for criterion in service.repo.list(RfpCriterion, grant_call_id=call.id):
        by_category.setdefault(criterion.category, []).append(criterion)

    budget = by_category[CriterionCategory.BUDGET_LIMIT][0]
    assert budget.parameters["max_amount"] == 100_000_000 and budget.parameters["currency"] == "RWF"

    themes = by_category[CriterionCategory.THEMATIC_PRIORITY][0].parameters["any_of"]
    assert {"Health", "Agriculture", "Energy", "Environment"}.issubset(set(themes))

    assert len(by_category[CriterionCategory.PARTNERSHIP]) == 2  # consortium, and industry partners
    assert by_category[CriterionCategory.GEOGRAPHIC_ELIGIBILITY][0].parameters["country"] == "Rwanda"


def test_the_women_representation_asset_is_flagged_for_review_not_applied_as_a_rule():
    """It is an asset in the competition, not an eligibility rule; a human must classify it."""
    service = _service()
    call = seed_sgci_call(service)
    asset = next(
        c for c in service.repo.list(RfpCriterion, grant_call_id=call.id)
        if "30% women" in c.requirement_text
    )
    assert asset.status == CriterionStatus.NEEDS_REVIEW
    assert not asset.is_confirmed


def test_seeding_twice_does_not_duplicate_the_call():
    service = _service()
    first = seed_sgci_call(service)
    second = seed_sgci_call(service)
    assert first.id == second.id
    assert sum(1 for c in service.list_calls() if c.reference == SGCI_CALL["reference"]) == 1


def test_it_sits_alongside_the_demo_call():
    service = _service()
    seed_demo(service)
    seed_sgci_call(service)
    references = {call.reference for call in service.list_calls()}
    assert {"DEMO-CRG-2026", "SGCI-STISA-2034"} <= references


def test_demo_call_can_be_seeded_without_its_synthetic_submissions():
    """An open call to upload real documents into, with an empty screening list."""
    from services.grant_workflow.models import Application

    service = _service()
    call = seed_demo(service, applications=False)
    assert call.status == GrantCallStatus.READY_FOR_SUBMISSIONS
    assert service.repo.list(Application, grant_call_id=call.id) == []

    seed_sgci_call(service)
    assert len(service.list_calls()) == 2


def test_recorded_decisions_are_exposed_on_the_call_overview():
    """A reviewer's confirm/dismiss is kept and reported against its document."""
    from services.grant_workflow.models import Application, Finding, ReviewerAction, Role
    from services.grant_workflow.service import Actor
    from services.grant_workflow.views import WorkflowViews

    service = _service()
    call = seed_demo(service)
    views = WorkflowViews(service)
    assert views.decisions(call.id) == []

    reviewer = Actor("reviewer-1", Role.GRANT_ADMINISTRATOR)
    application = service.repo.list(Application, grant_call_id=call.id)[0]
    finding = service.repo.list(Finding, application_id=application.id)[0]
    service.decide(reviewer, finding.finding_id, ReviewerAction.CONFIRM, "Checked the cited page.")

    [record] = views.decisions(call.id)
    assert record.review_state == "CONFIRMED" and record.action == "CONFIRM"
    assert record.application_reference == application.application_reference
    assert record.document_name == "proposal.txt"
    assert record.note == "Checked the cited page."
    assert record.finding_title == finding.title
    # and it reaches the overview the administrator actually looks at
    assert views.dashboard(call.id).decisions[0].decision_id == record.decision_id


def test_a_dismissed_finding_is_reported_as_dismissed():
    from services.grant_workflow.models import Application, Finding, ReviewerAction, Role
    from services.grant_workflow.service import Actor
    from services.grant_workflow.views import WorkflowViews

    service = _service()
    call = seed_demo(service)
    application = service.repo.list(Application, grant_call_id=call.id)[0]
    finding = service.repo.list(Finding, application_id=application.id)[0]
    service.decide(Actor("reviewer-1", Role.REVIEWER), finding.finding_id, ReviewerAction.DISMISS, "Not applicable.")

    [record] = WorkflowViews(service).decisions(call.id)
    assert record.review_state == "DISMISSED"
