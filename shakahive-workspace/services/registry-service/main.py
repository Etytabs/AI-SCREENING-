"""
Registry Service - Permanent Identity Management (E03)
Manages permanent researcher identities across tenants with conflict detection
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import sys
import hashlib
import json
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, JSON, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from shared.database import get_db, Base

app = FastAPI(
    title="Registry Service",
    description="Permanent identity management with cross-tenant conflict detection",
    version="2.0.0"
)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/novarai")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Registry Models
class ResearcherIdentity(Base):
    """Permanent researcher identity record"""
    __tablename__ = "researcher_identities"
    
    # Permanent unique identifier
    permanent_id = Column(String, primary_key=True, index=True)
    
    # Identity attributes (immutable after verification)
    orcid_id = Column(String, unique=True, nullable=True, index=True)
    email = Column(String, nullable=False, index=True)
    email_verified = Column(Boolean, default=False)
    
    # Name variants (for matching)
    given_name = Column(String, nullable=False)
    family_name = Column(String, nullable=False)
    name_variants = Column(JSON, nullable=True)  # List of alternative name spellings
    
    # Institutional affiliations
    primary_institution = Column(String, nullable=False)
    affiliations = Column(JSON, nullable=True)  # Historical affiliations
    
    # Verification status
    verification_status = Column(String, default="pending")  # pending, verified, rejected
    verification_method = Column(String, nullable=True)  # orcid, email, institutional
    verified_at = Column(DateTime, nullable=True)
    verified_by = Column(String, nullable=True)  # System or admin user
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_tenant = Column(String, nullable=False)  # Tenant that created the record
    source_system = Column(String, nullable=True)  # orcid, manual, import
    
    # Soft delete
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime, nullable=True)
    deletion_reason = Column(String, nullable=True)
    
    # Relationships
    tenant_links = relationship("TenantIdentityLink", back_populates="researcher", cascade="all, delete-orphan")
    verification_events = relationship("VerificationEvent", back_populates="researcher", cascade="all, delete-orphan")


class TenantIdentityLink(Base):
    """Links a permanent identity to a tenant-specific record"""
    __tablename__ = "tenant_identity_links"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'local_id', name='uq_tenant_local'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    permanent_id = Column(String, ForeignKey("researcher_identities.permanent_id"), nullable=False)
    tenant_id = Column(String, nullable=False, index=True)
    local_id = Column(String, nullable=False, index=True)  # ID in tenant's system
    
    # Link metadata
    linked_at = Column(DateTime, default=datetime.utcnow)
    linked_by = Column(String, nullable=True)
    link_confidence = Column(String, default="confirmed")  # confirmed, suspected, rejected
    match_score = Column(Integer, nullable=True)  # 0-100
    
    # Relationships
    researcher = relationship("ResearcherIdentity", back_populates="tenant_links")


class IdentityConflict(Base):
    """Record of identity conflicts detected"""
    __tablename__ = "identity_conflicts"
    
    id = Column(Integer, primary_key=True, index=True)
    conflict_type = Column(String, nullable=False)  # duplicate, similar, orcid_mismatch
    status = Column(String, default="open")  # open, resolved, dismissed
    
    # Conflicting records
    permanent_id_1 = Column(String, ForeignKey("researcher_identities.permanent_id"), nullable=True)
    permanent_id_2 = Column(String, ForeignKey("researcher_identities.permanent_id"), nullable=True)
    
    # Conflict details
    conflict_reason = Column(String, nullable=False)
    conflicting_attributes = Column(JSON, nullable=True)
    detected_at = Column(DateTime, default=datetime.utcnow)
    detected_by = Column(String, nullable=True)  # system or user
    
    # Resolution
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String, nullable=True)
    resolution_action = Column(String, nullable=True)  # merge, split, dismiss
    resolution_notes = Column(String, nullable=True)


class VerificationEvent(Base):
    """Audit trail of verification events"""
    __tablename__ = "verification_events"
    
    id = Column(Integer, primary_key=True, index=True)
    permanent_id = Column(String, ForeignKey("researcher_identities.permanent_id"), nullable=False)
    
    event_type = Column(String, nullable=False)  # created, verified, updated, merged, deleted
    event_data = Column(JSON, nullable=True)
    
    performed_by = Column(String, nullable=True)
    performed_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    # Relationships
    researcher = relationship("ResearcherIdentity", back_populates="verification_events")


# Pydantic models
class ResearcherIdentityCreate(BaseModel):
    """Request to create a new researcher identity"""
    email: EmailStr
    given_name: str
    family_name: str
    primary_institution: str
    orcid_id: Optional[str] = None
    name_variants: Optional[List[str]] = None
    affiliations: Optional[List[Dict[str, Any]]] = None
    source_system: Optional[str] = "manual"


class ResearcherIdentityUpdate(BaseModel):
    """Request to update researcher identity (restricted fields)"""
    primary_institution: Optional[str] = None
    affiliations: Optional[List[Dict[str, Any]]] = None
    name_variants: Optional[List[str]] = None


class TenantLinkRequest(BaseModel):
    """Request to link tenant record to permanent identity"""
    tenant_id: str
    local_id: str
    link_confidence: Optional[str] = "confirmed"
    match_score: Optional[int] = None


class ConflictResolution(BaseModel):
    """Request to resolve identity conflict"""
    resolution_action: str  # merge, split, dismiss
    resolution_notes: Optional[str] = None
    target_permanent_id: Optional[str] = None  # For merge actions


def generate_permanent_id(email: str, given_name: str, family_name: str) -> str:
    """Generate a permanent unique identifier"""
    data = f"{email.lower()}:{given_name.lower()}:{family_name.lower()}"
    hash_obj = hashlib.sha256(data.encode())
    return f"RID-{hash_obj.hexdigest()[:16].upper()}"


def detect_conflicts(
    db: Session,
    email: str,
    given_name: str,
    family_name: str,
    orcid_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Detect potential identity conflicts"""
    conflicts = []
    
    # Check for exact email match
    existing = db.query(ResearcherIdentity).filter(
        ResearcherIdentity.email == email,
        ResearcherIdentity.is_active == True
    ).first()
    
    if existing:
        conflicts.append({
            "type": "duplicate",
            "permanent_id": existing.permanent_id,
            "reason": "Email already exists",
            "existing_record": {
                "permanent_id": existing.permanent_id,
                "given_name": existing.given_name,
                "family_name": existing.family_name,
                "institution": existing.primary_institution
            }
        })
    
    # Check for ORCID conflict
    if orcid_id:
        existing_orcid = db.query(ResearcherIdentity).filter(
            ResearcherIdentity.orcid_id == orcid_id,
            ResearcherIdentity.is_active == True
        ).first()
        
        if existing_orcid:
            conflicts.append({
                "type": "orcid_mismatch",
                "permanent_id": existing_orcid.permanent_id,
                "reason": "ORCID already linked to different identity",
                "existing_record": {
                    "permanent_id": existing_orcid.permanent_id,
                    "email": existing_orcid.email,
                    "given_name": existing_orcid.given_name,
                    "family_name": existing_orcid.family_name
                }
            })
    
    # Check for similar names (fuzzy matching)
    similar = db.query(ResearcherIdentity).filter(
        ResearcherIdentity.is_active == True
    ).all()
    
    for record in similar:
        name_similarity = (
            fuzz.ratio(given_name.lower(), record.given_name.lower()) +
            fuzz.ratio(family_name.lower(), record.family_name.lower())
        ) / 2
        
        if name_similarity > 80 and record.permanent_id not in [c.get("permanent_id") for c in conflicts]:
            conflicts.append({
                "type": "similar",
                "permanent_id": record.permanent_id,
                "reason": f"High name similarity ({name_similarity:.0f}%)",
                "existing_record": {
                    "permanent_id": record.permanent_id,
                    "given_name": record.given_name,
                    "family_name": record.family_name,
                    "email": record.email
                }
            })
    
    return conflicts


