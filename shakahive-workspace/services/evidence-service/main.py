"""
Evidence Service - Evidence Matrix and Retrieval (E06)
Manages evidence matrix, retrieval, and citation support
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

app = FastAPI(
    title="Evidence Service",
    description="Evidence matrix and retrieval system",
    version="2.0.0"
)


class EvidenceType(str, Enum):
    PUBLICATION = "publication"
    PATENT = "patent"
    GRANT = "grant"
    WEBSITE = "website"
    REPORT = "report"


class EvidenceSource(str, Enum):
    CROSSREF = "crossref"
    OPENALEX = "openalex"
    EPO = "epo"
    MANUAL = "manual"
    INTEGRATION = "integration"


class EvidenceRecord(BaseModel):
    """Individual evidence record"""
    evidence_id: str
    evidence_type: EvidenceType
    source: EvidenceSource
    source_id: str  # DOI, patent number, etc.
    title: str
    authors: List[str] = []
    year: Optional[int] = None
    url: Optional[str] = None
    similarity_score: Optional[float] = None
    relevance_score: Optional[float] = None
    extracted_at: datetime = Field(default_factory=datetime.utcnow)


class EvidenceMatrix(BaseModel):
    """Evidence matrix for an application"""
    application_id: str
    evidence_records: List[EvidenceRecord] = []
    total_evidence: int = 0
    high_similarity_count: int = 0
    medium_similarity_count: int = 0
    low_similarity_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RetrievalQuery(BaseModel):
    """Query for evidence retrieval"""
    application_id: str
    query_text: str
    max_results: int = 50
    min_similarity: float = 0.5
    evidence_types: Optional[List[EvidenceType]] = None


class RetrievalResult(BaseModel):
    """Result of evidence retrieval"""
    application_id: str
    query_text: str
    results: List[EvidenceRecord] = []
    total_found: int = 0
    retrieval_time_ms: float = 0.0
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)


class CitationSupport(BaseModel):
    """Citation support analysis"""
    application_id: str
    claim: str
    supporting_evidence: List[str] = []  # evidence_ids
    confidence_score: float
    needs_verification: bool = False
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


# In-memory storage (in production, use database)
evidence_matrices = {}
retrieval_history = {}
citation_analyses = {}


def generate_evidence_id() -> str:
    """Generate unique evidence ID"""
    import hashlib
    import time
    return f"EVID-{int(time.time())}-{hashlib.md5(os.urandom(8)).hexdigest()[:8].upper()}"


@app.get("/")
async def root():
    return {
        "service": "Evidence Service",
        "version": "2.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/evidence-matrix/{application_id}", response_model=EvidenceMatrix)
async def create_evidence_matrix(
    application_id: str,
    evidence_records: List[EvidenceRecord]
):
    """Create or update evidence matrix for an application"""
    # Calculate similarity distribution
    high_sim = sum(1 for e in evidence_records if e.similarity_score and e.similarity_score >= 0.8)
    medium_sim = sum(1 for e in evidence_records if e.similarity_score and 0.5 <= e.similarity_score < 0.8)
    low_sim = sum(1 for e in evidence_records if e.similarity_score and e.similarity_score < 0.5)
    
    matrix = EvidenceMatrix(
        application_id=application_id,
        evidence_records=evidence_records,
        total_evidence=len(evidence_records),
        high_similarity_count=high_sim,
        medium_similarity_count=medium_sim,
        low_similarity_count=low_sim
    )
    
    evidence_matrices[application_id] = matrix.dict()
    
    return matrix


@app.get("/evidence-matrix/{application_id}", response_model=EvidenceMatrix)
async def get_evidence_matrix(application_id: str):
    """Get evidence matrix for an application"""
    if application_id not in evidence_matrices:
        raise HTTPException(status_code=404, detail="Evidence matrix not found")
    
    return EvidenceMatrix(**evidence_matrices[application_id])


@app.post("/retrieve", response_model=RetrievalResult)
async def retrieve_evidence(query: RetrievalQuery):
    """Retrieve evidence based on query"""
    import time
    start_time = time.time()
    
    # Mock retrieval - in production, would query integration service
    mock_results = []
    for i in range(min(query.max_results, 10)):
        mock_results.append(EvidenceRecord(
            evidence_id=generate_evidence_id(),
            evidence_type=EvidenceType.PUBLICATION,
            source=EvidenceSource.CROSSREF,
            source_id=f"10.1234/mock.{i}",
            title=f"Mock publication {i+1} related to {query.query_text[:30]}",
            authors=[f"Author {i+1}"],
            year=2023 - i,
            similarity_score=0.9 - (i * 0.05),
            relevance_score=0.85 - (i * 0.03)
        ))
    
    retrieval_time = (time.time() - start_time) * 1000
    
    result = RetrievalResult(
        application_id=query.application_id,
        query_text=query.query_text,
        results=mock_results,
        total_found=len(mock_results),
        retrieval_time_ms=retrieval_time
    )
    
    retrieval_history[f"{query.application_id}-{int(time.time())}"] = result.dict()
    
    return result


@app.post("/citation-support", response_model=CitationSupport)
async def analyze_citation_support(
    application_id: str,
    claim: str
):
    """Analyze citation support for a claim"""
    # Mock analysis - in production, would use NLP
    supporting_evidence = []
    confidence = 0.75
    
    # Check if evidence matrix exists
    if application_id in evidence_matrices:
        matrix = evidence_matrices[application_id]
        high_sim_evidence = [
            e for e in matrix["evidence_records"]
            if e.get("similarity_score", 0) >= 0.8
        ]
        supporting_evidence = [e["evidence_id"] for e in high_sim_evidence[:3]]
        confidence = min(0.95, 0.7 + len(supporting_evidence) * 0.1)
    
    analysis = CitationSupport(
        application_id=application_id,
        claim=claim,
        supporting_evidence=supporting_evidence,
        confidence_score=confidence,
        needs_verification=confidence < 0.8
    )
    
    citation_analyses[f"{application_id}-{hash(claim)}"] = analysis.dict()
    
    return analysis


@app.get("/evidence/{evidence_id}")
async def get_evidence(evidence_id: str):
    """Get individual evidence record"""
    for matrix in evidence_matrices.values():
        for evidence in matrix["evidence_records"]:
            if evidence["evidence_id"] == evidence_id:
                return evidence
    
    raise HTTPException(status_code=404, detail="Evidence record not found")


@app.put("/evidence/{evidence_id}")
async def update_evidence(
    evidence_id: str,
    similarity_score: Optional[float] = None,
    relevance_score: Optional[float] = None,
    notes: Optional[str] = None
):
    """Update evidence record"""
    for matrix in evidence_matrices.values():
        for evidence in matrix["evidence_records"]:
            if evidence["evidence_id"] == evidence_id:
                if similarity_score is not None:
                    evidence["similarity_score"] = similarity_score
                if relevance_score is not None:
                    evidence["relevance_score"] = relevance_score
                if notes is not None:
                    evidence["notes"] = notes
                return {"message": "Evidence updated", "evidence_id": evidence_id}
    
    raise HTTPException(status_code=404, detail="Evidence record not found")


@app.delete("/evidence-matrix/{application_id}")
async def delete_evidence_matrix(application_id: str):
    """Delete evidence matrix"""
    if application_id not in evidence_matrices:
        raise HTTPException(status_code=404, detail="Evidence matrix not found")
    
    del evidence_matrices[application_id]
    return {"message": "Evidence matrix deleted"}


@app.get("/applications/{application_id}/evidence-summary")
async def get_evidence_summary(application_id: str):
    """Get summary of evidence for an application"""
    if application_id not in evidence_matrices:
        raise HTTPException(status_code=404, detail="Evidence matrix not found")
    
    matrix = evidence_matrices[application_id]
    
    return {
        "application_id": application_id,
        "total_evidence": matrix["total_evidence"],
        "similarity_distribution": {
            "high": matrix["high_similarity_count"],
            "medium": matrix["medium_similarity_count"],
            "low": matrix["low_similarity_count"]
        },
        "evidence_by_type": {},
        "evidence_by_source": {},
        "last_updated": matrix["updated_at"]
    }


if __name__ == "__main__":
    import uvicorn
    from enum import Enum
    uvicorn.run(app, host="0.0.0.0", port=8011)
