"""Domain model for the grant-call screening workflow.

These Pydantic models are the contract shared by the service layer, the API and the
frontend (mirrored in apps/web/lib/types.ts). Assessment/run vocabularies reuse the
existing enums in ml.evidence.state.
"""
from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field

from ml.evidence.state import EvidenceRelationship, RunState


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def utcnow() -> datetime:
    return datetime.now(UTC)


class Role(StrEnum):
    NCST_GRANT_PERSONNEL = "NCST_GRANT_PERSONNEL"
    GRANT_INSTITUTION = "GRANT_INSTITUTION"
    RESEARCHER_APPLICANT = "RESEARCHER_APPLICANT"
    # Legacy demo roles retained for backward-compatible audit records.
    GRANT_ADMINISTRATOR = "GRANT_ADMINISTRATOR"
    REVIEWER = "REVIEWER"
    SYSTEM_ADMINISTRATOR = "SYSTEM_ADMINISTRATOR"


class DataOrigin(StrEnum):
    SYNTHETIC = "SYNTHETIC"
    UPLOADED = "UPLOADED"
    PROVIDER = "PROVIDER"


class GrantCallStatus(StrEnum):
    DRAFT = "DRAFT"
    REQUIREMENTS_PENDING = "REQUIREMENTS_PENDING"
    READY_FOR_SUBMISSIONS = "READY_FOR_SUBMISSIONS"
    SCREENING = "SCREENING"
    REVIEW = "REVIEW"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"


class CriterionStatus(StrEnum):
    EXTRACTED = "EXTRACTED"
    VERIFIED = "VERIFIED"
    EDITED = "EDITED"
    REJECTED = "REJECTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class CriterionCategory(StrEnum):
    APPLICANT_ELIGIBILITY = "applicant_eligibility"
    INSTITUTION_ELIGIBILITY = "institution_eligibility"
    GEOGRAPHIC_ELIGIBILITY = "geographic_eligibility"
    THEMATIC_PRIORITY = "thematic_priority"
    RESEARCH_DOMAIN = "research_domain"
    PARTNERSHIP = "partnership"
    MANDATORY_DOCUMENT = "mandatory_document"
    BUDGET_LIMIT = "budget_limit"
    FUNDING_AMOUNT = "funding_amount"
    PROJECT_DURATION = "project_duration"
    QUALIFICATIONS = "qualifications"
    ETHICS = "ethics"
    PERMITS = "permits"
    SUBMISSION = "submission"
    DEADLINE = "deadline"
    EVALUATION_CRITERIA = "evaluation_criteria"
    DECLARATIONS = "declarations"
    OTHER = "other"


class ApplicationStatus(StrEnum):
    SUBMITTED = "SUBMITTED"
    IN_REVIEW = "IN_REVIEW"
    REVIEW_COMPLETE = "REVIEW_COMPLETE"


class ProcessingStatus(StrEnum):
    UPLOADED = "UPLOADED"
    EXTRACTED = "EXTRACTED"
    PARTIAL = "PARTIAL"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"


class ScreeningStatus(StrEnum):
    NOT_SCREENED = "NOT_SCREENED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SCREENED = "SCREENED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


class StageName(StrEnum):
    DOCUMENT_EXTRACTION = "DOCUMENT_EXTRACTION"
    REQUIREMENT_MAPPING = "REQUIREMENT_MAPPING"
    ELIGIBILITY = "ELIGIBILITY"
    COMPLETENESS = "COMPLETENESS"
    DUPLICATION = "DUPLICATION"
    TEXT_SIMILARITY = "TEXT_SIMILARITY"
    NOVELTY = "NOVELTY"
    EVIDENCE = "EVIDENCE"


class StageStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class FindingType(StrEnum):
    ELIGIBILITY = "eligibility"
    COMPLETENESS = "completeness"
    DUPLICATION = "duplication"
    PLAGIARISM = "plagiarism"
    NOVELTY = "novelty"


class FindingStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class ReviewState(StrEnum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    DISMISSED = "DISMISSED"
    REVIEW_REQUESTED = "REVIEW_REQUESTED"
    ESCALATED = "ESCALATED"


class ReviewerAction(StrEnum):
    CONFIRM = "CONFIRM"
    DISMISS = "DISMISS"
    REQUEST_REVIEW = "REQUEST_REVIEW"
    ESCALATE = "ESCALATE"


class User(BaseModel):
    id: str
    name: str
    role: Role


class GrantCall(BaseModel):
    id: str = Field(default_factory=lambda: new_id("call"))
    name: str
    organization: str
    reference: str | None = None
    description: str | None = None
    open_date: date | None = None
    close_date: date | None = None
    funding_min: float | None = None
    funding_max: float | None = None
    currency: str | None = None
    domains: list[str] = Field(default_factory=list)
    status: GrantCallStatus = GrantCallStatus.DRAFT
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    created_by: str
    data_origin: DataOrigin = DataOrigin.UPLOADED


class RfpDocument(BaseModel):
    id: str = Field(default_factory=lambda: new_id("rfp"))
    grant_call_id: str
    filename: str
    version: int
    file_hash: str | None
    uploaded_at: datetime = Field(default_factory=utcnow)
    uploaded_by: str
    extraction_status: str
    page_count: int | None = None
    source_type: str = "rfp_upload"
    provenance: dict[str, Any] = Field(default_factory=dict)


ELIGIBILITY_CATEGORIES = frozenset({
    CriterionCategory.APPLICANT_ELIGIBILITY,
    CriterionCategory.INSTITUTION_ELIGIBILITY,
    CriterionCategory.GEOGRAPHIC_ELIGIBILITY,
    CriterionCategory.THEMATIC_PRIORITY,
    CriterionCategory.RESEARCH_DOMAIN,
    CriterionCategory.PARTNERSHIP,
    CriterionCategory.BUDGET_LIMIT,
    CriterionCategory.PROJECT_DURATION,
    CriterionCategory.QUALIFICATIONS,
    CriterionCategory.ETHICS,
    CriterionCategory.PERMITS,
})
COMPLETENESS_CATEGORIES = frozenset({CriterionCategory.MANDATORY_DOCUMENT, CriterionCategory.DECLARATIONS})


class RfpCriterion(BaseModel):
    id: str = Field(default_factory=lambda: new_id("crit"))
    grant_call_id: str
    rfp_document_id: str | None
    criterion_code: str
    category: CriterionCategory
    title: str
    description: str | None = None
    requirement_text: str
    source_page: int | None = None
    source_section: str | None = None
    citation_locator: str | None = None
    source_type: str = "rfp_extraction"
    required: bool = True
    active: bool = True
    extracted_confidence: float | None = None
    status: CriterionStatus = CriterionStatus.EXTRACTED
    parameters: dict[str, Any] = Field(default_factory=dict)
    administrator_note: str | None = None
    verified_by: str | None = None
    verified_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def screening_use(self) -> str:
        if self.category in COMPLETENESS_CATEGORIES:
            return "completeness"
        if self.category in ELIGIBILITY_CATEGORIES:
            return "eligibility"
        return "informational"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_confirmed(self) -> bool:
        return self.status in {CriterionStatus.VERIFIED, CriterionStatus.EDITED}


class Applicant(BaseModel):
    id: str = Field(default_factory=lambda: new_id("applicant"))
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    country: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Institution(BaseModel):
    id: str = Field(default_factory=lambda: new_id("inst"))
    name: str | None = None
    country: str | None = None
    type: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Application(BaseModel):
    id: str = Field(default_factory=lambda: new_id("app"))
    grant_call_id: str
    application_reference: str
    title: str | None = None
    applicant_id: str | None = None
    institution_id: str | None = None
    submitted_at: datetime = Field(default_factory=utcnow)
    status: ApplicationStatus = ApplicationStatus.SUBMITTED
    processing_status: ProcessingStatus = ProcessingStatus.UPLOADED
    screening_status: ScreeningStatus = ScreeningStatus.NOT_SCREENED
    requested_amount: float | None = None
    currency: str | None = None
    domain: str | None = None
    latest_run_id: str | None = None
    last_screened_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    data_origin: DataOrigin = DataOrigin.UPLOADED


class ApplicationDocument(BaseModel):
    id: str = Field(default_factory=lambda: new_id("doc"))
    application_id: str
    filename: str
    document_type: str
    file_hash: str | None
    version: int = 1
    uploaded_at: datetime = Field(default_factory=utcnow)
    uploaded_by: str
    extraction_status: str
    page_count: int | None = None
    error: str | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)


class PendingUpload(BaseModel):
    id: str = Field(default_factory=lambda: new_id("upload"))
    grant_call_id: str
    filename: str
    file_hash: str | None
    extraction_status: str
    reason: str
    uploaded_at: datetime = Field(default_factory=utcnow)
    uploaded_by: str


class DocumentPage(BaseModel):
    page_number: int
    text: str
    lines: list[str] = Field(default_factory=list)


