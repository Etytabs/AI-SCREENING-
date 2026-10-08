from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import sys
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from shared.models import EligibilityCriteria, EligibilityResult, GrantApplication

app = FastAPI(
    title="Eligibility Service",
    description="Checks grant application eligibility against criteria",
    version="1.0.0"
)


class EligibilityRequest(BaseModel):
    """Request for eligibility check"""
    application: Dict[str, Any]
    criteria: Optional[Dict[str, Any]] = None


def check_eligibility(application: Dict[str, Any], criteria: Optional[Dict[str, Any]] = None) -> EligibilityResult:
    """Perform eligibility check on application"""
    
    # Default criteria if none provided
    if criteria is None:
        criteria = {
            "institution_type": None,
            "min_researchers": 1,
            "max_budget": 1000000,
            "required_fields": ["title", "abstract", "author_name", "institution", "email", "budget_amount"],
            "excluded_institutions": [],
            "required_certifications": []
        }
    
    eligibility_criteria = EligibilityCriteria(**criteria)
    
    missing_requirements = []
    satisfied_requirements = []
    disqualification_reasons = []
    
    # Check required fields
    for field in eligibility_criteria.required_fields:
        field_value = application.get(field)
        if field_value is None or (isinstance(field_value, str) and not field_value.strip()):
            missing_requirements.append(f"Missing required field: {field}")
        else:
            satisfied_requirements.append(f"Field {field} is present")
    
    # Check institution type
    if eligibility_criteria.institution_type:
        app_institution = application.get("institution", "").lower()
        if eligibility_criteria.institution_type.lower() not in app_institution:
            disqualification_reasons.append(
                f"Institution type mismatch. Expected: {eligibility_criteria.institution_type}"
            )
        else:
            satisfied_requirements.append("Institution type matches criteria")
    
    # Check minimum researchers
    if eligibility_criteria.min_researchers:
        team_members = application.get("team_members", [])
        if len(team_members) < eligibility_criteria.min_researchers:
            disqualification_reasons.append(
                f"Insufficient team members. Required: {eligibility_criteria.min_researchers}, Found: {len(team_members)}"
            )
        else:
            satisfied_requirements.append(f"Team size meets minimum ({eligibility_criteria.min_researchers})")
    
    # Check maximum budget
    if eligibility_criteria.max_budget:
        budget = application.get("budget_amount", 0)
        if budget > eligibility_criteria.max_budget:
            disqualification_reasons.append(
                f"Budget exceeds maximum. Allowed: {eligibility_criteria.max_budget}, Requested: {budget}"
            )
        else:
            satisfied_requirements.append(f"Budget within limit ({eligibility_criteria.max_budget})")
    
    # Check excluded institutions
    if eligibility_criteria.excluded_institutions:
        app_institution = application.get("institution", "").lower()
        for excluded in eligibility_criteria.excluded_institutions:
            if excluded.lower() in app_institution:
                disqualification_reasons.append(f"Institution is excluded: {excluded}")
                break
    
    # Check email format
    email = application.get("email", "")
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        missing_requirements.append("Invalid email format")
    else:
        satisfied_requirements.append("Valid email format")
    
    # Check phone format if provided
    phone = application.get("phone")
    if phone and not re.match(r'^\+?[\d\s-]{10,}$', phone):
        missing_requirements.append("Invalid phone format")
    elif phone:
        satisfied_requirements.append("Valid phone format")
    
    # Determine eligibility
    is_eligible = (
        len(missing_requirements) == 0 and
        len(disqualification_reasons) == 0
    )
    
    # Calculate eligibility score
    total_checks = (
        len(eligibility_criteria.required_fields) +
        (1 if eligibility_criteria.institution_type else 0) +
        (1 if eligibility_criteria.min_researchers else 0) +
        (1 if eligibility_criteria.max_budget else 0) +
        (1 if eligibility_criteria.excluded_institutions else 0)
    )
    passed_checks = len(satisfied_requirements)
    score = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
    
    return EligibilityResult(
        service_name="eligibility",
        status="completed",
        score=score,
        details={
            "criteria_applied": criteria,
            "total_checks": total_checks,
            "passed_checks": passed_checks
        },
        is_eligible=is_eligible,
        missing_requirements=missing_requirements,
        satisfied_requirements=satisfied_requirements,
        disqualification_reasons=disqualification_reasons,
        timestamp=datetime.utcnow()
    )


@app.get("/")
async def root():
    return {
        "service": "Eligibility Service",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/check", response_model=EligibilityResult)
async def check_application_eligibility(request: EligibilityRequest):
    """Check eligibility of a grant application"""
    try:
        result = check_eligibility(request.application, request.criteria)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/validate-criteria")
async def validate_criteria(criteria: EligibilityCriteria):
    """Validate eligibility criteria configuration"""
    errors = []
    
    if criteria.min_researchers and criteria.min_researchers < 1:
        errors.append("min_researchers must be at least 1")
    
    if criteria.max_budget and criteria.max_budget < 0:
        errors.append("max_budget cannot be negative")
    
    if criteria.max_budget and criteria.min_researchers:
        # No validation conflict between these
        pass
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
