"""Service wiring and authenticated actor dependencies."""
import os
from typing import Annotated

from fastapi import Depends, HTTPException, Request

from ml.semantic_matching.embedding import get_runtime_embedder
from ml.semantic_matching.reranker import get_runtime_reranker
from services.auth.demo_auth import DemoAuthentication, DemoPrincipal, DemoWorkspace
from services.grant_workflow.duplication_archive import DuplicationArchive
from services.grant_workflow.jobs import ThreadPoolJobRunner
from services.grant_workflow.models import Role
from services.grant_workflow.service import Actor, GrantWorkflowService
from services.grant_workflow.views import WorkflowViews


def build_service() -> GrantWorkflowService:
    return GrantWorkflowService(
        jobs=ThreadPoolJobRunner(max_workers=int(os.getenv("AI_SCREENING_SCREENING_WORKERS", "2"))),
        embedder_factory=get_runtime_embedder,
        reranker_factory=get_runtime_reranker,
        duplication_archive=DuplicationArchive(),
    )


def get_service(request: Request) -> GrantWorkflowService:
    service = getattr(request.app.state, "workflow", None)
    if service is None:
        service = build_service()
        request.app.state.workflow = service
    return service


def get_views(service: Annotated[GrantWorkflowService, Depends(get_service)]) -> WorkflowViews:
    return WorkflowViews(service)


def get_demo_auth(request: Request) -> DemoAuthentication:
    return request.app.state.demo_auth


def request_bearer_token(request: Request) -> str | None:
    authorization = request.headers.get("authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def optional_actor(request: Request) -> Actor | None:
    principal: DemoPrincipal | None = getattr(request.state, "demo_principal", None)
    if principal is None or principal.workspace != DemoWorkspace.GRANT_ADMINISTRATOR:
        return None
    return Actor(user_id=principal.user_id, role=Role.GRANT_ADMINISTRATOR)


def current_actor(request: Request) -> Actor:
    actor = optional_actor(request)
    if actor is None:
        raise HTTPException(status_code=403, detail="Grant Administrator access is required")
    return actor
