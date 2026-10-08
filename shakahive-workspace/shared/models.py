from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ApplicationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ScreeningResult(BaseModel):
    """Base model for screening results"""
    service_name: str
    status: str
    score: Optional[float] = None
    details: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EligibilityCriteria(BaseModel):
    """Eligibility criteria for grant applications"""
    institution_type: Optional[str] = None
    min_researchers: Optional[int] = None
    max_budget: Optional[float] = None
    required_fields: List[str] = []
    excluded_institutions: List[str] = []
    required_certifications: List[str] = []


class EligibilityResult(ScreeningResult):
    """Result of eligibility screening"""
    is_eligible: bool
    missing_requirements: List[str] = []
    satisfied_requirements: List[str] = []
    disqualification_reasons: List[str] = []


class PlagiarismMatch(BaseModel):
    """Individual plagiarism match"""
    source_text: str
    matched_text: str
    similarity_score: float
    source_document: str
    start_position: int
    end_position: int


class PlagiarismResult(ScreeningResult):
    """Result of plagiarism detection"""
    overall_similarity: float
    is_plagiarized: bool
    matches: List[PlagiarismMatch] = []
    flagged_sections: List[str] = []
    originality_score: float


class DuplicateProposal(BaseModel):
    """Duplicate proposal information"""
    proposal_id: str
    title: str
    similarity_score: float
    overlapping_fields: List[str]
    submission_date: datetime
    author_name: str


class DuplicationResult(ScreeningResult):
    """Result of duplication check"""
    is_duplicate: bool
    similar_proposals: List[DuplicateProposal] = []
    highest_similarity: float
    potential_conflicts: List[str] = []


class NoveltyScore(BaseModel):
    """Novelty assessment components"""
    technical_novelty: float
    methodological_novelty: float
    application_novelty: float
    market_novelty: float


class NoveltyResult(ScreeningResult):
    """Result of novelty assessment"""
    overall_novelty_score: float
    is_novel: bool
    novelty_breakdown: NoveltyScore
    similar_works: List[Dict[str, Any]] = []
    innovation_potential: str
    ip_considerations: List[str] = []


class ScreeningReport(BaseModel):
    """Complete screening report"""
    application_id: str
    application_title: str
    submitted_by: str
    submission_date: datetime
    
    # Screening results
    eligibility: EligibilityResult
    plagiarism: PlagiarismResult
    duplication: DuplicationResult
    novelty: NoveltyResult
    
    # Overall assessment
    overall_score: float
    recommendation: str
    requires_human_review: bool
    priority_level: str
    
    # Additional metadata
    processing_time_seconds: float
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    notes: List[str] = []


class GrantApplication(BaseModel):
    """Grant application model"""
    id: Optional[str] = None
    title: str
    abstract: str
    full_proposal: str
    author_name: str
    institution: str
    email: str
    phone: Optional[str] = None
    budget_amount: float
    research_area: str
    keywords: List[str] = []
    team_members: List[Dict[str, str]] = []
    attachments: List[str] = []
    submission_date: datetime = Field(default_factory=datetime.utcnow)
    status: ApplicationStatus = ApplicationStatus.PENDING
    
    # Grant-specific fields
    grant_type: str
    funding_program: str
    project_duration_months: int
    expected_outcomes: List[str] = []


class ScreeningRequest(BaseModel):
    """Request to screen an application"""
    application_id: str
    eligibility_criteria: Optional[EligibilityCriteria] = None
    skip_plagiarism: bool = False
    skip_duplication: bool = False
    skip_novelty: bool = False
    priority: str = "normal"  # low, normal, high
