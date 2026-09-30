"""Request/response schemas for the grant-call screening workflow API."""
from datetime import date
from typing import Any

from pydantic import BaseModel, Field

from services.grant_workflow.models import (
    Applicant,
    Application,
    ApplicationDocument,
    CriterionCategory,
    Finding,
    GrantCall,
    GrantCallStatus,
    Institution,
    PendingUpload,
    ReviewerAction,
    ReviewerDecision,
    ReviewerNote,
    RfpCriterion,
    RfpDocument,
    Role,
    ScreeningRun,
)
from services.grant_workflow.views import ApplicationRow


class GrantCallCreate(BaseModel):
    name: str = Field(min_length=1)
    organization: str = Field(min_length=1)
    reference: str | None = None
    description: str | None = None
    open_date: date | None = None
    close_date: date | None = None
    funding_min: float | None = Field(default=None, ge=0)
    funding_max: float | None = Field(default=None, ge=0)
    currency: str | None = None
    domains: list[str] = Field(default_factory=list)


class GrantCallUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    organization: str | None = Field(default=None, min_length=1)
    reference: str | None = None
    description: str | None = None
    open_date: date | None = None
    close_date: date | None = None
    funding_min: float | None = Field(default=None, ge=0)
    funding_max: float | None = Field(default=None, ge=0)
    currency: str | None = None
    domains: list[str] | None = None
    status: GrantCallStatus | None = None


class RfpUploadResponse(BaseModel):
    rfp_document: RfpDocument
    requirements: list[RfpCriterion]
    grant_call: GrantCall


class RequirementCreate(BaseModel):
    title: str = Field(min_length=1)
    requirement_text: str = Field(min_length=1)
    category: CriterionCategory = CriterionCategory.OTHER
    description: str | None = None
    required: bool = True
    parameters: dict[str, Any] = Field(default_factory=dict)
    administrator_note: str | None = None


class RequirementUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    requirement_text: str | None = Field(default=None, min_length=1)
    category: CriterionCategory | None = None
    description: str | None = None
    required: bool | None = None
    parameters: dict[str, Any] | None = None
    administrator_note: str | None = None


class RequirementVerify(BaseModel):
    decision: str = Field(default="VERIFY", pattern="^(VERIFY|REJECT)$")
    note: str | None = None


class RequirementActive(BaseModel):
    active: bool


class UploadResponse(BaseModel):
    files_received: int
    applications_created: list[str]
    applications_updated: list[str]
    documents_associated: int
    requires_manual_association: list[PendingUpload]
    errors: list[str]
    duplicates: list[str]


class AssociateRequest(BaseModel):
    application_id: str | None = None
    new_reference: str | None = None


class ApplicationDetail(BaseModel):
    application: Application
    row: ApplicationRow
    applicant: Applicant | None
    institution: Institution | None
    documents: list[ApplicationDocument]
    latest_run: ScreeningRun | None


class ScreenRequest(BaseModel):
    application_ids: list[str] | None = None


class FindingDetail(BaseModel):
    finding: Finding
    decisions: list[ReviewerDecision]
    notes: list[ReviewerNote]


class DecisionRequest(BaseModel):
    action: ReviewerAction
    note: str = Field(min_length=1)


class NoteRequest(BaseModel):
    note: str = Field(min_length=1)


class SessionInfo(BaseModel):
    user_id: str
    role: Role | None
    roles: list[Role]
    identity_mode: str = "demo_headers"
    notice: str = (
        "Demo identity: the role is taken from the X-User-Role header and is not authenticated. "
        "Replace with an identity provider before handling real applications."
    )
