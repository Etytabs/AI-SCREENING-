"""
NOVARAai - Simplified Backend with Real AI Logic
A working prototype with actual AI capabilities for grant screening
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import sqlite3
import json
import hashlib
import os
import time

# Import AI modules
from ai.eligibility import EligibilityChecker
from ai.plagiarism import PlagiarismDetector
from ai.duplication import DuplicationChecker
from ai.novelty import NoveltyAssessor
from ai.document_extractor import DocumentExtractor

app = FastAPI(
    title="NOVARAai - NRIF Grant Screening",
    description="AI-powered grant screening with real ML models",
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

# Database setup
DB_PATH = "novarai.db"

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Applications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            abstract TEXT NOT NULL,
            applicant_name TEXT NOT NULL,
            institution TEXT NOT NULL,
            budget REAL NOT NULL,
            tenant_id TEXT DEFAULT 'nrif',
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_path TEXT,
            extracted_text TEXT,
            file_metadata TEXT
        )
    """)
    
    # Screening results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS screening_results (
            id TEXT PRIMARY KEY,
            application_id TEXT NOT NULL,
            eligibility_score REAL,
            eligibility_passed BOOLEAN,
            plagiarism_score REAL,
            plagiarism_matches TEXT,
            duplication_score REAL,
            duplication_matches TEXT,
            novelty_score REAL,
            novelty_details TEXT,
            overall_score REAL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES applications(id)
        )
    """)
    
    conn.commit()
    conn.close()

# Initialize AI modules
eligibility_checker = EligibilityChecker()
plagiarism_detector = PlagiarismDetector()
duplication_checker = DuplicationChecker()
novelty_assessor = NoveltyAssessor()
document_extractor = DocumentExtractor()

# Pydantic models
class Application(BaseModel):
    id: Optional[str] = None
    title: str
    abstract: str
    applicant_name: str
    institution: str
    budget: float
    tenant_id: str = "nrif"
    file_path: Optional[str] = None
    extracted_text: Optional[str] = None

class ScreeningResult(BaseModel):
    application_id: str
    eligibility: Dict[str, Any]
    plagiarism: Dict[str, Any]
    duplication: Dict[str, Any]
    novelty: Dict[str, Any]
    overall_score: float
    status: str

# API Endpoints

@app.get("/")
async def root():
    return {
        "service": "NOVARAai Backend",
        "version": "1.0.0",
        "status": "operational",
        "ai_modules": {
            "eligibility": "active",
            "plagiarism": "active",
            "duplication": "active",
            "novelty": "active"
        }
    }

@app.get("/applications")
async def get_applications():
    """Get all applications"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM applications ORDER BY created_at DESC")
    applications = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return {"applications": applications}

@app.post("/applications")
async def create_application(application: Application):
    """Create a new application"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Generate ID if not provided
    app_id = application.id or f"APP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    try:
        cursor.execute("""
            INSERT INTO applications 
            (id, title, abstract, applicant_name, institution, budget, tenant_id, status, extracted_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (app_id, application.title, application.abstract, 
              application.applicant_name, application.institution, 
              application.budget, application.tenant_id, 'pending', application.abstract))
        
        conn.commit()
        conn.close()
        
        return {"id": app_id, "status": "created"}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Application ID already exists")

@app.get("/applications/{app_id}")
async def get_application(app_id: str):
    """Get a specific application"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM applications WHERE id = ?", (app_id,))
    application = cursor.fetchone()
    
    conn.close()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return dict(application)

@app.delete("/applications/{app_id}")
async def delete_application(app_id: str):
    """Delete an application"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM applications WHERE id = ?", (app_id,))
    cursor.execute("DELETE FROM screening_results WHERE application_id = ?", (app_id,))
    
    conn.commit()
    conn.close()
    
    return {"message": "Application deleted"}

