"""Upload real comparison records for the duplication check."""
import sqlite3
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from apps.api.dependencies import current_actor, get_service
from services.grant_workflow.duplication_archive import (
    MAX_IMPORT_BYTES,
    ArchivedProject,
    ArchiveValidationError,
    DuplicateProjectError,
    DuplicationArchive,
)
from services.grant_workflow.service import ADMIN_ROLES, Actor, GrantWorkflowService

router = APIRouter(prefix="/api/v1/duplication", tags=["duplication"])
ServiceDep = Annotated[GrantWorkflowService, Depends(get_service)]
ActorDep = Annotated[Actor, Depends(current_actor)]


def _archive(service: GrantWorkflowService) -> DuplicationArchive:
    archive = service.duplication_archive
    if archive is None:
        raise HTTPException(status_code=503, detail="The project comparison library is not configured")
    return archive


@router.get("/projects", response_model=list[ArchivedProject])
def list_projects(service: ServiceDep) -> list[ArchivedProject]:
    try:
        return _archive(service).list_projects()
    except (sqlite3.Error, OSError) as exc:
        raise HTTPException(status_code=503, detail="The project comparison library is unavailable") from exc


@router.post("/projects", response_model=ArchivedProject, status_code=201)
async def import_project(
    actor: ActorDep,
    service: ServiceDep,
    file: Annotated[UploadFile, File()],
    title: Annotated[str, Form(min_length=1, max_length=500)],
    source_type: Annotated[Literal["historical_application", "funded_project"], Form()],
    reference: Annotated[str | None, Form(max_length=200)] = None,
    year: Annotated[int | None, Form(ge=1000, le=9999)] = None,
    organization: Annotated[str | None, Form(max_length=500)] = None,
) -> ArchivedProject:
    service._require(actor, ADMIN_ROLES, "import projects into the duplication comparison library")
    archive = _archive(service)
    data = await file.read(MAX_IMPORT_BYTES + 1)
    if len(data) > MAX_IMPORT_BYTES:
        raise HTTPException(status_code=413, detail="Project document exceeds the 20 MB upload limit")
    try:
        project = archive.import_document(
            filename=file.filename or "upload", data=data, title=title, source_type=source_type,
            reference=reference, year=year, organization=organization, uploaded_by=actor.user_id,
        )
    except DuplicateProjectError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ArchiveValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (sqlite3.Error, OSError) as exc:
        raise HTTPException(status_code=503, detail="The project comparison library is unavailable") from exc
    service.audit.record(
        "duplication.project_imported", actor.user_id, project.id, None,
        title=project.title, source_type=project.source_type, filename=project.filename,
    )
    return project
