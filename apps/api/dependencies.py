"""Service wiring and the (demo) authorization boundary.

Roles arrive in the X-User-Role / X-User-Id headers. This is NOT authentication; it only
structures the boundary so an identity provider can populate `Actor` later.
"""
import os
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request

from ml.semantic_matching.embedding import get_runtime_embedder
from ml.semantic_matching.reranker import get_runtime_reranker
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


RoleHeader = Annotated[str | None, Header()]
UserHeader = Annotated[str | None, Header()]


def optional_actor(x_user_role: RoleHeader = None, x_user_id: UserHeader = None) -> Actor | None:
    if not x_user_role:
        return None
    try:
        role = Role(x_user_role.strip().upper())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Unknown role {x_user_role!r}") from exc
    return Actor(user_id=(x_user_id or f"demo-{role.value.lower()}").strip(), role=role)


def current_actor(x_user_role: RoleHeader = None, x_user_id: UserHeader = None) -> Actor:
    actor = optional_actor(x_user_role, x_user_id)
    if actor is None:
        raise HTTPException(status_code=401, detail="X-User-Role header is required for this action")
    return actor
