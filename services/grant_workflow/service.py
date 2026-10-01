"""Grant-call screening workflow service.

All business rules live here; API route handlers only translate HTTP to these calls.
The service depends on the WorkflowRepository, JobRunner and GrantDataProvider
interfaces so storage, workers and data providers can be replaced independently.
"""
import dataclasses
import hashlib
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING, Any

from ml.evidence.state import ReviewStatus, RunState
from ml.semantic_matching.hybrid import TextEmbedder
from ml.semantic_matching.reranker import CrossEncoderReranker
from services.grant_workflow.audit import WorkflowAudit
from services.grant_workflow.documents import (
    UploadedFile,
    UploadError,
    classify_document,
    expand_uploads,
    extract_bytes,
    group_uploads,
    parse_metadata,
)
from services.grant_workflow.duplication_inputs import narrative_documents
from services.grant_workflow.jobs import JobRunner, ThreadPoolJobRunner
from services.grant_workflow.literature import PublishedLiteratureSource
from services.grant_workflow.models import (
    Applicant,
    Application,
    ApplicationDocument,
    ApplicationStatus,
    AuditLogEntry,
    BatchProgress,
    CriterionCategory,
    CriterionStatus,
    DataOrigin,
    DataSource,
    DocumentContent,
    DocumentPage,
    Finding,
    FindingEvidence,
    GrantCall,
    GrantCallStatus,
    Institution,
    PendingUpload,
    ProcessingStatus,
    ReviewerAction,
    ReviewerDecision,
    ReviewerNote,
    ReviewState,
    RfpCriterion,
    RfpDocument,
    Role,
    ScreeningBatch,
    ScreeningRun,
    ScreeningStatus,
    StageName,
    StageProgress,
    StageStatus,
    new_id,
    utcnow,
)
from services.grant_workflow.providers import (
    GrantDataProvider,
    MockGrantDataProvider,
    RIGMSGrantDataProvider,
    default_source_registry,
)
from services.grant_workflow.repository import InMemoryWorkflowRepository, WorkflowRepository
from services.grant_workflow.rfp_extraction import EXTRACTOR_VERSION, extract_requirements
from services.grant_workflow.screening.orchestrator import (
    FINISHED_RUN_STATES,
    PIPELINE_VERSION,
    ScreeningOrchestrator,
    active_criteria,
)
from services.human_review.decision import DecisionHistory
from services.ingestion.document import ExtractedDocument
from services.sources.registry import SourceRegistry

if TYPE_CHECKING:
    from services.grant_workflow.duplication_archive import DuplicationArchive

logger = logging.getLogger(__name__)


class WorkflowError(Exception):
    status_code = 400


class NotFoundError(WorkflowError):
    status_code = 404


class ConflictError(WorkflowError):
    status_code = 409


class PermissionDeniedError(WorkflowError):
    status_code = 403


class ValidationFailedError(WorkflowError):
    status_code = 422


@dataclass(frozen=True)
class Actor:
    user_id: str
    role: Role


# NCST grant personnel are the operational grant administrators for the real workflow.
# The legacy roles remain supported for backward-compatible demo/audit records.
ADMIN_ROLES = frozenset({Role.NCST_GRANT_PERSONNEL, Role.GRANT_ADMINISTRATOR, Role.SYSTEM_ADMINISTRATOR})
REVIEW_ROLES = frozenset({Role.NCST_GRANT_PERSONNEL, Role.REVIEWER, Role.GRANT_ADMINISTRATOR})
AUDIT_ROLES = frozenset({Role.NCST_GRANT_PERSONNEL, Role.SYSTEM_ADMINISTRATOR, Role.GRANT_ADMINISTRATOR})

OPEN_FOR_SUBMISSIONS = {GrantCallStatus.READY_FOR_SUBMISSIONS, GrantCallStatus.SCREENING, GrantCallStatus.REVIEW}
EDITABLE_REQUIREMENT_FIELDS = {"title", "description", "requirement_text", "category", "required", "parameters", "administrator_note"}
ACTIVE_RUN_STATES = {RunState.QUEUED, RunState.RUNNING}

_DECISION_STATES = {
    ReviewerAction.CONFIRM: ReviewState.CONFIRMED,
    ReviewerAction.DISMISS: ReviewState.DISMISSED,
    ReviewerAction.REQUEST_REVIEW: ReviewState.REVIEW_REQUESTED,
    ReviewerAction.ESCALATE: ReviewState.ESCALATED,
}


@dataclass
class BatchUploadResult:
    files_received: int = 0
    applications_created: list[str] = field(default_factory=list)
    applications_updated: list[str] = field(default_factory=list)
    documents_associated: int = 0
    requires_manual_association: list[PendingUpload] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _processing_status(documents: list[ApplicationDocument]) -> ProcessingStatus:
    ok = [d for d in documents if d.extraction_status == "success"]
    if documents and len(ok) == len(documents):
        return ProcessingStatus.EXTRACTED
    if ok:
        return ProcessingStatus.PARTIAL
    return ProcessingStatus.EXTRACTION_FAILED


