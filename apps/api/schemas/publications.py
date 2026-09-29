from pydantic import BaseModel, Field

class PublicationRecord(BaseModel):
    record_id: str
    title: str = Field(min_length=1)
    authors: list[str] = []
    doi: str | None = None
    year: int | None = None
    source: str

class ReconciliationResult(BaseModel):
    left_record_id: str
    right_record_id: str
    similarity: float = Field(ge=0.0, le=1.0)
    decision: str
    evidence: list[str] = []
