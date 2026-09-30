"""Grant-call screening workflow routes. Handlers only translate HTTP to service calls."""
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import Response

from apps.api.dependencies import current_actor, get_service, get_views, optional_actor
from apps.api.schemas.workflow import (
    ApplicationDetail,
    AssociateRequest,
    DecisionRequest,
    FindingDetail,
    GrantCallCreate,
    GrantCallUpdate,
    NoteRequest,
    RequirementActive,
    RequirementCreate,
    RequirementUpdate,
    RequirementVerify,
    RfpUploadResponse,
    ScreenRequest,
    SessionInfo,
    UploadResponse,
)
from services.grant_workflow.demo_data import DEMO_RFP_FILENAME
from services.grant_workflow.documents import UploadedFile
from services.grant_workflow.models import (
    Applicant,
    AuditLogEntry,
    BatchProgress,
    DataSource,
    DocumentContent,
    Finding,
    FindingEvidence,
    GrantCall,
    Institution,
    PendingUpload,
    ReviewerDecision,
    ReviewerNote,
    RfpCriterion,
    RfpDocument,
    Role,
    ScreeningBatch,
    ScreeningRun,
)
from services.grant_workflow.seed import demo_applications_zip, demo_rfp_bytes
from services.grant_workflow.service import Actor, BatchUploadResult, GrantWorkflowService
from services.grant_workflow.views import (
    ApplicationRow,
    DashboardSummary,
    ScreeningReport,
    WorkflowViews,
)

router = APIRouter(prefix="/api/v1", tags=["grant-workflow"])

ServiceDep = Annotated[GrantWorkflowService, Depends(get_service)]
ViewsDep = Annotated[WorkflowViews, Depends(get_views)]
ActorDep = Annotated[Actor, Depends(current_actor)]
OptionalActorDep = Annotated[Actor | None, Depends(optional_actor)]
UploadFiles = Annotated[list[UploadFile], File()]


async def _read(files: list[UploadFile]) -> list[UploadedFile]:
    return [UploadedFile(f.filename or "upload", await f.read()) for f in files]


def _upload_response(result: BatchUploadResult) -> UploadResponse:
    return UploadResponse(**result.__dict__)


@router.get("/session", response_model=SessionInfo)
def session(actor: OptionalActorDep) -> SessionInfo:
    return SessionInfo(
        user_id=actor.user_id if actor else "anonymous",
        role=actor.role if actor else None,
        roles=list(Role),
    )


# -- grant calls -------------------------------------------------------------
@router.post("/grants", response_model=GrantCall, status_code=201)
def create_grant(body: GrantCallCreate, actor: ActorDep, service: ServiceDep) -> GrantCall:
    return service.create_call(actor, body.model_dump())


@router.get("/grants", response_model=list[GrantCall])
def list_grants(service: ServiceDep) -> list[GrantCall]:
    return service.list_calls()


@router.get("/grants/{call_id}", response_model=GrantCall)
def get_grant(call_id: str, service: ServiceDep) -> GrantCall:
    return service.get_call(call_id)


@router.patch("/grants/{call_id}", response_model=GrantCall)
def update_grant(
    call_id: str, body: GrantCallUpdate, actor: ActorDep, service: ServiceDep
) -> GrantCall:
    return service.update_call(actor, call_id, body.model_dump(exclude_unset=True))


# -- RFP & requirements --------------------------------------------------------
@router.post("/grants/{call_id}/rfp", response_model=RfpUploadResponse, status_code=201)
async def upload_rfp(
    call_id: str,
    file: Annotated[UploadFile, File()],
    actor: ActorDep,
    service: ServiceDep,
) -> RfpUploadResponse:
    data = await file.read()
    rfp, criteria = service.upload_rfp(actor, call_id, file.filename or "call_document", data)
    return RfpUploadResponse(
        rfp_document=rfp, requirements=criteria, grant_call=service.get_call(call_id)
    )


@router.get("/grants/{call_id}/rfp", response_model=list[RfpDocument])
def list_rfps(call_id: str, service: ServiceDep) -> list[RfpDocument]:
    return service.list_rfps(call_id)


@router.get("/grants/{call_id}/requirements", response_model=list[RfpCriterion])
def list_requirements(
    call_id: str, service: ServiceDep, include_inactive: bool = True
) -> list[RfpCriterion]:
    return service.list_requirements(call_id, include_inactive=include_inactive)


