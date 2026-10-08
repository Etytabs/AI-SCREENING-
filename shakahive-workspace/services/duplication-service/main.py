from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import os
import sys
import json
from sentence_transformers import SentenceTransformer, util
import torch
import numpy as np
from rapidfuzz import fuzz, process

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from shared.models import DuplicationResult, DuplicateProposal

app = FastAPI(
    title="Duplication Check Service",
    description="Checks for duplicate or similar proposals",
    version="1.0.0"
)

# Global model variable
model = None
device = None

# Configuration
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.85"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")


class DuplicationRequest(BaseModel):
    """Request for duplication check"""
    application: Dict[str, Any]
    threshold: Optional[float] = SIMILARITY_THRESHOLD


def load_model():
    """Load the sentence transformer model"""
    global model, device
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading model on device: {device}")
    
    model = SentenceTransformer(EMBEDDING_MODEL, device=device)
    print("Model loaded successfully")


@app.on_event("startup")
async def startup_event():
    """Load model on startup"""
    load_model()


@app.get("/")
async def root():
    return {
        "service": "Duplication Check Service",
        "status": "operational",
        "device": device,
        "model": EMBEDDING_MODEL,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "device": device,
        "model_loaded": model is not None
    }


def generate_mock_historical_proposals() -> List[Dict[str, Any]]:
    """Generate mock historical proposals for demonstration"""
    # In production, this would query the database
    base_date = datetime.utcnow() - timedelta(days=365)
    
    return [
        {
            "id": "hist-001",
            "title": "AI-Powered Crop Disease Detection in Rwanda",
            "abstract": "This research aims to develop innovative solutions for sustainable agriculture using machine learning algorithms for crop disease detection.",
            "author_name": "Dr. Jean Mugabo",
            "institution": "University of Rwanda",
            "submission_date": (base_date + timedelta(days=30)).isoformat(),
            "research_area": "Agriculture Technology"
        },
        {
            "id": "hist-002",
            "title": "Precision Farming Using Satellite Imagery",
            "abstract": "Our approach leverages deep learning techniques to analyze satellite imagery for precision farming and yield prediction.",
            "author_name": "Prof. Marie Claire Uwimana",
            "institution": "Rwanda Institute for Scientific Research",
            "submission_date": (base_date + timedelta(days=60)).isoformat(),
            "research_area": "Remote Sensing"
        },
        {
            "id": "hist-003",
            "title": "IoT-Based Agricultural Monitoring System",
            "abstract": "We propose a novel framework for integrating IoT sensors in agricultural monitoring systems for real-time data collection.",
            "author_name": "Eng. Patrick Niyonzima",
            "institution": "Carnegie Mellon University Africa",
            "submission_date": (base_date + timedelta(days=90)).isoformat(),
            "research_area": "IoT and Sensors"
        },
        {
            "id": "hist-004",
            "title": "Mobile Health Solutions for Rural Communities",
            "abstract": "Developing mobile-based health interventions to improve healthcare access in rural Rwandan communities.",
            "author_name": "Dr. Anne Marie Kamanzi",
            "institution": "University of Rwanda",
            "submission_date": (base_date + timedelta(days=120)).isoformat(),
            "research_area": "Digital Health"
        },
        {
            "id": "hist-005",
            "title": "Renewable Energy Solutions for Off-Grid Communities",
            "abstract": "Investigating solar and wind energy solutions for communities without access to the national grid.",
            "author_name": "Dr. Emmanuel Ndayisaba",
            "institution": "Rwanda Energy Group",
            "submission_date": (base_date + timedelta(days=150)).isoformat(),
            "research_area": "Renewable Energy"
        }
    ]


def check_title_similarity(title1: str, title2: str) -> float:
    """Check similarity between two titles using fuzzy matching"""
    return fuzz.ratio(title1.lower(), title2.lower()) / 100.0


def check_author_match(author1: str, author2: str) -> bool:
    """Check if authors match"""
    return fuzz.ratio(author1.lower(), author2.lower()) > 80


