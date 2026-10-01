"""Read models: dashboard, application results rows and the screening report.

Aggregates only; no new judgements are made here. Application-level summaries follow a
fixed precedence (FAIL > REVIEW_REQUIRED > PASS) over the findings of the latest run.
"""
from collections import Counter
from typing import Any

from pydantic import BaseModel, Field

from services.grant_workflow.models import (
    Applicant,
    Application,
    ApplicationDocument,
    ApplicationStatus,
    BatchProgress,
    DataOrigin,
    DataSource,
    Finding,
    FindingStatus,
    FindingType,
    GrantCall,
    Institution,
    ReviewerDecision,
    ReviewState,
    RfpCriterion,
    ScreeningStatus,
    utcnow,
)
from services.grant_workflow.screening.orchestrator import active_criteria
from services.grant_workflow.service import GrantWorkflowService

NOT_SCREENED = "NOT_SCREENED"
REVIEWED_STATES = {ReviewState.CONFIRMED, ReviewState.DISMISSED}

DISCLAIMER = (
    "AI-assisted screening signals for human review. Findings are not funding decisions and do not "
    "establish eligibility, duplication, plagiarism or scientific novelty. Every finding must be "
    "verified against its cited evidence by an authorized reviewer."
)
SYNTHETIC_NOTICE = "Contains synthetic demonstration data. Not official NCST/NRIF calls, applications, statistics or decisions."


class ApplicationRow(BaseModel):
    id: str
    application_reference: str
    title: str | None
    applicant_name: str | None
    institution_name: str | None
    country: str | None
    requested_amount: float | None
    currency: str | None
    domain: str | None
    document_count: int
    document_names: list[str]
    unreadable_documents: int
    processing_status: str
    screening_status: str
    status: str
    eligibility: str
    completeness: str
    duplication: str
    text_similarity: str
    novelty: str
    open_findings: int
    reviewed_findings: int
    total_findings: int
    review_progress: str
    last_screened_at: Any = None
    latest_run_id: str | None
    data_origin: DataOrigin


class RecordedDecision(BaseModel):
    """One reviewer decision, joined to the document and finding it was taken on."""

    decision_id: str
    finding_id: str
    application_id: str
    application_reference: str
    document_name: str | None
    finding_type: str
    finding_title: str
    action: str
    review_state: str
    reviewer_id: str
    note: str
    created_at: Any


class DashboardSummary(BaseModel):
    grant_call: GrantCall
    requirements_total: int
    requirements_confirmed: int
    applications_total: int
    screening_status_counts: dict[str, int]
    eligibility_counts: dict[str, int]
    completeness_counts: dict[str, int]
    duplication_flags: int
    text_similarity_flags: int
    novelty_counts: dict[str, int]
    findings_total: int
    findings_by_status: dict[str, int]
    findings_reviewed: int
    findings_pending_review: int
    applications_review_complete: int
    latest_batch: BatchProgress | None
    sources: list[DataSource]
    contains_synthetic_data: bool
    decisions: list[RecordedDecision] = Field(default_factory=list)
    disclaimer: str = DISCLAIMER


class ReportFinding(BaseModel):
    finding_id: str
    type: str
    status: str
    signal: str | None
    title: str
    explanation: str
    review_state: str
    evidence_count: int
    valid_citations: int
    decisions: list[ReviewerDecision] = Field(default_factory=list)


class ReportApplication(BaseModel):
    row: ApplicationRow
    findings: list[ReportFinding]


class ScreeningReport(BaseModel):
    generated_at: Any
    grant_call: GrantCall
    requirements: list[RfpCriterion]
    summary: DashboardSummary
    applications: list[ReportApplication]
    disclaimer: str = DISCLAIMER
    synthetic_notice: str | None = None


def rollup(statuses: list[FindingStatus]) -> str:
    if not statuses:
        return NOT_SCREENED
    if FindingStatus.FAIL in statuses:
        return FindingStatus.FAIL.value
    if FindingStatus.REVIEW_REQUIRED in statuses:
        return FindingStatus.REVIEW_REQUIRED.value
    return FindingStatus.PASS.value


