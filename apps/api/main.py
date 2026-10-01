import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from apps.api.dependencies import get_service
from apps.api.routes import duplication, grants, health, ncst, publications, workflow
from services.config.env import load_env_file
from services.grant_workflow.seed import seed_demo
from services.grant_workflow.service import WorkflowError
from services.grant_workflow.sgci_call import seed_sgci_call

logger = logging.getLogger(__name__)

# Read .env before anything reads os.getenv (API keys, source configuration).
load_env_file()


def _flag(name: str, default: str = "true") -> bool:
    return os.getenv(name, default).strip().lower() not in {"0", "false", "no", "off"}


def _demo_seed_enabled() -> bool:
    return _flag("AI_SCREENING_DEMO_SEED")


def _demo_applications_enabled() -> bool:
    """Seed the five synthetic submissions, or leave the demo call empty for real uploads."""
    return _flag("AI_SCREENING_DEMO_APPLICATIONS")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if getattr(app.state, "workflow", None) is None:
        service = get_service(Request({"type": "http", "app": app}))
        if _demo_seed_enabled():
            try:
                seed_demo(service, applications=_demo_applications_enabled())
            except Exception:
                logger.exception("Synthetic demo seed failed")
        try:
            seed_sgci_call(service)
        except Exception:
            logger.exception("SGCI call seed failed")
    yield


app = FastAPI(title="shakaHive Research Intelligence API", version="0.1.0", lifespan=lifespan)

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
app.include_router(duplication.router)


@app.get("/api/v1")
def api_info() -> dict[str, str]:
    return {"name": "shakaHive", "version": "0.1.0", "purpose": "Research intelligence"}
