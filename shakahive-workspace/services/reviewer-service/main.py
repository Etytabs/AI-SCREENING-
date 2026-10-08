"""
Reviewer Service - Human Review Workflow (E07)
Manages reviewer workflow, conflict guards, and traceable decisions
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

app = FastAPI(
    title="Reviewer Service",
    description="Human review workflow with conflict guards",
    version="2.0.0"
)


class ReviewStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    APPROVED = "approved"
    REJECTED = "rejected"
    RETURNED = "returned"


class DecisionType(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"
    ESCALATE = "escalate"


class ReviewAssignment(BaseModel):
    """Review assignment model"""
    assignment_id: str
    application_id: str
    reviewer_id: str
    assigned_by: str
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = None
    status: ReviewStatus = ReviewStatus.PENDING
    priority: str = "normal"  # low, normal, high


class ReviewDecision(BaseModel):
    """Review decision model"""
    decision_id: str
    assignment_id: str
    application_id: str
    reviewer_id: str
    decision_type: DecisionType
    decision_reason: str
    comments: Optional[str] = None
    confidence_level: Optional[str] = None  # high, medium, low
    decision_at: datetime = Field(default_factory=datetime.utcnow)
    version_hash: Optional[str] = None  # For conflict detection


class ReviewConflict(BaseModel):
    """Review conflict record"""
    conflict_id: str
    application_id: str
    conflict_type: str  # version_mismatch, simultaneous_edit, decision_conflict
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    detected_by: str
    description: str
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None


class ReviewWorkflow(BaseModel):
    """Complete review workflow for an application"""
    application_id: str
    assignments: List[ReviewAssignment] = []
    decisions: List[ReviewDecision] = []
    conflicts: List[ReviewConflict] = []
    overall_status: ReviewStatus
    final_decision: Optional[DecisionType] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# In-memory storage (in production, use database)
review_workflows = {}
assignments = {}
decisions = {}
conflicts = {}


def generate_assignment_id() -> str:
    """Generate unique assignment ID"""
    import hashlib
    import time
    return f"ASSIGN-{int(time.time())}-{hashlib.md5(os.urandom(8)).hexdigest()[:8].upper()}"


def generate_decision_id() -> str:
    """Generate unique decision ID"""
    import hashlib
    import time
    return f"DEC-{int(time.time())}-{hashlib.md5(os.urandom(8)).hexdigest()[:8].upper()}"


def generate_conflict_id() -> str:
    """Generate unique conflict ID"""
    import hashlib
    import time
    return f"CONF-{int(time.time())}-{hashlib.md5(os.urandom(8)).hexdigest()[:8].upper()}"


@app.get("/")
async def root():
    return {
        "service": "Reviewer Service",
        "version": "2.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/workflows/{application_id}", response_model=ReviewWorkflow)
async def create_review_workflow(application_id: str):
    """Create a new review workflow for an application"""
    if application_id in review_workflows:
        raise HTTPException(status_code=409, detail="Review workflow already exists")
    
    workflow = ReviewWorkflow(
        application_id=application_id,
        overall_status=ReviewStatus.PENDING
    )
    
    review_workflows[application_id] = workflow.dict()
    
    return workflow


@app.get("/workflows/{application_id}", response_model=ReviewWorkflow)
async def get_review_workflow(application_id: str):
    """Get review workflow for an application"""
    if application_id not in review_workflows:
        raise HTTPException(status_code=404, detail="Review workflow not found")
    
    return ReviewWorkflow(**review_workflows[application_id])


@app.post("/assignments", response_model=ReviewAssignment)
async def assign_reviewer(
    application_id: str,
    reviewer_id: str,
    assigned_by: str,
    due_date: Optional[datetime] = None,
    priority: str = "normal"
):
    """Assign a reviewer to an application"""
    if application_id not in review_workflows:
        raise HTTPException(status_code=404, detail="Review workflow not found")
    
    assignment_id = generate_assignment_id()
    
    assignment = ReviewAssignment(
        assignment_id=assignment_id,
        application_id=application_id,
        reviewer_id=reviewer_id,
        assigned_by=assigned_by,
        due_date=due_date,
        priority=priority,
        status=ReviewStatus.ASSIGNED
    )
    
    assignments[assignment_id] = assignment.dict()
    
    # Update workflow
    review_workflows[application_id]["assignments"].append(assignment.dict())
    review_workflows[application_id]["updated_at"] = datetime.utcnow()
    
    return assignment


@app.get("/assignments/{assignment_id}", response_model=ReviewAssignment)
async def get_assignment(assignment_id: str):
    """Get assignment details"""
    if assignment_id not in assignments:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    return ReviewAssignment(**assignments[assignment_id])


@app.put("/assignments/{assignment_id}/status")
async def update_assignment_status(
    assignment_id: str,
    status: ReviewStatus
):
    """Update assignment status"""
    if assignment_id not in assignments:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    assignments[assignment_id]["status"] = status
    assignments[assignment_id]["updated_at"] = datetime.utcnow()
    
    # Update workflow
    application_id = assignments[assignment_id]["application_id"]
    for assignment in review_workflows[application_id]["assignments"]:
        if assignment["assignment_id"] == assignment_id:
            assignment["status"] = status
            break
    
    return {"message": "Assignment status updated", "status": status}


@app.post("/decisions", response_model=ReviewDecision)
async def submit_decision(
    assignment_id: str,
    decision_type: DecisionType,
    decision_reason: str,
    reviewer_id: str,
    comments: Optional[str] = None,
    confidence_level: Optional[str] = None,
    version_hash: Optional[str] = None
):
    """Submit a review decision"""
    if assignment_id not in assignments:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    assignment = assignments[assignment_id]
    
    # Check for version conflicts
    if version_hash:
        # In production, compare with current application version
        pass
    
    decision_id = generate_decision_id()
    
    decision = ReviewDecision(
        decision_id=decision_id,
        assignment_id=assignment_id,
        application_id=assignment["application_id"],
        reviewer_id=reviewer_id,
        decision_type=decision_type,
        decision_reason=decision_reason,
        comments=comments,
        confidence_level=confidence_level,
        version_hash=version_hash
    )
    
    decisions[decision_id] = decision.dict()
    
    # Update assignment status
    assignments[assignment_id]["status"] = ReviewStatus.COMPLETED
    
    # Update workflow
    application_id = assignment["application_id"]
    review_workflows[application_id]["decisions"].append(decision.dict())
    review_workflows[application_id]["updated_at"] = datetime.utcnow()
    
    # Update overall status if all assignments completed
    all_completed = all(
        a["status"] == ReviewStatus.COMPLETED
        for a in review_workflows[application_id]["assignments"]
    )
    if all_completed:
        review_workflows[application_id]["overall_status"] = ReviewStatus.COMPLETED
    
    return decision


@app.get("/decisions/{decision_id}", response_model=ReviewDecision)
async def get_decision(decision_id: str):
    """Get decision details"""
    if decision_id not in decisions:
        raise HTTPException(status_code=404, detail="Decision not found")
    
    return ReviewDecision(**decisions[decision_id])


@app.post("/conflicts", response_model=ReviewConflict)
async def report_conflict(
    application_id: str,
    conflict_type: str,
    detected_by: str,
    description: str
):
    """Report a review conflict"""
    conflict_id = generate_conflict_id()
    
    conflict = ReviewConflict(
        conflict_id=conflict_id,
        application_id=application_id,
        conflict_type=conflict_type,
        detected_by=detected_by,
        description=description
    )
    
    conflicts[conflict_id] = conflict.dict()
    
    # Update workflow
    if application_id in review_workflows:
        review_workflows[application_id]["conflicts"].append(conflict.dict())
        review_workflows[application_id]["updated_at"] = datetime.utcnow()
    
    return conflict


@app.put("/conflicts/{conflict_id}/resolve")
async def resolve_conflict(
    conflict_id: str,
    resolution_notes: Optional[str] = None
):
    """Resolve a conflict"""
    if conflict_id not in conflicts:
        raise HTTPException(status_code=404, detail="Conflict not found")
    
    conflicts[conflict_id]["resolved"] = True
    conflicts[conflict_id]["resolved_at"] = datetime.utcnow()
    conflicts[conflict_id]["resolution_notes"] = resolution_notes
    
    return {"message": "Conflict resolved", "conflict_id": conflict_id}


@app.get("/applications/{application_id}/assignments")
async def list_application_assignments(application_id: str):
    """List all assignments for an application"""
    if application_id not in review_workflows:
        raise HTTPException(status_code=404, detail="Review workflow not found")
    
    return {
        "application_id": application_id,
        "assignments": review_workflows[application_id]["assignments"],
        "total": len(review_workflows[application_id]["assignments"])
    }


@app.get("/reviewers/{reviewer_id}/assignments")
async def list_reviewer_assignments(
    reviewer_id: str,
    status: Optional[ReviewStatus] = None
):
    """List assignments for a reviewer"""
    reviewer_assignments = [
        assignment for assignment in assignments.values()
        if assignment["reviewer_id"] == reviewer_id
    ]
    
    if status:
        reviewer_assignments = [
            a for a in reviewer_assignments
            if a["status"] == status
        ]
    
    return {
        "reviewer_id": reviewer_id,
        "assignments": reviewer_assignments,
        "total": len(reviewer_assignments)
    }


@app.post("/workflows/{application_id}/finalize")
async def finalize_review_workflow(
    application_id: str,
    final_decision: DecisionType,
    finalized_by: str
):
    """Finalize review workflow with final decision"""
    if application_id not in review_workflows:
        raise HTTPException(status_code=404, detail="Review workflow not found")
    
    workflow = review_workflows[application_id]
    
    if workflow["overall_status"] != ReviewStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Cannot finalize workflow until all reviews are completed"
        )
    
    workflow["final_decision"] = final_decision
    workflow["overall_status"] = ReviewStatus.APPROVED if final_decision == DecisionType.APPROVE else ReviewStatus.REJECTED
    workflow["updated_at"] = datetime.utcnow()
    
    return {
        "application_id": application_id,
        "final_decision": final_decision,
        "finalized_by": finalized_by,
        "finalized_at": workflow["updated_at"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8012)