from rapidfuzz import fuzz


@app.get("/")
async def root():
    return {
        "service": "Registry Service",
        "version": "2.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/identities", response_model=Dict[str, Any])
async def create_identity(
    identity: ResearcherIdentityCreate,
    tenant_id: str = Header(..., alias="X-Tenant-ID"),
    db: Session = Depends(get_db)
):
    """Create a new researcher identity with conflict detection"""
    
    # Detect conflicts
    conflicts = detect_conflicts(
        db,
        identity.email,
        identity.given_name,
        identity.family_name,
        identity.orcid_id
    )
    
    # Block if duplicate or ORCID conflict
    blocking_conflicts = [c for c in conflicts if c["type"] in ["duplicate", "orcid_mismatch"]]
    if blocking_conflicts:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "Identity conflict detected",
                "conflicts": blocking_conflicts,
                "message": "Cannot create identity due to blocking conflicts"
            }
        )
    
    # Generate permanent ID
    permanent_id = generate_permanent_id(
        identity.email,
        identity.given_name,
        identity.family_name
    )
    
    # Create identity record
    researcher = ResearcherIdentity(
        permanent_id=permanent_id,
        email=identity.email,
        given_name=identity.given_name,
        family_name=identity.family_name,
        primary_institution=identity.primary_institution,
        orcid_id=identity.orcid_id,
        name_variants=identity.name_variants or [],
        affiliations=identity.affiliations or [],
        created_by_tenant=tenant_id,
        source_system=identity.source_system
    )
    
    db.add(researcher)
    
    # Log similar conflicts for review
    for conflict in [c for c in conflicts if c["type"] == "similar"]:
        conflict_record = IdentityConflict(
            conflict_type="similar",
            permanent_id_1=permanent_id,
            permanent_id_2=conflict["permanent_id"],
            conflict_reason=conflict["reason"],
            conflicting_attributes=conflict["existing_record"],
            detected_by="system"
        )
        db.add(conflict_record)
    
    # Log creation event
    event = VerificationEvent(
        permanent_id=permanent_id,
        event_type="created",
        event_data={"source": "api", "tenant": tenant_id}
    )
    db.add(event)
    
    db.commit()
    db.refresh(researcher)
    
    return {
        "permanent_id": permanent_id,
        "status": "created",
        "verification_status": researcher.verification_status,
        "conflicts_detected": len(conflicts),
        "similar_identities": [c for c in conflicts if c["type"] == "similar"]
    }


