from dataclasses import dataclass

@dataclass(frozen=True)
class Evidence:
    source_id: str
    field: str
    value: str
    rationale: str

@dataclass(frozen=True)
class ModelExplanation:
    decision: str
    confidence: float
    evidence: tuple[Evidence, ...]
