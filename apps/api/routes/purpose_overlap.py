"""Purpose-overlap evidence endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from apps.api.dependencies import current_actor
from ml.purpose_overlap.service import compare_purposes
from services.grant_workflow.service import Actor

router = APIRouter(prefix="/api/v1/purpose-overlap", tags=["purpose-overlap"])
ActorDep = Annotated[Actor, Depends(current_actor)]


class PurposeOverlapRequest(BaseModel):
    left_text: str = Field(min_length=40, max_length=100_000)
    right_text: str = Field(min_length=40, max_length=100_000)
    left_label: str = Field(default="Application A", max_length=200)
    right_label: str = Field(default="Application B", max_length=200)


@router.post("/compare")
def compare(request: PurposeOverlapRequest, _: ActorDep) -> dict:
    result = compare_purposes(request.left_text, request.right_text)
    return {
        "left_label": request.left_label,
        "right_label": request.right_label,
        "disposition": result.disposition,
        "confidence": result.confidence,
        "summary": result.summary,
        "method": result.method,
        "dimensions": [
            {
                "dimension": item.dimension,
                "left_text": item.left_text,
                "right_text": item.right_text,
                "similarity": item.similarity,
                "status": item.status,
            }
            for item in result.dimensions
        ],
        "limitations": list(result.limitations),
        "human_review_required": True,
        "disclaimer": "This is purpose-comparison evidence, not a duplication, plagiarism or funding decision.",
    }