def _signal(findings: list[Finding], kind: FindingType) -> str:
    matching = [f for f in findings if f.type == kind]
    if not matching:
        return NOT_SCREENED
    return matching[0].signal or matching[0].status.value


def _document_names(documents: list[ApplicationDocument]) -> list[str]:
    """Uploaded filenames, proposal first, so a list can be labelled by what was submitted."""
    return [
        document.filename
        for document in sorted(
            documents, key=lambda d: (d.document_type != "proposal", d.uploaded_at, d.filename)
        )
    ]


class WorkflowViews:
    def __init__(self, service: GrantWorkflowService) -> None:
        self.service = service
        self.repo = service.repo

    def row(self, application: Application) -> ApplicationRow:
        applicant = self.repo.get(Applicant, application.applicant_id) if application.applicant_id else None
        institution = self.repo.get(Institution, application.institution_id) if application.institution_id else None
        documents = self.repo.list(ApplicationDocument, application_id=application.id)
        findings = self.service.list_findings(application.id) if application.latest_run_id else []
        screened = application.screening_status not in {ScreeningStatus.NOT_SCREENED, ScreeningStatus.QUEUED, ScreeningStatus.RUNNING}
        if not screened:
            findings = []
        reviewed = sum(1 for f in findings if f.review_state in REVIEWED_STATES)
        needs_review = [f for f in findings if f.status != FindingStatus.PASS]
        open_findings = sum(1 for f in needs_review if f.review_state not in REVIEWED_STATES)
        if not findings:
            progress = NOT_SCREENED
        elif application.status == ApplicationStatus.REVIEW_COMPLETE:
            progress = "COMPLETE"
        elif reviewed:
            progress = "IN_PROGRESS"
        else:
            progress = "PENDING"
        return ApplicationRow(
            id=application.id,
            application_reference=application.application_reference,
            title=application.title,
            applicant_name=applicant.name if applicant else None,
            institution_name=institution.name if institution else None,
            country=institution.country if institution else None,
            requested_amount=application.requested_amount,
            currency=application.currency,
            domain=application.domain,
            document_count=len(documents),
            document_names=_document_names(documents),
            unreadable_documents=sum(1 for d in documents if d.extraction_status != "success"),
            processing_status=application.processing_status.value,
            screening_status=application.screening_status.value,
            status=application.status.value,
            eligibility=rollup([f.status for f in findings if f.type == FindingType.ELIGIBILITY]),
            completeness=rollup([f.status for f in findings if f.type == FindingType.COMPLETENESS]),
            duplication=_signal(findings, FindingType.DUPLICATION),
            text_similarity=_signal(findings, FindingType.PLAGIARISM),
            novelty=_signal(findings, FindingType.NOVELTY),
            open_findings=open_findings,
            reviewed_findings=reviewed,
            total_findings=len(findings),
            review_progress=progress,
            last_screened_at=application.last_screened_at,
            latest_run_id=application.latest_run_id,
            data_origin=application.data_origin,
        )

    def application_rows(self, call_id: str, filters: dict[str, str | None] | None = None) -> list[ApplicationRow]:
        self.service.get_call(call_id)
        rows = [self.row(a) for a in self.repo.list(Application, grant_call_id=call_id)]
        filters = {k: v for k, v in (filters or {}).items() if v}
        query = (filters.pop("q", None) or "").lower().strip()
        if query:
            rows = [
                r for r in rows
                if any(query in (value or "").lower() for value in (r.application_reference, r.title, r.applicant_name, r.institution_name, r.domain))
            ]
        flagged = filters.pop("flagged", None)
        if flagged == "true":
            rows = [r for r in rows if r.duplication == "POSSIBLE_DUPLICATION" or r.text_similarity == "SHARED_PASSAGES_FOUND"]
        for key in ("screening_status", "eligibility", "completeness", "novelty", "review_progress", "processing_status"):
            if key in filters:
                rows = [r for r in rows if getattr(r, key) == filters[key]]
        return sorted(rows, key=lambda r: r.application_reference)

    def decisions(self, call_id: str) -> list[RecordedDecision]:
        """Reviewer decisions already recorded for this call, newest first.

        A read model only: it joins stored decisions to their finding and document and
        makes no judgement of its own.
        """
        self.service.get_call(call_id)
        applications = {a.id: a for a in self.repo.list(Application, grant_call_id=call_id)}
        documents = {
            app_id: _document_names(self.repo.list(ApplicationDocument, application_id=app_id))
            for app_id in applications
        }
        findings = {
            finding.finding_id: finding
            for app_id in applications
            for finding in self.service.list_findings(app_id)
        }
        records = []
        for decision in self.repo.list(ReviewerDecision, grant_call_id=call_id):
            finding = findings.get(decision.finding_id)
            application = applications.get(decision.application_id)
            if finding is None or application is None:
                continue
            names = documents.get(decision.application_id) or []
            records.append(RecordedDecision(
                decision_id=decision.id,
                finding_id=decision.finding_id,
                application_id=decision.application_id,
                application_reference=application.application_reference,
                document_name=names[0] if names else None,
                finding_type=finding.type.value,
                finding_title=finding.title,
                action=decision.action.value,
                review_state=decision.new_state.value,
                reviewer_id=decision.reviewer_id,
                note=decision.note,
                created_at=decision.created_at,
            ))
        records.sort(key=lambda item: item.created_at, reverse=True)
        return records

    def dashboard(self, call_id: str) -> DashboardSummary:
        call = self.service.get_call(call_id)
        rows = self.application_rows(call_id)
        requirements = [c for c in self.repo.list(RfpCriterion, grant_call_id=call_id) if c.active]
        findings = [f for a in self.repo.list(Application, grant_call_id=call_id) for f in self.service.list_findings(a.id)]
        reviewed = sum(1 for f in findings if f.review_state in REVIEWED_STATES)
        sources = self.service.sources()
        return DashboardSummary(
            grant_call=call,
            requirements_total=len(requirements),
            requirements_confirmed=len(active_criteria(self.repo, call_id)),
            applications_total=len(rows),
            screening_status_counts=dict(Counter(r.screening_status for r in rows)),
            eligibility_counts=dict(Counter(r.eligibility for r in rows)),
            completeness_counts=dict(Counter(r.completeness for r in rows)),
            duplication_flags=sum(1 for r in rows if r.duplication == "POSSIBLE_DUPLICATION"),
            text_similarity_flags=sum(1 for r in rows if r.text_similarity == "SHARED_PASSAGES_FOUND"),
            novelty_counts=dict(Counter(r.novelty for r in rows)),
            findings_total=len(findings),
            findings_by_status=dict(Counter(f.status.value for f in findings)),
            findings_reviewed=reviewed,
            findings_pending_review=sum(1 for f in findings if f.status != FindingStatus.PASS and f.review_state not in REVIEWED_STATES),
            applications_review_complete=sum(1 for r in rows if r.review_progress == "COMPLETE"),
            latest_batch=self.service.latest_batch(call_id),
            sources=sources,
            decisions=self.decisions(call_id),
            contains_synthetic_data=call.data_origin == DataOrigin.SYNTHETIC or any(r.data_origin == DataOrigin.SYNTHETIC for r in rows),
        )

    def report(self, call_id: str) -> ScreeningReport:
        summary = self.dashboard(call_id)
        applications = []
        for row in self.application_rows(call_id):
            items = []
            for finding in self.service.list_findings(row.id):
                decisions, _ = self.service.finding_history(finding.finding_id)
                items.append(ReportFinding(
                    finding_id=finding.finding_id, type=finding.type.value, status=finding.status.value,
                    signal=finding.signal, title=finding.title, explanation=finding.explanation,
                    review_state=finding.review_state.value, evidence_count=len(finding.evidence),
                    valid_citations=sum(1 for e in finding.evidence if e.citation_valid), decisions=decisions,
                ))
            applications.append(ReportApplication(row=row, findings=items))
        return ScreeningReport(
            generated_at=utcnow(), grant_call=summary.grant_call,
            requirements=active_criteria(self.repo, call_id), summary=summary, applications=applications,
            synthetic_notice=SYNTHETIC_NOTICE if summary.contains_synthetic_data else None,
        )
