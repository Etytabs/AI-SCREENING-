from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import sys
import json
from jinja2 import Template
import base64

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from shared.models import ScreeningReport

app = FastAPI(
    title="Report Generation Service",
    description="Generates comprehensive screening reports",
    version="1.0.0"
)


class ReportRequest(BaseModel):
    """Request for report generation"""
    application_id: str
    eligibility: Optional[Dict[str, Any]] = None
    plagiarism: Optional[Dict[str, Any]] = None
    duplication: Optional[Dict[str, Any]] = None
    novelty: Optional[Dict[str, Any]] = None


def calculate_overall_score(
    eligibility: Dict,
    plagiarism: Dict,
    duplication: Dict,
    novelty: Dict
) -> float:
    """Calculate overall screening score"""
    scores = []
    
    if eligibility and "score" in eligibility:
        scores.append(eligibility["score"])
    
    if plagiarism:
        # Originality score (inverse of plagiarism)
        originality = plagiarism.get("originality_score", 50)
        scores.append(originality)
    
    if duplication:
        # Lower duplication is better
        dup_score = 100 - (duplication.get("highest_similarity", 0) * 100)
        scores.append(dup_score)
    
    if novelty and "score" in novelty:
        scores.append(novelty["score"] * 100)
    
    if not scores:
        return 50.0  # Default score
    
    return sum(scores) / len(scores)


def determine_recommendation(
    eligibility: Dict,
    plagiarism: Dict,
    duplication: Dict,
    novelty: Dict,
    overall_score: float
) -> str:
    """Determine overall recommendation"""
    # Check for disqualifying factors
    if eligibility and not eligibility.get("is_eligible", True):
        return "REJECT - Not eligible for funding"
    
    if plagiarism and plagiarism.get("is_plagiarized", False):
        return "REJECT - Plagiarism detected"
    
    if duplication and duplication.get("is_duplicate", False):
        return "REVIEW - Potential duplicate submission"
    
    # Score-based recommendation
    if overall_score >= 80:
        return "ACCEPT - High quality proposal"
    elif overall_score >= 60:
        return "ACCEPT - Meets minimum requirements"
    elif overall_score >= 40:
        return "REVIEW - Requires further evaluation"
    else:
        return "REJECT - Does not meet standards"


def determine_priority_level(
    eligibility: Dict,
    plagiarism: Dict,
    duplication: Dict,
    novelty: Dict,
    overall_score: float
) -> str:
    """Determine priority level for human review"""
    # High priority if issues detected
    if eligibility and not eligibility.get("is_eligible", True):
        return "HIGH"
    
    if plagiarism and plagiarism.get("is_plagiarized", False):
        return "HIGH"
    
    if duplication and duplication.get("is_duplicate", False):
        return "HIGH"
    
    if novelty and novelty.get("is_novel", True) == False:
        return "MEDIUM"
    
    # Score-based priority
    if overall_score < 40:
        return "HIGH"
    elif overall_score < 60:
        return "MEDIUM"
    else:
        return "LOW"


def generate_notes(
    eligibility: Dict,
    plagiarism: Dict,
    duplication: Dict,
    novelty: Dict
) -> List[str]:
    """Generate notes for human reviewers"""
    notes = []
    
    if eligibility:
        if not eligibility.get("is_eligible", True):
            notes.append(f"Eligibility issues: {', '.join(eligibility.get('disqualification_reasons', []))}")
        if eligibility.get("missing_requirements"):
            notes.append(f"Missing requirements: {', '.join(eligibility['missing_requirements'])}")
    
    if plagiarism and plagiarism.get("is_plagiarized", False):
        notes.append(f"Plagiarism detected with {plagiarism.get('overall_similarity', 0):.1%} similarity")
        notes.append(f"Flagged sections: {len(plagiarism.get('flagged_sections', []))}")
    
    if duplication and duplication.get("is_duplicate", False):
        notes.append(f"Potential duplicate: {len(duplication.get('similar_proposals', []))} similar proposals found")
        notes.append(f"Highest similarity: {duplication.get('highest_similarity', 0):.1%}")
    
    if novelty:
        if not novelty.get("is_novel", True):
            notes.append(f"Low novelty score: {novelty.get('overall_novelty_score', 0):.1%}")
        notes.append(f"Innovation potential: {novelty.get('innovation_potential', 'Unknown')}")
        if novelty.get("ip_considerations"):
            notes.append(f"IP considerations: {', '.join(novelty['ip_considerations'])}")
    
    return notes


