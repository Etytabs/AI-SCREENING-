from fastapi import APIRouter
from apps.api.schemas.publications import PublicationRecord
from services.reconciliation.engine import reconcile_publication

router = APIRouter(prefix="/api/v1/publications", tags=["publications"])

@router.post("/reconcile")
def reconcile_publication_record(record: PublicationRecord) -> dict:
    return {"record_id": record.record_id, "status": "queued", "message": "Publication accepted for reconciliation."}

@router.post("/reconcile-pair")
def reconcile_pair(left: PublicationRecord, right: PublicationRecord) -> dict:
    result = reconcile_publication(
        left.record_id, left.title, left.authors[0] if left.authors else "",
        right.record_id, right.title, right.authors[0] if right.authors else "",
    )
    return {**result, "human_review_required": True}