class GrantWorkflowService:
    def __init__(
        self,
        repo: WorkflowRepository | None = None,
        *,
        audit: WorkflowAudit | None = None,
        jobs: JobRunner | None = None,
        providers: list[GrantDataProvider] | None = None,
        registry: SourceRegistry | None = None,
        embedder_factory: Callable[[], TextEmbedder | None] = lambda: None,
        reranker_factory: Callable[[], CrossEncoderReranker | None] = lambda: None,
        duplication_archive: "DuplicationArchive | None" = None,
        literature: PublishedLiteratureSource | None = None,
    ) -> None:
        self.repo = repo or InMemoryWorkflowRepository()
        self.audit = audit or WorkflowAudit()
        self.jobs = jobs or ThreadPoolJobRunner()
        rigms = RIGMSGrantDataProvider()
        self.providers = providers if providers is not None else [MockGrantDataProvider(), rigms]
        self.literature = literature or PublishedLiteratureSource()
        self.registry = registry or default_source_registry(rigms, self.literature)
        self.decisions = DecisionHistory()
        self.duplication_archive = duplication_archive
        self.duplication_archive_errors: dict[str, str] = {}
        self.orchestrator = ScreeningOrchestrator(
            self.repo, self.audit, self.providers,
            embedder_factory=embedder_factory, reranker_factory=reranker_factory,
            duplication_archive=duplication_archive,
            duplication_archive_errors=self.duplication_archive_errors,
            literature=self.literature,
        )

    # -- guards -----------------------------------------------------------------
    @staticmethod
    def _require(actor: Actor, roles: frozenset[Role], action: str) -> None:
        if actor.role not in roles:
            allowed = ", ".join(sorted(r.value for r in roles))
            raise PermissionDeniedError(f"{actor.role.value} cannot {action}; requires one of: {allowed}")

    def _get(self, model, item_id: str, label: str):
        item = self.repo.get(model, item_id)
        if item is None:
            raise NotFoundError(f"{label} {item_id} not found")
        return item

    def get_call(self, call_id: str) -> GrantCall:
        return self._get(GrantCall, call_id, "Grant call")

    def _set_call_status(self, call: GrantCall, status: GrantCallStatus, actor: str) -> GrantCall:
        if call.status == status:
            return call
        updated = call.model_copy(update={"status": status, "updated_at": utcnow()})
        self.repo.save(updated)
        self.audit.record("grant_call.status_changed", actor, call.id, call.id,
                          from_status=call.status.value, to_status=status.value)
        return updated

    # -- grant calls ------------------------------------------------------------
    def create_call(self, actor: Actor, data: dict[str, Any], *, data_origin: DataOrigin = DataOrigin.UPLOADED) -> GrantCall:
        self._require(actor, ADMIN_ROLES, "create grant calls")
        if not str(data.get("name") or "").strip() or not str(data.get("organization") or "").strip():
            raise ValidationFailedError("name and organization are required")
        self._validate_call_values(data)
        call = GrantCall(**data, created_by=actor.user_id, data_origin=data_origin)
        self.repo.save(call)
        self.audit.record("grant_call.created", actor.user_id, call.id, call.id, name=call.name)
        return call

    @staticmethod
    def _validate_call_values(data: dict[str, Any]) -> None:
        low, high = data.get("funding_min"), data.get("funding_max")
        if low is not None and high is not None and low > high:
            raise ValidationFailedError("funding_min cannot exceed funding_max")
        opened, closed = data.get("open_date"), data.get("close_date")
        if isinstance(opened, date) and isinstance(closed, date) and opened > closed:
            raise ValidationFailedError("open_date cannot be after close_date")

    def list_calls(self) -> list[GrantCall]:
        return sorted(self.repo.list(GrantCall), key=lambda c: c.created_at, reverse=True)

    def update_call(self, actor: Actor, call_id: str, changes: dict[str, Any]) -> GrantCall:
        self._require(actor, ADMIN_ROLES, "edit grant calls")
        call = self.get_call(call_id)
        status = changes.pop("status", None)
        merged = {**call.model_dump(), **changes}
        self._validate_call_values(merged)
        updated = call.model_copy(update={**changes, "updated_at": utcnow()})
        self.repo.save(updated)
        if changes:
            self.audit.record("grant_call.updated", actor.user_id, call.id, call.id, fields=sorted(changes))
        if status is not None:
            allowed = {GrantCallStatus.CLOSED, GrantCallStatus.ARCHIVED}
            if status not in allowed:
                raise ValidationFailedError("Only CLOSED or ARCHIVED can be set directly; other statuses follow the workflow")
            updated = self._set_call_status(updated, status, actor.user_id)
        return updated

    # -- RFP --------------------------------------------------------------------
    def upload_rfp(self, actor: Actor, call_id: str, filename: str, data: bytes) -> tuple[RfpDocument, list[RfpCriterion]]:
        self._require(actor, ADMIN_ROLES, "upload call documents")
        call = self.get_call(call_id)
        if call.status in {GrantCallStatus.CLOSED, GrantCallStatus.ARCHIVED}:
            raise ConflictError("Cannot change the call document of a closed call")
        rfp_id = new_id("rfp")
        try:
            extracted = extract_bytes(filename, data, rfp_id)
        except UploadError as exc:
            raise ValidationFailedError(str(exc)) from exc
        with self.repo.lock:
            version = len(self.repo.list(RfpDocument, grant_call_id=call_id)) + 1
            rfp = RfpDocument(
                id=rfp_id, grant_call_id=call_id, filename=filename, version=version, file_hash=_sha256(data),
                uploaded_by=actor.user_id, extraction_status=extracted.extraction_status,
                page_count=extracted.page_count, provenance={"extractor": EXTRACTOR_VERSION, "content_type": extracted.content_type},
            )
            self.repo.save(rfp)
            self.repo.save_content(rfp.id, extracted)
            criteria: list[RfpCriterion] = []
            if extracted.extraction_status == "success":
                criteria = extract_requirements(extracted, grant_call_id=call_id, rfp_document_id=rfp.id)
                offset = len(self.repo.list(RfpCriterion, grant_call_id=call_id))
                for index, criterion in enumerate(criteria, start=1):
                    criterion.criterion_code = f"R{offset + index:02d}"
            for old in self.repo.list(RfpCriterion, grant_call_id=call_id):
                if old.rfp_document_id and old.rfp_document_id != rfp.id and not old.is_confirmed and old.active:
                    self.repo.save(old.model_copy(update={"active": False, "administrator_note": f"Superseded by call document v{version}", "updated_at": utcnow()}))
            for criterion in criteria:
                self.repo.save(criterion)
        self.audit.record("rfp.uploaded", actor.user_id, rfp.id, call_id, filename=filename, version=version,
                          extraction_status=extracted.extraction_status, requirements_extracted=len(criteria))
        if call.status in {GrantCallStatus.DRAFT, GrantCallStatus.READY_FOR_SUBMISSIONS} and criteria:
            self._set_call_status(call, GrantCallStatus.REQUIREMENTS_PENDING, actor.user_id)
        return rfp, criteria

    def list_rfps(self, call_id: str) -> list[RfpDocument]:
        self.get_call(call_id)
        return sorted(self.repo.list(RfpDocument, grant_call_id=call_id), key=lambda r: r.version)

    # -- requirements -------------------------------------------------------------
    def list_requirements(self, call_id: str, *, include_inactive: bool = True) -> list[RfpCriterion]:
        self.get_call(call_id)
        criteria = self.repo.list(RfpCriterion, grant_call_id=call_id)
        if not include_inactive:
            criteria = [c for c in criteria if c.active]
        return sorted(criteria, key=lambda c: c.criterion_code)

    def _criterion(self, criterion_id: str) -> RfpCriterion:
        return self._get(RfpCriterion, criterion_id, "Requirement")

    def _requirements_editable(self, criterion: RfpCriterion) -> GrantCall:
        call = self.get_call(criterion.grant_call_id)
        if call.status in {GrantCallStatus.CLOSED, GrantCallStatus.ARCHIVED}:
            raise ConflictError("Requirements of a closed call cannot change")
        return call

    def _after_requirement_change(self, call: GrantCall, actor: Actor) -> None:
        if call.status == GrantCallStatus.READY_FOR_SUBMISSIONS and not self._all_confirmed(call.id):
            self._set_call_status(call, GrantCallStatus.REQUIREMENTS_PENDING, actor.user_id)

    def update_requirement(self, actor: Actor, criterion_id: str, changes: dict[str, Any]) -> RfpCriterion:
        self._require(actor, ADMIN_ROLES, "edit requirements")
        criterion = self._criterion(criterion_id)
        call = self._requirements_editable(criterion)
        unknown = set(changes) - EDITABLE_REQUIREMENT_FIELDS
        if unknown:
            raise ValidationFailedError(f"Fields cannot be edited: {', '.join(sorted(unknown))}")
        if "requirement_text" in changes and not str(changes["requirement_text"]).strip():
            raise ValidationFailedError("requirement_text cannot be empty")
        update = {**changes, "status": CriterionStatus.EDITED, "verified_by": actor.user_id, "verified_at": utcnow(), "updated_at": utcnow()}
        if "requirement_text" in changes and changes["requirement_text"] != criterion.requirement_text:
            update["source_type"] = "administrator_edit"
        updated = criterion.model_copy(update=update)
        self.repo.save(updated)
        self.audit.record("requirement.edited", actor.user_id, criterion.id, criterion.grant_call_id,
                          code=criterion.criterion_code, fields=sorted(changes))
        self._after_requirement_change(call, actor)
        return updated

    def verify_requirement(self, actor: Actor, criterion_id: str, *, decision: str = "VERIFY", note: str | None = None) -> RfpCriterion:
        self._require(actor, ADMIN_ROLES, "verify requirements")
        criterion = self._criterion(criterion_id)
        call = self._requirements_editable(criterion)
        decision = decision.upper()
        if decision not in {"VERIFY", "REJECT"}:
            raise ValidationFailedError("decision must be VERIFY or REJECT")
        status = CriterionStatus.VERIFIED if decision == "VERIFY" else CriterionStatus.REJECTED
        if status == CriterionStatus.REJECTED and not (note or "").strip():
            raise ValidationFailedError("A note is required when rejecting a requirement")
        updated = criterion.model_copy(update={
            "status": status, "verified_by": actor.user_id, "verified_at": utcnow(), "updated_at": utcnow(),
            "administrator_note": note or criterion.administrator_note,
        })
        self.repo.save(updated)
        self.audit.record(f"requirement.{'verified' if status == CriterionStatus.VERIFIED else 'rejected'}",
                          actor.user_id, criterion.id, criterion.grant_call_id, code=criterion.criterion_code, note=note)
        self._after_requirement_change(call, actor)
        return updated

    def add_requirement(self, actor: Actor, call_id: str, data: dict[str, Any]) -> RfpCriterion:
        self._require(actor, ADMIN_ROLES, "add requirements")
        call = self.get_call(call_id)
        if call.status in {GrantCallStatus.CLOSED, GrantCallStatus.ARCHIVED}:
            raise ConflictError("Requirements of a closed call cannot change")
        if not str(data.get("requirement_text") or "").strip() or not str(data.get("title") or "").strip():
            raise ValidationFailedError("title and requirement_text are required")
        with self.repo.lock:
            code = f"R{len(self.repo.list(RfpCriterion, grant_call_id=call_id)) + 1:02d}"
            criterion = RfpCriterion(
                grant_call_id=call_id, rfp_document_id=None, criterion_code=code,
                category=data.get("category") or CriterionCategory.OTHER, title=data["title"],
                description=data.get("description"), requirement_text=data["requirement_text"],
                required=data.get("required", True), parameters=data.get("parameters") or {},
                administrator_note=data.get("administrator_note"), source_type="administrator",
                status=CriterionStatus.VERIFIED, verified_by=actor.user_id, verified_at=utcnow(),
            )
            self.repo.save(criterion)
        self.audit.record("requirement.added", actor.user_id, criterion.id, call_id, code=code, title=criterion.title)
        return criterion

    def set_requirement_active(self, actor: Actor, criterion_id: str, active: bool) -> RfpCriterion:
        self._require(actor, ADMIN_ROLES, "change requirements")
        criterion = self._criterion(criterion_id)
        call = self._requirements_editable(criterion)
        updated = criterion.model_copy(update={"active": active, "updated_at": utcnow()})
        self.repo.save(updated)
        self.audit.record("requirement.activated" if active else "requirement.deactivated", actor.user_id,
                          criterion.id, criterion.grant_call_id, code=criterion.criterion_code)
        self._after_requirement_change(call, actor)
        return updated

    def _all_confirmed(self, call_id: str) -> bool:
        pending = [
            c for c in self.repo.list(RfpCriterion, grant_call_id=call_id)
            if c.active and c.status != CriterionStatus.REJECTED and not c.is_confirmed
        ]
        return not pending

    def confirm_requirements(self, actor: Actor, call_id: str) -> GrantCall:
        self._require(actor, ADMIN_ROLES, "confirm requirements")
        call = self.get_call(call_id)
        if call.status in {GrantCallStatus.CLOSED, GrantCallStatus.ARCHIVED}:
            raise ConflictError("Call is closed")
        pending = [
            c.criterion_code for c in self.repo.list(RfpCriterion, grant_call_id=call_id)
            if c.active and c.status != CriterionStatus.REJECTED and not c.is_confirmed
        ]
        if pending:
            raise ConflictError(f"Requirements still awaiting verification: {', '.join(sorted(pending))}")
        if not active_criteria(self.repo, call_id):
            raise ConflictError("At least one verified, active requirement is needed before accepting submissions")
        self.audit.record("requirements.confirmed", actor.user_id, call_id, call_id,
                          count=len(active_criteria(self.repo, call_id)))
        if call.status in {GrantCallStatus.DRAFT, GrantCallStatus.REQUIREMENTS_PENDING}:
            call = self._set_call_status(call, GrantCallStatus.READY_FOR_SUBMISSIONS, actor.user_id)
        return call

    # -- applications -----------------------------------------------------------
    def _application_hashes(self, application: Application) -> dict[str, str]:
        # Identical files across different applications (e.g. a declaration template) are legitimate.
        return {
            doc.file_hash: f"{application.application_reference}/{doc.filename}"
            for doc in self.repo.list(ApplicationDocument, application_id=application.id)
            if doc.file_hash
        }

    def _stage_document(self, actor: Actor, application_id: str, upload: UploadedFile) -> tuple[ApplicationDocument, ExtractedDocument | None]:
        doc_id = new_id("doc")
        try:
            extracted = extract_bytes(upload.filename, upload.data, doc_id)
            error = extracted.error
            status = extracted.extraction_status
            if status == "success" and not extracted.text.strip():
                status, error = "no_text", "No extractable text (the file may be scanned or empty)"
        except UploadError as exc:
            extracted, status, error = None, "unsupported_type" if upload.data else "empty_file", str(exc)
        document_type = classify_document(upload.filename, extracted if status == "success" else None)
        existing = [d for d in self.repo.list(ApplicationDocument, application_id=application_id) if d.filename == upload.filename]
        meta = ApplicationDocument(
            id=doc_id, application_id=application_id, filename=upload.filename, document_type=document_type,
            file_hash=_sha256(upload.data) if upload.data else None, version=len(existing) + 1,
            uploaded_by=actor.user_id, extraction_status=status, page_count=extracted.page_count if extracted else None,
            error=error, provenance={"upload_path": upload.path},
        )
        self.repo.save(meta)
        if extracted is not None:
            self.repo.save_content(doc_id, extracted)
        return meta, (extracted if status == "success" else None)

    def _next_reference(self, call_id: str) -> str:
        count = len(self.repo.list(Application, grant_call_id=call_id))
        existing = {a.application_reference for a in self.repo.list(Application, grant_call_id=call_id)}
        index = count + 1
        while f"APP-{index:04d}" in existing:
            index += 1
        return f"APP-{index:04d}"

    def _apply_metadata(self, application: Application) -> Application:
        documents = self.repo.list(ApplicationDocument, application_id=application.id)
        readable = [(d.document_type, self.repo.get_content(d.id)) for d in documents if d.extraction_status == "success"]
        metadata = parse_metadata([(t, c) for t, c in readable if c is not None])
        applicant = self.repo.get(Applicant, application.applicant_id) if application.applicant_id else Applicant()
        institution = self.repo.get(Institution, application.institution_id) if application.institution_id else Institution()
        applicant = applicant.model_copy(update={
            "name": applicant.name or metadata.applicant_name, "email": applicant.email or metadata.email,
            "phone": applicant.phone or metadata.phone, "metadata": {**applicant.metadata, "sources": metadata.sources},
        })
        institution = institution.model_copy(update={
            "name": institution.name or metadata.institution_name, "country": institution.country or metadata.country,
            "type": institution.type or metadata.institution_type,
        })
        self.repo.save(applicant)
        self.repo.save(institution)
        updated = application.model_copy(update={
            "title": application.title or metadata.title,
            "requested_amount": application.requested_amount if application.requested_amount is not None else metadata.requested_amount,
            "currency": application.currency or metadata.currency,
            "domain": application.domain or metadata.domain,
            "applicant_id": applicant.id, "institution_id": institution.id,
            "processing_status": _processing_status(documents), "updated_at": utcnow(),
        })
        self.repo.save(updated)
        self._archive_for_duplication(updated)
        return updated

    def _archive_for_duplication(self, application: Application) -> None:
        if self.duplication_archive is None or application.data_origin == DataOrigin.SYNTHETIC:
            return
        selected = narrative_documents([
            (meta, self.repo.get_content(meta.id))
            for meta in self.repo.list(ApplicationDocument, application_id=application.id)
        ])
        readable = [
            (meta, doc) for meta, doc in selected
            if doc is not None and meta.extraction_status == "success" and doc.text.strip()
        ]
        if not readable:
            return
        institution = self.repo.get(Institution, application.institution_id) if application.institution_id else None
        try:
            self.duplication_archive.snapshot_application(
                application, readable, organization=institution.name if institution else None,
            )
            self.duplication_archive_errors.pop(application.id, None)
        except Exception:
            # Archiving is independent of submission and eligibility; expose a
            # coverage failure to duplication instead of rejecting the upload.
            logger.exception("Could not archive application %s for duplication", application.id)
            self.duplication_archive_errors[application.id] = "A submitted proposal could not be saved to the comparison library."

    def _open_call(self, call_id: str) -> GrantCall:
        call = self.get_call(call_id)
        if call.status not in OPEN_FOR_SUBMISSIONS:
            raise ConflictError(f"Call is {call.status.value}; confirm the requirements before accepting applications")
        return call

    def create_application(self, actor: Actor, call_id: str, files: list[UploadedFile], *, reference: str | None = None,
                           data_origin: DataOrigin = DataOrigin.UPLOADED) -> tuple[Application, BatchUploadResult]:
        self._require(actor, ADMIN_ROLES, "upload applications")
        self._open_call(call_id)
        expanded, errors = expand_uploads(files)
        if not expanded:
            raise ValidationFailedError("Empty submission: no files were provided" + (f" ({'; '.join(errors)})" if errors else ""))
        result = BatchUploadResult(files_received=len(expanded), errors=errors)
        with self.repo.lock:
            reference = (reference or "").strip() or self._next_reference(call_id)
            if any(a.application_reference == reference for a in self.repo.list(Application, grant_call_id=call_id)):
                raise ConflictError(f"Application reference {reference} already exists in this call")
            application = Application(grant_call_id=call_id, application_reference=reference, data_origin=data_origin)
            self.repo.save(application)
            application = self._add_files(actor, application, expanded, result)
        result.applications_created.append(application.id)
        self.audit.record("application.created", actor.user_id, application.id, call_id,
                          reference=reference, documents=result.documents_associated, duplicates=result.duplicates)
        return application, result

    def _add_files(self, actor: Actor, application: Application, files: list[UploadedFile], result: BatchUploadResult) -> Application:
        hashes = self._application_hashes(application)
        for upload in files:
            digest = _sha256(upload.data) if upload.data else None
            if digest and digest in hashes:
                result.duplicates.append(f"{upload.path} duplicates {hashes[digest]}")
                continue
            meta, _ = self._stage_document(actor, application.id, upload)
            if meta.error:
                result.errors.append(f"{upload.path}: {meta.error}")
            if digest:
                hashes[digest] = f"{application.application_reference}/{upload.filename}"
            result.documents_associated += 1
        return self._apply_metadata(application)

    def upload_applications(self, actor: Actor, call_id: str, files: list[UploadedFile], *,
                            data_origin: DataOrigin = DataOrigin.UPLOADED) -> BatchUploadResult:
        self._require(actor, ADMIN_ROLES, "upload applications")
        self._open_call(call_id)
        expanded, errors = expand_uploads(files)
        result = BatchUploadResult(files_received=len(expanded), errors=list(errors))
        if not expanded:
            raise ValidationFailedError("Empty submission: no files were provided" + (f" ({'; '.join(errors)})" if errors else ""))
        groups, unassigned = group_uploads(expanded)
        with self.repo.lock:
            by_reference = {a.application_reference: a for a in self.repo.list(Application, grant_call_id=call_id)}
            for reference, members in groups.items():
                existing = by_reference.get(reference)
                application = existing or Application(grant_call_id=call_id, application_reference=reference, data_origin=data_origin)
                if existing is None:
                    self.repo.save(application)
                before = result.documents_associated
                application = self._add_files(actor, application, members, result)
                added = result.documents_associated > before
                if existing is None and not added:
                    self.repo.delete(Application, application.id)
                elif existing is None:
                    result.applications_created.append(application.id)
                    by_reference[reference] = application
                elif added:
                    result.applications_updated.append(application.id)
            # An unlabelled upload is still a valid research submission. If the
            # administrator uploads a loose file, create one application for that file
            # and give it a generated reference. Folder/prefix grouping above remains
            # available when several files belong to the same submission.
            #
            # This avoids making file naming conventions a prerequisite for screening.
            # Exact duplicate files are intentionally retained as separate applications:
            # the screening duplication stage must be able to flag the second submission
            # against the first one in the same grant call.
            for upload in unassigned:
                reference = self._next_reference(call_id)
                application = Application(
                    grant_call_id=call_id,
                    application_reference=reference,
                    data_origin=data_origin,
                )
                self.repo.save(application)
                before = result.documents_associated
                application = self._add_files(actor, application, [upload], result)
                added = result.documents_associated > before
                if added:
                    result.applications_created.append(application.id)
                else:
                    self.repo.delete(Application, application.id)
                    result.errors.append(f"{upload.path}: no document could be associated")
        self.audit.record(
            "applications.batch_uploaded", actor.user_id, call_id, call_id,
            files_received=result.files_received, created=len(result.applications_created),
            updated=len(result.applications_updated), pending=len(result.requires_manual_association),
            duplicates=len(result.duplicates), errors=len(result.errors),
        )
        return result

    def add_documents(self, actor: Actor, application_id: str, files: list[UploadedFile]) -> tuple[Application, BatchUploadResult]:
        self._require(actor, ADMIN_ROLES, "upload application documents")
        application = self._get(Application, application_id, "Application")
        self._open_call(application.grant_call_id)
        expanded, errors = expand_uploads(files)
        if not expanded:
            raise ValidationFailedError("Empty submission: no files were provided")
        result = BatchUploadResult(files_received=len(expanded), errors=errors)
        with self.repo.lock:
            application = self._add_files(actor, application, expanded, result)
        result.applications_updated.append(application.id)
        self.audit.record("application.documents_added", actor.user_id, application.id, application.grant_call_id,
                          documents=result.documents_associated, duplicates=result.duplicates)
        return application, result

    def list_pending_uploads(self, call_id: str) -> list[PendingUpload]:
        self.get_call(call_id)
        return self.repo.list(PendingUpload, grant_call_id=call_id)

    def associate_upload(self, actor: Actor, upload_id: str, *, application_id: str | None = None,
                         new_reference: str | None = None) -> Application:
        self._require(actor, ADMIN_ROLES, "associate uploads")
        pending = self._get(PendingUpload, upload_id, "Pending upload")
        self._open_call(pending.grant_call_id)
        with self.repo.lock:
            if application_id:
                application = self._get(Application, application_id, "Application")
                if application.grant_call_id != pending.grant_call_id:
                    raise ValidationFailedError("Application belongs to another call")
            else:
                reference = (new_reference or "").strip() or self._next_reference(pending.grant_call_id)
                if any(a.application_reference == reference for a in self.repo.list(Application, grant_call_id=pending.grant_call_id)):
                    raise ConflictError(f"Application reference {reference} already exists")
                application = Application(grant_call_id=pending.grant_call_id, application_reference=reference)
                self.repo.save(application)
            content = self.repo.get_content(pending.id)
            doc_id = new_id("doc")
            if content is not None:
                content = dataclasses.replace(content, source_id=doc_id)
                self.repo.save_content(doc_id, content)
            existing = [d for d in self.repo.list(ApplicationDocument, application_id=application.id) if d.filename == pending.filename]
            self.repo.save(ApplicationDocument(
                id=doc_id, application_id=application.id, filename=pending.filename,
                document_type=classify_document(pending.filename, content if pending.extraction_status == "success" else None),
                file_hash=pending.file_hash, version=len(existing) + 1, uploaded_by=actor.user_id,
                extraction_status=pending.extraction_status, page_count=content.page_count if content else None,
                error=content.error if content else None, provenance={"associated_from": pending.id},
            ))
            self.repo.delete(PendingUpload, pending.id)
            application = self._apply_metadata(application)
        self.audit.record("upload.associated", actor.user_id, application.id, application.grant_call_id,
                          upload_id=pending.id, filename=pending.filename)
        return application

    def get_application(self, application_id: str) -> Application:
        return self._get(Application, application_id, "Application")

    def application_documents(self, application_id: str) -> list[ApplicationDocument]:
        self.get_application(application_id)
        return sorted(self.repo.list(ApplicationDocument, application_id=application_id), key=lambda d: d.uploaded_at)

    def document_content(self, document_id: str) -> DocumentContent:
        meta = self.repo.get(ApplicationDocument, document_id)
        if meta is not None:
            owner_type, owner_id, filename, status = "application", meta.application_id, meta.filename, meta.extraction_status
        else:
            rfp = self._get(RfpDocument, document_id, "Document")
            owner_type, owner_id, filename, status = "grant_call", rfp.grant_call_id, rfp.filename, rfp.extraction_status
        content = self.repo.get_content(document_id)
        pages = [DocumentPage(page_number=p.page_number, text=p.text, lines=list(p.lines)) for p in content.pages] if content else []
        return DocumentContent(document_id=document_id, filename=filename, owner_type=owner_type, owner_id=owner_id,
                               extraction_status=status, pages=pages)

    # -- screening --------------------------------------------------------------
    def start_screening(self, actor: Actor, call_id: str, application_ids: list[str] | None = None) -> ScreeningBatch:
        self._require(actor, ADMIN_ROLES, "launch screening")
        call = self.get_call(call_id)
        if call.status not in OPEN_FOR_SUBMISSIONS:
            raise ConflictError(f"Call is {call.status.value}; requirements must be confirmed before screening")
        if not active_criteria(self.repo, call_id):
            raise ConflictError("No verified requirements to screen against")
        with self.repo.lock:
            applications = self.repo.list(Application, grant_call_id=call_id)
            if application_ids is not None:
                wanted = set(application_ids)
                unknown = wanted - {a.id for a in applications}
                if unknown:
                    raise NotFoundError(f"Applications not in this call: {', '.join(sorted(unknown))}")
                applications = [a for a in applications if a.id in wanted]
            active_runs = {r.application_id for r in self.repo.list(ScreeningRun, grant_call_id=call_id) if r.status in ACTIVE_RUN_STATES}
            applications = [a for a in applications if a.id not in active_runs]
            if not applications:
                raise ConflictError("No applications to screen (none uploaded, or all are already being screened)")
            batch = ScreeningBatch(grant_call_id=call_id, run_ids=[], created_by=actor.user_id)
            runs = []
            for application in sorted(applications, key=lambda a: a.application_reference):
                run = ScreeningRun(grant_call_id=call_id, application_id=application.id, batch_id=batch.id,
                                   pipeline_version=PIPELINE_VERSION, created_by=actor.user_id)
                self.repo.save(run)
                self.repo.save(application.model_copy(update={"screening_status": ScreeningStatus.QUEUED, "latest_run_id": run.id, "updated_at": utcnow()}))
                runs.append(run)
            batch.run_ids = [r.id for r in runs]
            self.repo.save(batch)
            self._set_call_status(self.get_call(call_id), GrantCallStatus.SCREENING, actor.user_id)
        self.audit.record("screening.batch_started", actor.user_id, batch.id, call_id, applications=len(runs))
        for run in runs:
            self.jobs.submit(lambda run_id=run.id: self.orchestrator.run(run_id))
        return batch

    def get_run(self, run_id: str) -> ScreeningRun:
        return self._get(ScreeningRun, run_id, "Screening run")

    def batch_progress(self, batch_id: str) -> BatchProgress:
        batch = self._get(ScreeningBatch, batch_id, "Screening batch")
        runs = [r for r in (self.repo.get(ScreeningRun, run_id) for run_id in batch.run_ids) if r is not None]
        return self._progress(batch.id, batch.grant_call_id, runs)

    @staticmethod
    def _progress(batch_id: str, call_id: str, runs: list[ScreeningRun]) -> BatchProgress:
        total = len(runs)
        stages = []
        for stage in StageName:
            states = [next(s for s in r.stages if s.stage == stage) for r in runs]
            completed = sum(1 for s in states if s.status in {StageStatus.COMPLETE, StageStatus.SKIPPED})
            failed = sum(1 for s in states if s.status == StageStatus.FAILED)
            stages.append(StageProgress(stage=stage, completed=completed, failed=failed, total=total,
                                        percent_processed=round(100 * (completed + failed) / total, 1) if total else 0.0))
        finished = sum(1 for r in runs if r.status in FINISHED_RUN_STATES)
        if not runs:
            status = RunState.QUEUED
        elif finished < total:
            status = RunState.RUNNING if any(r.status != RunState.QUEUED for r in runs) else RunState.QUEUED
        elif all(r.status == RunState.COMPLETE for r in runs):
            status = RunState.COMPLETE
        elif all(r.status == RunState.BLOCKED for r in runs):
            status = RunState.BLOCKED
        else:
            status = RunState.PARTIAL
        return BatchProgress(batch_id=batch_id, grant_call_id=call_id, status=status, total=total, finished=finished,
                             stages=stages, runs=runs)

    def latest_batch(self, call_id: str) -> BatchProgress | None:
        batches = sorted(self.repo.list(ScreeningBatch, grant_call_id=call_id), key=lambda b: b.created_at)
        return self.batch_progress(batches[-1].id) if batches else None

    # -- findings & review --------------------------------------------------------
    def list_findings(self, application_id: str, *, run_id: str | None = None) -> list[Finding]:
        application = self.get_application(application_id)
        run_id = run_id or application.latest_run_id
        if not run_id:
            return []
        order = {"eligibility": 0, "completeness": 1, "duplication": 2, "plagiarism": 3, "novelty": 4}
        findings = self.repo.list(Finding, application_id=application_id, screening_run_id=run_id)
        return sorted(findings, key=lambda f: (order.get(f.type.value, 9), f.title))

    def get_finding(self, finding_id: str) -> Finding:
        return self._get(Finding, finding_id, "Finding")

    def finding_evidence(self, finding_id: str) -> list[FindingEvidence]:
        return self.get_finding(finding_id).evidence

    def decide(self, actor: Actor, finding_id: str, action: ReviewerAction, note: str) -> ReviewerDecision:
        self._require(actor, REVIEW_ROLES, "record reviewer decisions")
        finding = self.get_finding(finding_id)
        note = (note or "").strip()
        if not note:
            raise ValidationFailedError("A rationale note is required for every reviewer decision")
        if action == ReviewerAction.CONFIRM:
            self.decisions.record_decision(finding_id, actor.user_id, ReviewStatus.UPHELD, note)
        elif action == ReviewerAction.DISMISS:
            self.decisions.record_decision(finding_id, actor.user_id, ReviewStatus.DISMISSED, note)
        elif action == ReviewerAction.ESCALATE:
            self.decisions.escalate(finding_id, actor.user_id, note)
        else:
            self.decisions.request_clarification(finding_id, actor.user_id, note, "review_panel")
        new_state = _DECISION_STATES[action]
        decision = ReviewerDecision(
            finding_id=finding_id, application_id=finding.application_id, grant_call_id=finding.grant_call_id,
            action=action, reviewer_id=actor.user_id, reviewer_role=actor.role, note=note,
            previous_state=finding.review_state, new_state=new_state,
        )
        with self.repo.lock:
            self.repo.save(decision)
            self.repo.save(finding.model_copy(update={"review_state": new_state}))
            self._refresh_review_status(finding.application_id)
        self.audit.record("finding.decision", actor.user_id, finding_id, finding.grant_call_id,
                          application_id=finding.application_id, action=action.value,
                          previous_state=finding.review_state.value, new_state=new_state.value, note=note)
        return decision

    def _refresh_review_status(self, application_id: str) -> None:
        application = self.get_application(application_id)
        findings = self.list_findings(application_id)
        done = findings and all(f.review_state in {ReviewState.CONFIRMED, ReviewState.DISMISSED} for f in findings)
        status = ApplicationStatus.REVIEW_COMPLETE if done else ApplicationStatus.IN_REVIEW
        if application.status != status:
            self.repo.save(application.model_copy(update={"status": status, "updated_at": utcnow()}))

    def add_note(self, actor: Actor, finding_id: str, note: str) -> ReviewerNote:
        self._require(actor, REVIEW_ROLES, "add reviewer notes")
        finding = self.get_finding(finding_id)
        if not (note or "").strip():
            raise ValidationFailedError("Note cannot be empty")
        item = ReviewerNote(finding_id=finding_id, application_id=finding.application_id,
                            grant_call_id=finding.grant_call_id, author_id=actor.user_id, note=note.strip())
        self.repo.save(item)
        self.audit.record("finding.note_added", actor.user_id, finding_id, finding.grant_call_id,
                          application_id=finding.application_id)
        return item

    def finding_history(self, finding_id: str) -> tuple[list[ReviewerDecision], list[ReviewerNote]]:
        self.get_finding(finding_id)
        decisions = sorted(self.repo.list(ReviewerDecision, finding_id=finding_id), key=lambda d: d.created_at)
        notes = sorted(self.repo.list(ReviewerNote, finding_id=finding_id), key=lambda n: n.created_at)
        return decisions, notes

    # -- audit & sources ----------------------------------------------------------
    def audit_log(self, actor: Actor, call_id: str) -> list[AuditLogEntry]:
        self._require(actor, AUDIT_ROLES, "inspect the audit trail")
        self.get_call(call_id)
        return list(reversed(self.audit.entries(grant_call_id=call_id)))

    def sources(self) -> list[DataSource]:
        return [
            DataSource(
                source_id=s.source_id, provider=s.provider, source_name=s.source_name, source_type=s.source_type,
                access_status=s.access_status.value,
                required_for_core_workflow=s.source_id in {"same_call_applications"},
                coverage=s.coverage, methodology=s.methodology,
            )
            for s in self.registry.list()
        ]
