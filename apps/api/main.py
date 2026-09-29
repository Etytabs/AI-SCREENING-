from fastapi import FastAPI

app = FastAPI(title="AI-SCREENING Research Intelligence API", version="0.1.0")

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-screening-api"}

@app.get("/api/v1")
def api_info() -> dict[str, str]:
    return {"name": "AI-SCREENING", "version": "0.1.0", "purpose": "Research intelligence"}
