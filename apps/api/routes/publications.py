from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Query

from apps.api.schemas.publications import PublicationRecord
from services.reconciliation.engine import reconcile_publication
from services.research_sources.connectors import search_source
from services.research_sources.registry import list_sources

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


@router.get("/sources")
def research_sources() -> list[dict]:
    return [asdict(source) for source in list_sources()]


@router.get("/search")
def search_research_sources(
    q: str = Query(min_length=2),
    source: str = Query(default="crossref"),
    limit: int = Query(default=10, ge=1, le=50),
) -> dict:
    try:
        records = search_source(source, q, limit)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "query": q,
        "source": source,
        "count": len(records),
        "records": [asdict(record) for record in records],
        "human_review_required": True,
    }