def check_institution_match(inst1: str, inst2: str) -> bool:
    """Check if institutions match"""
    return fuzz.ratio(inst1.lower(), inst2.lower()) > 80


def compute_embedding_similarity(text1: str, text2: str) -> float:
    """Compute semantic similarity using embeddings"""
    if model is None:
        return 0.0
    
    embedding1 = model.encode(text1, convert_to_tensor=True)
    embedding2 = model.encode(text2, convert_to_tensor=True)
    
    similarity = util.cos_sim(embedding1, embedding2).item()
    return similarity


@app.post("/check", response_model=DuplicationResult)
async def check_duplication(request: DuplicationRequest):
    """Check for duplicate or similar proposals"""
    try:
        application = request.application
        threshold = request.threshold or SIMILARITY_THRESHOLD
        
        # Extract application data
        title = application.get("title", "")
        abstract = application.get("abstract", "")
        author_name = application.get("author_name", "")
        institution = application.get("institution", "")
        
        # Get historical proposals
        historical_proposals = generate_mock_historical_proposals()
        
        similar_proposals = []
        potential_conflicts = []
        
        for hist_prop in historical_proposals:
            # Check title similarity
            title_similarity = check_title_similarity(title, hist_prop["title"])
            
            # Check abstract similarity
            abstract_similarity = compute_embedding_similarity(abstract, hist_prop["abstract"])
            
            # Check author/institution matches
            author_match = check_author_match(author_name, hist_prop["author_name"])
            institution_match = check_institution_match(institution, hist_prop["institution"])
            
            # Calculate overall similarity
            overall_similarity = max(title_similarity, abstract_similarity)
            
            # Identify overlapping fields
            overlapping_fields = []
            if title_similarity > 0.7:
                overlapping_fields.append("title")
            if abstract_similarity > 0.7:
                overlapping_fields.append("abstract")
            if author_match:
                overlapping_fields.append("author")
            if institution_match:
                overlapping_fields.append("institution")
            if application.get("research_area") == hist_prop.get("research_area"):
                overlapping_fields.append("research_area")
            
            # If similarity exceeds threshold, flag as potential duplicate
            if overall_similarity >= threshold or (author_match and institution_match):
                similar_proposals.append(DuplicateProposal(
                    proposal_id=hist_prop["id"],
                    title=hist_prop["title"],
                    similarity_score=overall_similarity,
                    overlapping_fields=overlapping_fields,
                    submission_date=datetime.fromisoformat(hist_prop["submission_date"]),
                    author_name=hist_prop["author_name"]
                ))
                
                # Add conflict notes
                if author_match and institution_match:
                    potential_conflicts.append(
                        f"Same author/institution as previous submission: {hist_prop['title']} ({hist_prop['submission_date'][:10]})"
                    )
                elif overall_similarity >= threshold:
                    potential_conflicts.append(
                        f"Highly similar to previous submission: {hist_prop['title']} ({hist_prop['submission_date'][:10]})"
                    )
        
        # Determine if duplicate
        is_duplicate = len(similar_proposals) > 0
        
        # Find highest similarity
        highest_similarity = max([p.similarity_score for p in similar_proposals]) if similar_proposals else 0.0
        
        return DuplicationResult(
            service_name="duplication",
            status="completed",
            score=highest_similarity,
            is_duplicate=is_duplicate,
            similar_proposals=similar_proposals,
            highest_similarity=highest_similarity,
            potential_conflicts=potential_conflicts,
            details={
                "threshold_used": threshold,
                "historical_proposals_checked": len(historical_proposals),
                "device_used": device
            },
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/add-historical")
async def add_historical_proposal(proposal: Dict[str, Any]):
    """Add a proposal to historical database (for demo purposes)"""
    # In production, this would insert into database
    return {
        "status": "success",
        "message": "Proposal added to historical database",
        "proposal_id": proposal.get("id", "unknown")
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