@app.get("/identities/{permanent_id}")
async def get_identity(
    permanent_id: str,
    tenant_id: str = Header(..., alias="X-Tenant-ID"),
    db: Session = Depends(get_db)
):
    """Get researcher identity by permanent ID"""
    researcher = db.query(ResearcherIdentity).filter(
        ResearcherIdentity.permanent_id == permanent_id,
        ResearcherIdentity.is_active == True
    ).first()
    
    if not researcher:
        raise HTTPException(status_code=404, detail="Identity not found")
    
    # Get tenant links
    links = db.query(TenantIdentityLink).filter(
        TenantIdentityLink.permanent_id == permanent_id
    ).all()
    
    return {
        "permanent_id": researcher.permanent_id,
        "email": researcher.email,
        "email_verified": researcher.email_verified,
        "given_name": researcher.given_name,
        "family_name": researcher.family_name,
        "orcid_id": researcher.orcid_id,
        "primary_institution": researcher.primary_institution,
        "affiliations": researcher.affiliations,
        "verification_status": researcher.verification_status,
        "verification_method": researcher.verification_method,
        "created_at": researcher.created_at,
        "tenant_links": [
            {
                "tenant_id": link.tenant_id,
                "local_id": link.local_id,
                "link_confidence": link.link_confidence,
                "linked_at": link.linked_at
            }
            for link in links
        ]
    }


@app.post("/identities/{permanent_id}/verify")
async def verify_identity(
    permanent_id: str,
    verification_method: str,
    tenant_id: str = Header(..., alias="X-Tenant-ID"),
    db: Session = Depends(get_db)
):
    """Verify researcher identity (ORCID, email, or institutional)"""
    researcher = db.query(ResearcherIdentity).filter(
        ResearcherIdentity.permanent_id == permanent_id,
        ResearcherIdentity.is_active == True
    ).first()
    
    if not researcher:
        raise HTTPException(status_code=404, detail="Identity not found")
    
    if researcher.verification_status == "verified":
        raise HTTPException(status_code=400, detail="Identity already verified")
    
    # Update verification status
    researcher.verification_status = "verified"
    researcher.verification_method = verification_method
    researcher.verified_at = datetime.utcnow()
    researcher.verified_by = tenant_id
    
    # Log verification event
    event = VerificationEvent(
        permanent_id=permanent_id,
        event_type="verified",
        event_data={"method": verification_method, "tenant": tenant_id}
    )
    db.add(event)
    
    db.commit()
    
    return {
        "permanent_id": permanent_id,
        "status": "verified",
        "verification_method": verification_method,
        "verified_at": researcher.verified_at
    }


