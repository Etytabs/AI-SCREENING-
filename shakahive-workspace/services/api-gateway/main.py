from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import asyncio
import uuid
from typing import Optional
import os
from datetime import datetime
import json

# Import shared models
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from shared.models import (
    GrantApplication, ScreeningRequest, ScreeningReport,
    ApplicationStatus
)

app = FastAPI(
    title="NOVARAai API Gateway",
    description="AI-powered Research and Grant Screening Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
ELIGIBILITY_SERVICE_URL = os.getenv("ELIGIBILITY_SERVICE_URL", "http://localhost:8001")
PLAGIARISM_SERVICE_URL = os.getenv("PLAGIARISM_SERVICE_URL", "http://localhost:8002")
DUPLICATION_SERVICE_URL = os.getenv("DUPLICATION_SERVICE_URL", "http://localhost:8003")
NOVELTY_SERVICE_URL = os.getenv("NOVELTY_SERVICE_URL", "http://localhost:8004")
REPORT_SERVICE_URL = os.getenv("REPORT_SERVICE_URL", "http://localhost:8005")

# In-memory storage for applications (in production, use database)
applications_store = {}
screening_tasks = {}


class ScreeningStatus(BaseModel):
    """Status of screening process"""
    application_id: str
    status: str
    current_step: str
    progress: float
    estimated_completion: Optional[datetime] = None


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "NOVARAai API Gateway",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "eligibility": ELIGIBILITY_SERVICE_URL,
            "plagiarism": PLAGIARISM_SERVICE_URL,
            "duplication": DUPLICATION_SERVICE_URL,
            "novelty": NOVELTY_SERVICE_URL,
            "report": REPORT_SERVICE_URL
        }
    }


