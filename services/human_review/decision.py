from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass(frozen=True)
class ReviewDecision:
    item_id: str
    reviewer_id: str
    decision: str
    rationale: str
    created_at: datetime

def record_decision(item_id: str, reviewer_id: str, decision: str, rationale: str) -> ReviewDecision:
    return ReviewDecision(item_id, reviewer_id, decision, rationale, datetime.now(timezone.utc))
