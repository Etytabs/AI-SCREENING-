from pydantic import BaseModel, Field

class GrantProposal(BaseModel):
    proposal_id: str
    title: str = Field(min_length=1)
    abstract: str = ""
    full_text: str = ""

class EligibilityResult(BaseModel):
    criterion: str
    passed: bool
    evidence: str
    confidence: float = Field(ge=0.0, le=1.0)