@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    services = {
        "eligibility": ELIGIBILITY_SERVICE_URL,
        "plagiarism": PLAGIARISM_SERVICE_URL,
        "duplication": DUPLICATION_SERVICE_URL,
        "novelty": NOVELTY_SERVICE_URL,
        "report": REPORT_SERVICE_URL
    }
    
    health_status = {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        for service_name, url in services.items():
            try:
                response = await client.get(f"{url}/health")
                health_status[service_name] = "healthy" if response.status_code == 200 else "unhealthy"
            except Exception:
                health_status[service_name] = "unreachable"
    
    return {
        "gateway": "healthy",
        "services": health_status,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/applications", response_model=dict)
async def submit_application(application: GrantApplication):
    """Submit a new grant application"""
    application_id = str(uuid.uuid4())
    application.id = application_id
    application.status = ApplicationStatus.PENDING
    
    applications_store[application_id] = application.dict()
    
    return {
        "application_id": application_id,
        "status": "submitted",
        "message": "Application submitted successfully. Use /screen/{application_id} to start screening."
    }


@app.post("/applications/upload")
async def upload_application(
    file: UploadFile = File(...),
    title: str = None,
    author_name: str = None,
    institution: str = None
):
    """Upload application file (PDF, DOCX, etc.)"""
    application_id = str(uuid.uuid4())
    
    # Save file (in production, use cloud storage)
    file_path = f"uploads/{application_id}_{file.filename}"
    os.makedirs("uploads", exist_ok=True)
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    return {
        "application_id": application_id,
        "file_path": file_path,
        "status": "uploaded",
        "message": "File uploaded successfully. Parse and submit application data."
    }


@app.post("/screen/{application_id}")
async def start_screening(
    application_id: str,
    request: ScreeningRequest,
    background_tasks: BackgroundTasks
):
    """Start the screening process for an application"""
    if application_id not in applications_store:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Update application status
    applications_store[application_id]["status"] = ApplicationStatus.PROCESSING
    screening_tasks[application_id] = {
        "status": "processing",
        "current_step": "initializing",
        "progress": 0.0,
        "started_at": datetime.utcnow()
    }
    
    # Start background screening process
    background_tasks.add_task(
        run_screening_process,
        application_id,
        request
    )
    
    return {
        "application_id": application_id,
        "status": "screening_started",
        "message": "Screening process initiated. Check status at /status/{application_id}"
    }


async def run_screening_process(application_id: str, request: ScreeningRequest):
    """Run the complete screening process"""
    try:
        application = applications_store[application_id]
        screening_tasks[application_id]["current_step"] = "eligibility"
        screening_tasks[application_id]["progress"] = 10.0
        
        # Step 1: Eligibility Check
        eligibility_result = None
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{ELIGIBILITY_SERVICE_URL}/check",
                json={
                    "application": application,
                    "criteria": request.eligibility_criteria.dict() if request.eligibility_criteria else None
                }
            )
            eligibility_result = response.json()
        
        screening_tasks[application_id]["current_step"] = "plagiarism"
        screening_tasks[application_id]["progress"] = 30.0
        
        # Step 2: Plagiarism Detection
        plagiarism_result = None
        if not request.skip_plagiarism:
            async with httpx.AsyncClient(timeout=600.0) as client:
                response = await client.post(
                    f"{PLAGIARISM_SERVICE_URL}/detect",
                    json={"application": application}
                )
                plagiarism_result = response.json()
        
        screening_tasks[application_id]["current_step"] = "duplication"
        screening_tasks[application_id]["progress"] = 50.0
        
        # Step 3: Duplication Check
        duplication_result = None
        if not request.skip_duplication:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{DUPLICATION_SERVICE_URL}/check",
                    json={"application": application}
                )
                duplication_result = response.json()
        
        screening_tasks[application_id]["current_step"] = "novelty"
        screening_tasks[application_id]["progress"] = 70.0
        
        # Step 4: Novelty Assessment
        novelty_result = None
        if not request.skip_novelty:
            async with httpx.AsyncClient(timeout=600.0) as client:
                response = await client.post(
                    f"{NOVELTY_SERVICE_URL}/assess",
                    json={"application": application}
                )
                novelty_result = response.json()
        
        screening_tasks[application_id]["current_step"] = "report_generation"
        screening_tasks[application_id]["progress"] = 90.0
        
        # Step 5: Generate Report
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{REPORT_SERVICE_URL}/generate",
                json={
                    "application_id": application_id,
                    "eligibility": eligibility_result,
                    "plagiarism": plagiarism_result,
                    "duplication": duplication_result,
                    "novelty": novelty_result
                }
            )
            report = response.json()
        
        # Update final status
        screening_tasks[application_id]["status"] = "completed"
        screening_tasks[application_id]["progress"] = 100.0
        screening_tasks[application_id]["current_step"] = "completed"
        screening_tasks[application_id]["report"] = report
        
        applications_store[application_id]["status"] = ApplicationStatus.COMPLETED
        
    except Exception as e:
        screening_tasks[application_id]["status"] = "failed"
        screening_tasks[application_id]["error"] = str(e)
        applications_store[application_id]["status"] = ApplicationStatus.FAILED


@app.get("/status/{application_id}", response_model=ScreeningStatus)
async def get_screening_status(application_id: str):
    """Get the status of screening process"""
    if application_id not in screening_tasks:
        raise HTTPException(status_code=404, detail="Screening task not found")
    
    task = screening_tasks[application_id]
    
    return ScreeningStatus(
        application_id=application_id,
        status=task["status"],
        current_step=task["current_step"],
        progress=task["progress"],
        estimated_completion=None
    )


@app.get("/report/{application_id}")
async def get_screening_report(application_id: str):
    """Get the complete screening report"""
    if application_id not in screening_tasks:
        raise HTTPException(status_code=404, detail="Screening task not found")
    
    task = screening_tasks[application_id]
    
    if task["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Screening not completed. Current status: {task['status']}"
        )
    
    return task.get("report")


@app.get("/applications")
async def list_applications():
    """List all applications"""
    return {
        "applications": [
            {
                "id": app_id,
                "title": app["title"],
                "author": app["author_name"],
                "institution": app["institution"],
                "status": app["status"],
                "submission_date": app["submission_date"]
            }
            for app_id, app in applications_store.items()
        ],
        "total": len(applications_store)
    }


@app.get("/applications/{application_id}")
async def get_application(application_id: str):
    """Get application details"""
    if application_id not in applications_store:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return applications_store[application_id]


@app.delete("/applications/{application_id}")
async def delete_application(application_id: str):
    """Delete an application"""
    if application_id not in applications_store:
        raise HTTPException(status_code=404, detail="Application not found")
    
    del applications_store[application_id]
    if application_id in screening_tasks:
        del screening_tasks[application_id]
    
    return {"message": "Application deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
