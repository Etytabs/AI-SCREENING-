from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from apps.api.schemas.grants import GrantProposal
from services.screening.pipeline import screen_document

router = APIRouter(prefix="/api/v1/grants", tags=["grants"])

@router.post("/screen")
def screen_proposal(proposal: GrantProposal) -> dict:
    return {"proposal_id": proposal.proposal_id, "status": "queued", "message": "Proposal accepted for AI-assisted screening."}

@router.post("/screen-document")
async def screen_document_upload(
    file: UploadFile = File(...),
    proposal_id: str = Form("demo-proposal"),
) -> dict:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".docx"}:
        raise HTTPException(status_code=415, detail="Only PDF and DOCX proposals are supported.")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded document is empty.")
    with NamedTemporaryFile(suffix=suffix) as tmp:
        tmp.write(data)
        tmp.flush()
        return screen_document(tmp.name, proposal_id)