@app.get("/")
async def root():
    return {
        "service": "Report Generation Service",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/generate", response_model=ScreeningReport)
async def generate_report(request: ReportRequest):
    """Generate comprehensive screening report"""
    try:
        # Calculate overall metrics
        overall_score = calculate_overall_score(
            request.eligibility,
            request.plagiarism,
            request.duplication,
            request.novelty
        )
        
        recommendation = determine_recommendation(
            request.eligibility,
            request.plagiarism,
            request.duplication,
            request.novelty,
            overall_score
        )
        
        priority_level = determine_priority_level(
            request.eligibility,
            request.plagiarism,
            request.duplication,
            request.novelty,
            overall_score
        )
        
        # Determine if human review is required
        requires_human_review = (
            priority_level in ["HIGH", "MEDIUM"] or
            overall_score < 70 or
            (request.eligibility and not request.eligibility.get("is_eligible", True)) or
            (request.plagiarism and request.plagiarism.get("is_plagiarized", False)) or
            (request.duplication and request.duplication.get("is_duplicate", False))
        )
        
        # Generate notes
        notes = generate_notes(
            request.eligibility,
            request.plagiarism,
            request.duplication,
            request.novelty
        )
        
        # Create report (in production, fetch application details from database)
        report = ScreeningReport(
            application_id=request.application_id,
            application_title="Sample Application Title",  # Would fetch from DB
            submitted_by="Sample Author",  # Would fetch from DB
            submission_date=datetime.utcnow(),
            eligibility=request.eligibility or {},
            plagiarism=request.plagiarism or {},
            duplication=request.duplication or {},
            novelty=request.novelty or {},
            overall_score=overall_score,
            recommendation=recommendation,
            requires_human_review=requires_human_review,
            priority_level=priority_level,
            processing_time_seconds=0.0,  # Would calculate from actual timing
            notes=notes
        )
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-html")
async def generate_html_report(request: ReportRequest):
    """Generate HTML-formatted report"""
    report = await generate_report(request)
    
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Screening Report - {{ report.application_id }}</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .header { background: #2c3e50; color: white; padding: 20px; }
            .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; }
            .pass { color: green; font-weight: bold; }
            .fail { color: red; font-weight: bold; }
            .warning { color: orange; font-weight: bold; }
            .score { font-size: 24px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>NOVARAai Screening Report</h1>
            <p>Application ID: {{ report.application_id }}</p>
            <p>Generated: {{ report.generated_at }}</p>
        </div>
        
        <div class="section">
            <h2>Overall Assessment</h2>
            <p class="score">Score: {{ "%.1f"|format(report.overall_score) }}/100</p>
            <p class="{{ 'pass' if 'ACCEPT' in report.recommendation else 'fail' }}">
                Recommendation: {{ report.recommendation }}
            </p>
            <p>Priority: {{ report.priority_level }}</p>
            <p>Human Review Required: {{ report.requires_human_review }}</p>
        </div>
        
        <div class="section">
            <h2>Eligibility Check</h2>
            <p>Status: {{ report.eligibility.status }}</p>
            <p>Eligible: {{ report.eligibility.is_eligible }}</p>
            <p>Score: {{ "%.1f"|format(report.eligibility.score or 0) }}</p>
        </div>
        
        <div class="section">
            <h2>Plagiarism Detection</h2>
            <p>Status: {{ report.plagiarism.status }}</p>
            <p>Plagiarized: {{ report.plagiarism.is_plagiarized }}</p>
            <p>Similarity: {{ "%.1f"|format(report.plagiarism.overall_similarity * 100 or 0) }}%</p>
            <p>Originality Score: {{ "%.1f"|format(report.plagiarism.originality_score or 0) }}</p>
        </div>
        
        <div class="section">
            <h2>Duplication Check</h2>
            <p>Status: {{ report.duplication.status }}</p>
            <p>Duplicate: {{ report.duplication.is_duplicate }}</p>
            <p>Highest Similarity: {{ "%.1f"|format(report.duplication.highest_similarity * 100 or 0) }}%</p>
        </div>
        
        <div class="section">
            <h2>Novelty Assessment</h2>
            <p>Status: {{ report.novelty.status }}</p>
            <p>Novel: {{ report.novelty.is_novel }}</p>
            <p>Overall Novelty: {{ "%.1f"|format(report.novelty.overall_novelty_score * 100 or 0) }}%</p>
            <p>Innovation Potential: {{ report.novelty.innovation_potential }}</p>
        </div>
        
        <div class="section">
            <h2>Notes for Reviewers</h2>
            <ul>
                {% for note in report.notes %}
                <li>{{ note }}</li>
                {% endfor %}
            </ul>
        </div>
    </body>
    </html>
    """
    
    template = Template(html_template)
    html_content = template.render(report=report)
    
    return {
        "application_id": request.application_id,
        "html_content": html_content,
        "content_type": "text/html"
    }


@app.post("/generate-pdf")
async def generate_pdf_report(request: ReportRequest):
    """Generate PDF report (placeholder - requires PDF library)"""
    # In production, use libraries like weasyprint or reportlab
    html_response = await generate_html_report(request)
    
    return {
        "application_id": request.application_id,
        "message": "PDF generation requires additional dependencies (weasyprint/reportlab)",
        "html_content": html_response["html_content"],
        "note": "Convert HTML to PDF using your preferred library"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
