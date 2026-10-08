from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Text, Boolean, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/novarai")

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=20, max_overflow=40)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class GrantApplicationDB(Base):
    """Database model for grant applications"""
    __tablename__ = "grant_applications"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    abstract = Column(Text, nullable=False)
    full_proposal = Column(Text, nullable=False)
    author_name = Column(String, nullable=False)
    institution = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    budget_amount = Column(Float, nullable=False)
    research_area = Column(String, nullable=False)
    keywords = Column(JSON, nullable=True)
    team_members = Column(JSON, nullable=True)
    attachments = Column(JSON, nullable=True)
    submission_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")
    
    # Grant-specific fields
    grant_type = Column(String, nullable=False)
    funding_program = Column(String, nullable=False)
    project_duration_months = Column(Integer, nullable=False)
    expected_outcomes = Column(JSON, nullable=True)
    
    # Tenant isolation
    tenant_id = Column(String, nullable=False, index=True)
    
    # Relationships
    screening_reports = relationship("ScreeningReportDB", back_populates="application", cascade="all, delete-orphan")


class ScreeningReportDB(Base):
    """Database model for screening reports"""
    __tablename__ = "screening_reports"
    
    id = Column(String, primary_key=True, index=True)
    application_id = Column(String, ForeignKey("grant_applications.id"), nullable=False)
    
    # Screening results (stored as JSON)
    eligibility_result = Column(JSON, nullable=True)
    plagiarism_result = Column(JSON, nullable=True)
    duplication_result = Column(JSON, nullable=True)
    novelty_result = Column(JSON, nullable=True)
    
    # Overall assessment
    overall_score = Column(Float, nullable=False)
    recommendation = Column(String, nullable=False)
    requires_human_review = Column(Boolean, default=True)
    priority_level = Column(String, nullable=False)
    
    # Metadata
    processing_time_seconds = Column(Float, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(JSON, nullable=True)
    
    # Relationship
    application = relationship("GrantApplicationDB", back_populates="screening_reports")


class HistoricalProposalDB(Base):
    """Database model for historical proposals (for duplication check)"""
    __tablename__ = "historical_proposals"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    abstract = Column(Text, nullable=False)
    author_name = Column(String, nullable=False)
    institution = Column(String, nullable=False)
    submission_date = Column(DateTime, nullable=False)
    
    # Embedding vector for similarity search
    embedding_vector = Column(JSON, nullable=True)
    
    # Metadata
    research_area = Column(String, nullable=True)
    keywords = Column(JSON, nullable=True)
    status = Column(String, nullable=True)
    
    # Tenant isolation
    tenant_id = Column(String, nullable=False, index=True)


# Registry Service Tables
class ResearcherIdentityDB(Base):
    """Permanent researcher identity record"""
    __tablename__ = "researcher_identities"
    
    permanent_id = Column(String, primary_key=True, index=True)
    orcid_id = Column(String, unique=True, nullable=True, index=True)
    email = Column(String, nullable=False, index=True)
    email_verified = Column(Boolean, default=False)
    given_name = Column(String, nullable=False)
    family_name = Column(String, nullable=False)
    name_variants = Column(JSON, nullable=True)
    primary_institution = Column(String, nullable=False)
    affiliations = Column(JSON, nullable=True)
    verification_status = Column(String, default="pending")
    verification_method = Column(String, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verified_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_tenant = Column(String, nullable=False)
    source_system = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime, nullable=True)
    deletion_reason = Column(String, nullable=True)


class TenantIdentityLinkDB(Base):
    """Links a permanent identity to a tenant-specific record"""
    __tablename__ = "tenant_identity_links"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'local_id', name='uq_tenant_local'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    permanent_id = Column(String, ForeignKey("researcher_identities.permanent_id"), nullable=False)
    tenant_id = Column(String, nullable=False, index=True)
    local_id = Column(String, nullable=False, index=True)
    linked_at = Column(DateTime, default=datetime.utcnow)
    linked_by = Column(String, nullable=True)
    link_confidence = Column(String, default="confirmed")
    match_score = Column(Integer, nullable=True)


class IdentityConflictDB(Base):
    """Record of identity conflicts detected"""
    __tablename__ = "identity_conflicts"
    
    id = Column(Integer, primary_key=True, index=True)
    conflict_type = Column(String, nullable=False)
    status = Column(String, default="open")
    permanent_id_1 = Column(String, ForeignKey("researcher_identities.permanent_id"), nullable=True)
    permanent_id_2 = Column(String, ForeignKey("researcher_identities.permanent_id"), nullable=True)
    conflict_reason = Column(String, nullable=False)
    conflicting_attributes = Column(JSON, nullable=True)
    detected_at = Column(DateTime, default=datetime.utcnow)
    detected_by = Column(String, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String, nullable=True)
    resolution_action = Column(String, nullable=True)
    resolution_notes = Column(String, nullable=True)


def get_db():
    """Database dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
