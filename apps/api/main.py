from fastapi import FastAPI

from apps.api.routes import grants, health, publications

app = FastAPI(
    title="AI-SCREENING Research Intelligence API",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(grants.router)
app.include_router(publications.router)

@app.get("/api/v1")
def api_info() -> dict[str, str]:
    return {
        "name": "AI-SCREENING",
        "version": "0.1.0",
        "purpose": "Research intelligence",
    }