@app.put("/applications/{app_id}/status")
async def update_application_status(app_id: str, status: str):
    """Update application status"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE applications SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (status, app_id)
    )
    
    conn.commit()
    conn.close()
    
    return {"message": "Status updated"}

@app.post("/screen/{app_id}")
async def screen_application(app_id: str):
    """Run AI screening on an application - Optimized for fast processing"""
    start_time = time.time()
    
    # Get application
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM applications WHERE id = ?", (app_id,))
    application = cursor.fetchone()
    
    if not application:
        conn.close()
        raise HTTPException(status_code=404, detail="Application not found")
    
    app_data = dict(application)
    conn.close()
    
    # Use extracted text if available, otherwise use abstract
    text_to_analyze = app_data.get('abstract', '')
    
    print(f"Running AI screening for application {app_id}...")
    print(f"Analyzing {len(text_to_analyze)} characters of text...")
    
    # Run AI screening in sequence (optimized for speed)
    # 1. Eligibility Check
    eligibility_result = eligibility_checker.check(app_data)
    
    # 2. Plagiarism Detection
    plagiarism_result = plagiarism_detector.detect(text_to_analyze)
    
    # 3. Duplication Check
    # Get all other applications for comparison
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, abstract FROM applications WHERE id != ?", (app_id,))
    other_apps = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    duplication_result = duplication_checker.check(text_to_analyze, other_apps)
    
    # 4. Novelty Assessment
    novelty_result = novelty_assessor.assess(text_to_analyze)
    
    # Calculate overall score
    overall_score = (
        eligibility_result['score'] * 0.3 +
        plagiarism_result['originality_score'] * 0.3 +
        (100 - duplication_result['similarity_score']) * 0.2 +
        novelty_result['overall_score'] * 0.2
    )
    
    # Determine status
    if overall_score >= 70 and eligibility_result['passed']:
        status = "approved"
    elif overall_score >= 50:
        status = "pending_review"
    else:
        status = "rejected"
    
    # Save screening result
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    screening_id = f"SCR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    cursor.execute("""
        INSERT INTO screening_results 
        (id, application_id, eligibility_score, eligibility_passed, 
         plagiarism_score, plagiarism_matches, duplication_score, duplication_matches,
         novelty_score, novelty_details, overall_score, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        screening_id, app_id, eligibility_result['score'], eligibility_result['passed'],
        plagiarism_result['originality_score'], json.dumps(plagiarism_result['matches']),
        duplication_result['similarity_score'], json.dumps(duplication_result['matches']),
        novelty_result['overall_score'], json.dumps(novelty_result),
        overall_score, status
    ))
    
    # Update application status
    cursor.execute(
        "UPDATE applications SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (status, app_id)
    )
    
    conn.commit()
    conn.close()
    
    print(f"Screening completed in {processing_time:.2f} seconds")
    
    return {
        "screening_id": screening_id,
        "eligibility": eligibility_result,
        "plagiarism": plagiarism_result,
        "duplication": duplication_result,
        "novelty": novelty_result,
        "overall_score": round(overall_score, 2),
        "status": status
    }

@app.get("/screenings")
async def get_screenings():
    """Get all screening results"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT sr.*, a.title 
        FROM screening_results sr
        JOIN applications a ON sr.application_id = a.id
        ORDER BY sr.created_at DESC
    """)
    
    screenings = []
    for row in cursor.fetchall():
        screening = dict(row)
        screening['plagiarism_matches'] = json.loads(screening['plagiarism_matches'] or '[]')
        screening['duplication_matches'] = json.loads(screening['duplication_matches'] or '[]')
        screening['novelty_details'] = json.loads(screening['novelty_details'] or '{}')
        screenings.append(screening)
    
    conn.close()
    return {"screenings": screenings}

@app.post("/auth-service/login")
async def login(email: str, password: str, tenant_id: str):
    """Simple authentication (for prototype)"""
    # For prototype, accept any credentials
    return {
        "access_token": "mock-token-" + hashlib.md5(email.encode()).hexdigest(),
        "token_type": "bearer",
        "expires_in": 86400,
        "user": {
            "user_id": "user-001",
            "email": email,
            "tenant_id": tenant_id,
            "role": "admin"
        },
        "tenant": {
            "tenant_id": tenant_id,
            "tenant_name": "National Research & Innovation Fund" if tenant_id == "nrif" else tenant_id,
            "tenant_type": "funding_agency"
        }
    }

@app.post("/upload-document")
async def upload_document(file: UploadFile = File(...)):
    """Upload and extract text from a document"""
    try:
        # Create uploads directory if it doesn't exist
        uploads_dir = "uploads"
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)
        
        # Save uploaded file
        file_path = os.path.join(uploads_dir, file.filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Extract text from document
        extraction_result = document_extractor.extract(file_path, content)
        
        if not extraction_result["success"]:
            # Clean up file if extraction failed
            os.remove(file_path)
            raise HTTPException(status_code=400, detail=extraction_result["error"])
        
        return {
            "success": True,
            "file_path": file_path,
            "filename": file.filename,
            "extracted_text": extraction_result["text"],
            "metadata": extraction_result["metadata"],
            "character_count": len(extraction_result["text"])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/register")
async def register_user(
    email: str,
    password: str,
    full_name: str,
    institution: str,
    role: str = "researcher",
    tenant_id: str = "nrif"
):
    """Register a new user/researcher"""
    # For prototype, just return success
    user_id = f"USER-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    return {
        "success": True,
        "user_id": user_id,
        "email": email,
        "full_name": full_name,
        "institution": institution,
        "role": role,
        "tenant_id": tenant_id,
        "message": "Registration successful. Please login to continue."
    }

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    print("Database initialized")
    print("AI modules loaded")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
