from fastapi import APIRouter
from apps.api.schemas.grants import GrantProposal

router = APIRouter(prefix="/api/v1/grants", tags=["grants"])

@router.post("/screen")
def screen_proposal(proposal: GrantProposal) -> dict:
    # ML services are intentionally separated from the API layer.
    return {
        "proposal_id": proposal.proposal_id,
        "status": "queued",
        "message": "Proposal accepted for AI-assisted screening.",
    }
