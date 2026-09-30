from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Query

from apps.api.schemas.publications import PublicationRecord
from ml.semantic_matching.embedding import get_runtime_embedder
from ml.semantic_matching.hybrid import rank_candidates
from services.reconciliation.engine import reconcile_publication
from services.research_sources.connectors import search_source
from services.research_sources.registry import list_sources

router = APIRouter(prefix="/api/v1/publications", tags=["publications"])

@router.post("/reconcile")
def reconcile_publication_record(record: PublicationRecord) -> dict:
    return {"record_id": record.record_id, "status": "queued", "message": "Publication accepted for reconciliation."}

@router.post("/reconcile-pair")
def reconcile_pair(left: PublicationRecord, right: PublicationRecord) -> dict:
    result = reconcile_publication(left.record_id, left.title, left.authors[0] if left.authors else "", right.record_id, right.title, right.authors[0] if right.authors else "")
    return {**result, "human_review_required": True}

@router.get("/sources")
def research_sources() -> list[dict]:
    return [asdict(source) for source in list_sources()]

@router.get("/search")
def search_research_sources(q: str = Query(min_length=2), source: str = Query(default="crossref"), limit: int = Query(default=10, ge=1, le=50)) -> dict:
    try:
        records = search_source(source, q, limit)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"query": q, "source": source, "count": len(records), "records": [asdict(record) for record in records], "human_review_required": True}

@router.get("/compare")
def compare_research_sources(q: str = Query(min_length=2), sources: str = Query(default="crossref,doaj,pmc,arxiv"), limit: int = Query(default=5, ge=1, le=20)) -> dict:
    requested = [item.strip() for item in sources.split(",") if item.strip()]
    records = []
    errors = []
    for source in requested:
        try:
            records.extend(search_source(source, q, limit))
        except (RuntimeError, ValueError, OSError) as exc:
            errors.append({"source": source, "error": str(exc)})
    unique = {}
    for record in records:
        key = (record.doi or "").lower() or record.title.strip().lower()
        if key and key not in unique:
            unique[key] = record
    ranked = rank_candidates(q, [(r.record_id, r.searchable_text()) for r in unique.values()], embedder=get_runtime_embedder(), top_k=limit)
    by_id = {record.record_id: record for record in unique.values()}
    return {"query": q, "sources_requested": requested, "sources_with_errors": errors, "count": len(ranked), "records": [{**asdict(by_id[item.candidate_id]), "lexical_similarity": round(item.lexical_score, 4), "semantic_similarity": None if item.semantic_score is None else round(item.semantic_score, 4), "similarity": round(item.fused_score, 4), "rank": item.rank, "method": item.method} for item in ranked], "human_review_required": True, "comparison_note": "Similarity ranks evidence for review; it is not a duplicate, quality, or validity verdict."}