@router.post("/grants/{call_id}/requirements", response_model=RfpCriterion, status_code=201)
def add_requirement(
    call_id: str, body: RequirementCreate, actor: ActorDep, service: ServiceDep
) -> RfpCriterion:
    return service.add_requirement(actor, call_id, body.model_dump())


@router.post("/grants/{call_id}/requirements/confirm", response_model=GrantCall)
def confirm_requirements(call_id: str, actor: ActorDep, service: ServiceDep) -> GrantCall:
    return service.confirm_requirements(actor, call_id)


@router.patch("/requirements/{criterion_id}", response_model=RfpCriterion)
def update_requirement(
    criterion_id: str, body: RequirementUpdate, actor: ActorDep, service: ServiceDep
) -> RfpCriterion:
    return service.update_requirement(actor, criterion_id, body.model_dump(exclude_unset=True))


@router.post("/requirements/{criterion_id}/verify", response_model=RfpCriterion)
def verify_requirement(
    criterion_id: str, body: RequirementVerify, actor: ActorDep, service: ServiceDep
) -> RfpCriterion:
    return service.verify_requirement(actor, criterion_id, decision=body.decision, note=body.note)


@router.post("/requirements/{criterion_id}/active", response_model=RfpCriterion)
def set_requirement_active(
    criterion_id: str, body: RequirementActive, actor: ActorDep, service: ServiceDep
) -> RfpCriterion:
    return service.set_requirement_active(actor, criterion_id, body.active)


# -- applications ----------------------------------------------------------------
@router.post("/grants/{call_id}/applications", response_model=UploadResponse, status_code=201)
async def create_application(
    call_id: str,
    files: UploadFiles,
    actor: ActorDep,
    service: ServiceDep,
    reference: Annotated[str | None, Form()] = None,
) -> UploadResponse:
    _, result = service.create_application(actor, call_id, await _read(files), reference=reference)
    return _upload_response(result)


@router.post(
    "/grants/{call_id}/applications/batch", response_model=UploadResponse, status_code=201
)
async def batch_applications(
    call_id: str, files: UploadFiles, actor: ActorDep, service: ServiceDep
) -> UploadResponse:
    return _upload_response(service.upload_applications(actor, call_id, await _read(files)))


@router.get("/grants/{call_id}/applications", response_model=list[ApplicationRow])
def list_applications(
    call_id: str,
    views: ViewsDep,
    q: str | None = None,
    screening_status: str | None = None,
    eligibility: str | None = None,
    completeness: str | None = None,
    novelty: str | None = None,
    review_progress: str | None = None,
    processing_status: str | None = None,
    flagged: Annotated[str | None, Query(pattern="^(true|false)$")] = None,
) -> list[ApplicationRow]:
    return views.application_rows(call_id, {
        "q": q,
        "screening_status": screening_status,
        "eligibility": eligibility,
        "completeness": completeness,
        "novelty": novelty,
        "review_progress": review_progress,
        "processing_status": processing_status,
        "flagged": flagged,
    })


@router.get("/grants/{call_id}/pending-uploads", response_model=list[PendingUpload])
def pending_uploads(call_id: str, service: ServiceDep) -> list[PendingUpload]:
    return service.list_pending_uploads(call_id)


@router.post("/pending-uploads/{upload_id}/associate", response_model=ApplicationRow)
def associate_upload(
    upload_id: str, body: AssociateRequest, actor: ActorDep, service: ServiceDep, views: ViewsDep
) -> ApplicationRow:
    application = service.associate_upload(
        actor, upload_id, application_id=body.application_id, new_reference=body.new_reference
    )
    return views.row(application)


@router.get("/applications/{application_id}", response_model=ApplicationDetail)
def get_application(
    application_id: str, service: ServiceDep, views: ViewsDep
) -> ApplicationDetail:
    application = service.get_application(application_id)
    repo = service.repo
    return ApplicationDetail(
        application=application,
        row=views.row(application),
        applicant=repo.get(Applicant, application.applicant_id) if application.applicant_id else None,
        institution=(
            repo.get(Institution, application.institution_id) if application.institution_id else None
        ),
        documents=service.application_documents(application_id),
        latest_run=service.get_run(application.latest_run_id) if application.latest_run_id else None,
    )