class DocumentContent(BaseModel):
    document_id: str
    filename: str
    owner_type: str
    owner_id: str
    extraction_status: str
    pages: list[DocumentPage]


class StageState(BaseModel):
    stage: StageName
    status: StageStatus = StageStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    message: str | None = None


class ScreeningRun(BaseModel):
    id: str = Field(default_factory=lambda: new_id("run"))
    grant_call_id: str
    application_id: str
    batch_id: str | None = None
    status: RunState = RunState.QUEUED
    started_at: datetime | None = None
    completed_at: datetime | None = None
    pipeline_version: str
    error: str | None = None
    created_by: str
    created_at: datetime = Field(default_factory=utcnow)
    stages: list[StageState] = Field(default_factory=lambda: [StageState(stage=s) for s in StageName])
    finding_ids: list[str] = Field(default_factory=list)
    coverage: dict[str, Any] = Field(default_factory=dict)


class ScreeningBatch(BaseModel):
    id: str = Field(default_factory=lambda: new_id("batch"))
    grant_call_id: str
    run_ids: list[str]
    created_by: str
    created_at: datetime = Field(default_factory=utcnow)


class StageProgress(BaseModel):
    stage: StageName
    completed: int
    failed: int
    total: int
    percent_processed: float


class BatchProgress(BaseModel):
    batch_id: str
    grant_call_id: str
    status: RunState
    total: int
    finished: int
    stages: list[StageProgress]
    runs: list[ScreeningRun]


class FindingEvidence(BaseModel):
    evidence_id: str = Field(default_factory=lambda: new_id("ev"))
    finding_id: str
    source_id: str
    source_type: str
    document_id: str | None = None
    page: int | None = None
    section: str | None = None
    text: str
    field: str | None = None
    relationship: EvidenceRelationship = EvidenceRelationship.SUPPORTS
    citation_locator: str | None = None
    citation_valid: bool | None = None
    created_at: datetime = Field(default_factory=utcnow)


class SimilarityMatch(BaseModel):
    match_id: str = Field(default_factory=lambda: new_id("match"))
    finding_id: str
    source_type: str
    record_id: str
    application_id: str | None = None
    document_id: str | None = None
    title: str | None = None
    similarity_score: float
    lexical_score: float | None = None
    semantic_score: float | None = None
    reranker_score: float | None = None
    match_type: str | None = None
    query_passage: str | None = None
    query_page: int | None = None
    query_document_id: str | None = None
    query_coverage: float | None = None
    source_coverage: float | None = None
    year: int | None = None
    outcome: str | None = None
    matched_section: str | None = None
    matched_page: int | None = None
    matched_passage: str | None = None
    matching_concepts: list[str] = Field(default_factory=list)
    authors: list[str] = Field(default_factory=list)
    published_on: str | None = None
    publisher: str | None = None
    source_url: str | None = None
    doi: str | None = None
    explanation: str
    method: str
    data_origin: DataOrigin = DataOrigin.UPLOADED


class Finding(BaseModel):
    finding_id: str = Field(default_factory=lambda: new_id("finding"))
    screening_run_id: str
    application_id: str
    grant_call_id: str
    criterion_id: str | None = None
    type: FindingType
    status: FindingStatus
    title: str
    signal: str | None = None
    confidence: float | None = None
    explanation: str
    recommended_action: str
    method: str
    created_at: datetime = Field(default_factory=utcnow)
    review_state: ReviewState = ReviewState.PENDING
    evidence: list[FindingEvidence] = Field(default_factory=list)
    matches: list[SimilarityMatch] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class ReviewerDecision(BaseModel):
    id: str = Field(default_factory=lambda: new_id("decision"))
    finding_id: str
    application_id: str
    grant_call_id: str
    action: ReviewerAction
    reviewer_id: str
    reviewer_role: Role
    note: str
    previous_state: ReviewState
    new_state: ReviewState
    created_at: datetime = Field(default_factory=utcnow)


class ReviewerNote(BaseModel):
    id: str = Field(default_factory=lambda: new_id("note"))
    finding_id: str
    application_id: str
    grant_call_id: str
    author_id: str
    note: str
    created_at: datetime = Field(default_factory=utcnow)


class AuditLogEntry(BaseModel):
    event_type: str
    actor: str
    entity_id: str
    grant_call_id: str | None
    timestamp: datetime
    details: dict[str, Any]


class DataSource(BaseModel):
    source_id: str
    provider: str
    source_name: str
    source_type: str
    access_status: str
    required_for_core_workflow: bool
    coverage: str | None = None
    methodology: str | None = None
