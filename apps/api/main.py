import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.routes import grants, health, publications

app = FastAPI(title="AI-SCREENING Research Intelligence API", version="0.1.0")

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "AI_SCREENING_CORS_ORIGINS",
        "http://localhost:3000,https://ai-screening.pages.dev",
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

app.include_router(health.router)
app.include_router(grants.router)
app.include_router(publications.router)


@app.get("/api/v1")
def api_info() -> dict[str, str]:
    return {"name": "AI-SCREENING", "version": "0.1.0", "purpose": "Research intelligence"}