@router.post(
    "/applications/{application_id}/documents", response_model=UploadResponse, status_code=201
)
async def add_documents(
    application_id: str, files: UploadFiles, actor: ActorDep, service: ServiceDep
) -> UploadResponse:
    _, result = service.add_documents(actor, application_id, await _read(files))
    return _upload_response(result)


@router.get("/documents/{document_id}/content", response_model=DocumentContent)
def document_content(document_id: str, service: ServiceDep) -> DocumentContent:
    return service.document_content(document_id)


# -- screening -------------------------------------------------------------------
@router.post("/grants/{call_id}/screen", response_model=ScreeningBatch, status_code=202)
def screen_call(
    call_id: str, actor: ActorDep, service: ServiceDep, body: ScreenRequest | None = None
) -> ScreeningBatch:
    return service.start_screening(actor, call_id, body.application_ids if body else None)


@router.post(
    "/applications/{application_id}/screen", response_model=ScreeningBatch, status_code=202
)
def screen_application(application_id: str, actor: ActorDep, service: ServiceDep) -> ScreeningBatch:
    application = service.get_application(application_id)
    return service.start_screening(actor, application.grant_call_id, [application_id])


@router.get("/screening-runs/{run_id}", response_model=ScreeningRun)
def get_run(run_id: str, service: ServiceDep) -> ScreeningRun:
    return service.get_run(run_id)


@router.get("/screening-batches/{batch_id}", response_model=BatchProgress)
def get_batch(batch_id: str, service: ServiceDep) -> BatchProgress:
    return service.batch_progress(batch_id)


# -- findings & review -------------------------------------------------------------
@router.get("/applications/{application_id}/findings", response_model=list[Finding])
def list_findings(
    application_id: str, service: ServiceDep, run_id: str | None = None
) -> list[Finding]:
    return service.list_findings(application_id, run_id=run_id)


@router.get("/findings/{finding_id}", response_model=FindingDetail)
def get_finding(finding_id: str, service: ServiceDep) -> FindingDetail:
    decisions, notes = service.finding_history(finding_id)
    return FindingDetail(finding=service.get_finding(finding_id), decisions=decisions, notes=notes)


@router.get("/findings/{finding_id}/evidence", response_model=list[FindingEvidence])
def finding_evidence(finding_id: str, service: ServiceDep) -> list[FindingEvidence]:
    return service.finding_evidence(finding_id)


@router.post("/findings/{finding_id}/decision", response_model=ReviewerDecision, status_code=201)
def decide(
    finding_id: str, body: DecisionRequest, actor: ActorDep, service: ServiceDep
) -> ReviewerDecision:
    return service.decide(actor, finding_id, body.action, body.note)


@router.post("/findings/{finding_id}/notes", response_model=ReviewerNote, status_code=201)
def add_note(finding_id: str, body: NoteRequest, actor: ActorDep, service: ServiceDep) -> ReviewerNote:
    return service.add_note(actor, finding_id, body.note)


# -- dashboard, audit, report, sources ----------------------------------------------
@router.get("/grants/{call_id}/dashboard", response_model=DashboardSummary)
def dashboard(call_id: str, views: ViewsDep) -> DashboardSummary:
    return views.dashboard(call_id)


@router.get("/grants/{call_id}/audit", response_model=list[AuditLogEntry])
def audit(call_id: str, actor: ActorDep, service: ServiceDep) -> list[AuditLogEntry]:
    return service.audit_log(actor, call_id)


@router.get("/grants/{call_id}/report", response_model=ScreeningReport)
def report(call_id: str, views: ViewsDep) -> ScreeningReport:
    return views.report(call_id)


@router.get("/sources", response_model=list[DataSource])
def sources(service: ServiceDep) -> list[DataSource]:
    return service.sources()


# -- synthetic demo files -----------------------------------------------------------
@router.get("/demo/rfp", response_class=Response)
def demo_rfp() -> Response:
    return Response(
        demo_rfp_bytes(),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{DEMO_RFP_FILENAME}"'},
    )


@router.get("/demo/applications.zip", response_class=Response)
def demo_applications() -> Response:
    return Response(
        demo_applications_zip(),
        media_type="application/zip",
        headers={
            "Content-Disposition": 'attachment; filename="DEMO-CRG-2026_synthetic_applications.zip"'
        },
    )
