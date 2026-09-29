from fastapi import APIRouter
from apps.api.schemas.publications import PublicationRecord

router = APIRouter(prefix="/api/v1/publications", tags=["publications"])

@router.post("/reconcile")
def reconcile_publication(record: PublicationRecord) -> dict:
    return {
        "record_id": record.record_id,
        "status": "queued",
        "message": "Publication accepted for reconciliation.",
    }