@app.post("/identities/{permanent_id}/links")
async def link_tenant_record(
    permanent_id: str,
    link_request: TenantLinkRequest,
    tenant_id: str = Header(..., alias="X-Tenant-ID"),
    db: Session = Depends(get_db)
):
    """Link a tenant-specific record to a permanent identity"""
    researcher = db.query(ResearcherIdentity).filter(
        ResearcherIdentity.permanent_id == permanent_id,
        ResearcherIdentity.is_active == True
    ).first()
    
    if not researcher:
        raise HTTPException(status_code=404, detail="Identity not found")
    
    # Check if link already exists
    existing = db.query(TenantIdentityLink).filter(
        TenantIdentityLink.permanent_id == permanent_id,
        TenantIdentityLink.tenant_id == link_request.tenant_id,
        TenantIdentityLink.local_id == link_request.local_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=409, detail="Link already exists")
    
    # Create link
    link = TenantIdentityLink(
        permanent_id=permanent_id,
        tenant_id=link_request.tenant_id,
        local_id=link_request.local_id,
        link_confidence=link_request.link_confidence,
        match_score=link_request.match_score,
        linked_by=tenant_id
    )
    
    db.add(link)
    db.commit()
    
    return {
        "status": "linked",
        "permanent_id": permanent_id,
        "tenant_id": link_request.tenant_id,
        "local_id": link_request.local_id
    }


@app.get("/conflicts")
async def list_conflicts(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List identity conflicts"""
    query = db.query(IdentityConflict)
    
    if status:
        query = query.filter(IdentityConflict.status == status)
    
    conflicts = query.order_by(IdentityConflict.detected_at.desc()).all()
    
    return {
        "conflicts": [
            {
                "id": conflict.id,
                "type": conflict.conflict_type,
                "status": conflict.status,
                "permanent_id_1": conflict.permanent_id_1,
                "permanent_id_2": conflict.permanent_id_2,
                "reason": conflict.conflict_reason,
                "detected_at": conflict.detected_at
            }
            for conflict in conflicts
        ],
        "total": len(conflicts)
    }


@app.post("/conflicts/{conflict_id}/resolve")
async def resolve_conflict(
    conflict_id: int,
    resolution: ConflictResolution,
    tenant_id: str = Header(..., alias="X-Tenant-ID"),
    db: Session = Depends(get_db)
):
    """Resolve an identity conflict"""
    conflict = db.query(IdentityConflict).filter(
        IdentityConflict.id == conflict_id
    ).first()
    
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")
    
    if conflict.status != "open":
        raise HTTPException(status_code=400, detail="Conflict already resolved")
    
    # Update conflict
    conflict.status = "resolved"
    conflict.resolution_action = resolution.resolution_action
    conflict.resolution_notes = resolution.resolution_notes
    conflict.resolved_at = datetime.utcnow()
    conflict.resolved_by = tenant_id
    
    # Handle merge action
    if resolution.resolution_action == "merge" and resolution.target_permanent_id:
        # Implement merge logic (would merge records and update links)
        pass
    
    db.commit()
    
    return {
        "conflict_id": conflict_id,
        "status": "resolved",
        "action": resolution.resolution_action
    }


@app.get("/identities/search")
async def search_identities(
    email: Optional[str] = None,
    orcid_id: Optional[str] = None,
    name: Optional[str] = None,
    institution: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Search for researcher identities"""
    query = db.query(ResearcherIdentity).filter(
        ResearcherIdentity.is_active == True
    )
    
    if email:
        query = query.filter(ResearcherIdentity.email == email)
    
    if orcid_id:
        query = query.filter(ResearcherIdentity.orcid_id == orcid_id)
    
    if name:
        query = query.filter(
            (ResearcherIdentity.given_name.ilike(f"%{name}%")) |
            (ResearcherIdentity.family_name.ilike(f"%{name}%"))
        )
    
    if institution:
        query = query.filter(ResearcherIdentity.primary_institution.ilike(f"%{institution}%"))
    
    results = query.limit(50).all()
    
    return {
        "identities": [
            {
                "permanent_id": r.permanent_id,
                "email": r.email,
                "given_name": r.given_name,
                "family_name": r.family_name,
                "orcid_id": r.orcid_id,
                "primary_institution": r.primary_institution,
                "verification_status": r.verification_status
            }
            for r in results
        ],
        "total": len(results)
    }


if __name__ == "__main__":
    import uvicorn
    # Create tables
    Base.metadata.create_all(bind=engine)
    uvicorn.run(app, host="0.0.0.0", port=8006)
