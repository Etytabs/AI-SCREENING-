import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from apps.api.dependencies import get_service
from apps.api.routes import grants, health, ncst, publications, workflow
from services.grant_workflow.seed import seed_demo
from services.grant_workflow.service import WorkflowError

logger = logging.getLogger(__name__)


def _demo_seed_enabled() -> bool:
    return os.getenv("AI_SCREENING_DEMO_SEED", "true").strip().lower() not in {"0", "false", "no", "off"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    if _demo_seed_enabled() and getattr(app.state, "workflow", None) is None:
        service = get_service(Request({"type": "http", "app": app}))
        try:
            seed_demo(service)
        except Exception:
            logger.exception("Synthetic demo seed failed")
    yield


app = FastAPI(title="AI-SCREENING Research Intelligence API", version="0.1.0", lifespan=lifespan)

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "AI_SCREENING_CORS_ORIGINS",
        "http://localhost:3000,http://localhost:3001,https://ai-screening.pages.dev",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://[a-z0-9-]+\\.ai-screening\\.pages\\.dev",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(WorkflowError)
async def workflow_error(_: Request, exc: WorkflowError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})


app.include_router(health.router)
app.include_router(grants.router)
app.include_router(ncst.router)
app.include_router(publications.router)
app.include_router(workflow.router)


@app.get("/api/v1")
def api_info() -> dict[str, str]:
    return {"name": "AI-SCREENING", "version": "0.1.0", "purpose": "Research intelligence"}
