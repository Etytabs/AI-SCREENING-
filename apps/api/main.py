import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from apps.api.dependencies import get_service
from apps.api.routes import auth, duplication, grants, health, ncst, publications, workflow
from services.auth.demo_auth import DemoAuthentication, DemoWorkspace
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
            except Exception as exc:
                logger.error("Synthetic demo seed failed (%s)", type(exc).__name__)
        try:
            seed_sgci_call(service)
        except Exception as exc:
            logger.error("SGCI call seed failed (%s)", type(exc).__name__)
    yield


app = FastAPI(title="shakaHive Research Intelligence API", version="0.1.0", lifespan=lifespan)
app.state.demo_auth = DemoAuthentication.from_environment()


@app.middleware("http")
async def demo_auth_boundary(request: Request, call_next):
    path = request.url.path
    is_api_v1 = path == "/api/v1" or path.startswith("/api/v1/")
    if request.method == "OPTIONS" or not is_api_v1:
        return await call_next(request)
    if path in {"/api/v1", "/api/v1/auth/login"}:
        response = await call_next(request)
        if path == "/api/v1/auth/login":
            response.headers["Cache-Control"] = "no-store"
        return response

    authentication = request.app.state.demo_auth
    if not authentication.enabled:
        return JSONResponse(
            status_code=503,
            content={"detail": "Demo authentication is not enabled"},
            headers={"Cache-Control": "no-store"},
        )

    token = request.headers.get("authorization", "")
    scheme, _, value = token.partition(" ")
    principal = authentication.resolve(value.strip() if scheme.lower() == "bearer" else None)
    if principal is None:
        return JSONResponse(
            status_code=401,
            content={"detail": "Authentication required"},
            headers={"Cache-Control": "no-store"},
        )

    request.state.demo_principal = principal
    auth_paths = {"/api/v1/auth/me", "/api/v1/auth/logout"}
    if path not in auth_paths and principal.workspace != DemoWorkspace.GRANT_ADMINISTRATOR:
        return JSONResponse(
            status_code=403,
            content={"detail": "Grant Administrator access is required"},
            headers={"Cache-Control": "no-store"},
        )

    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response

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
    allow_origin_regex=r"https://[a-z0-9-]+\.ai-screening\.pages\.dev",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(WorkflowError)
async def workflow_error(_: Request, exc: WorkflowError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})


@app.exception_handler(RequestValidationError)
async def request_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [
        {
            "loc": [part for part in error["loc"] if isinstance(part, (str, int))],
            "msg": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": errors})


@app.middleware("http")
async def redact_unhandled_error(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        logger.error("Unhandled API error %s at %s", type(exc).__name__, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(grants.router)
app.include_router(ncst.router)
app.include_router(publications.router)
app.include_router(workflow.router)
app.include_router(duplication.router)


@app.get("/api/v1")
def api_info() -> dict[str, str]:
    return {"name": "shakaHive", "version": "0.1.0", "purpose": "Research intelligence"}
