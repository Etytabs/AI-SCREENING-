from dataclasses import dataclass
from datetime import UTC, datetime

from ml.evidence.state import ReviewStatus


@dataclass(frozen=True)
class ReviewDecision:
    item_id: str
    reviewer_id: str
    decision: ReviewStatus
    rationale: str
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.rationale.strip():
            raise ValueError("rationale is required")


@dataclass(frozen=True)
class ClarificationRequest:
    item_id: str
    reviewer_id: str
    question: str
    recipient: str
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.question.strip():
            raise ValueError("question is required")
        if not self.recipient.strip():
            raise ValueError("recipient is required")


class DecisionHistory:
    def __init__(self) -> None:
        self._decisions: list[ReviewDecision | ClarificationRequest] = []

    def record_decision(
        self,
        item_id: str,
        reviewer_id: str,
        decision: ReviewStatus,
        rationale: str,
    ) -> ReviewDecision:
        if decision not in {ReviewStatus.UPHELD, ReviewStatus.DISMISSED}:
            raise ValueError("decision must be UPHELD or DISMISSED")
        entry = ReviewDecision(
            item_id=item_id,
            reviewer_id=reviewer_id,
            decision=decision,
            rationale=rationale,
            created_at=datetime.now(UTC),
        )
        self._decisions.append(entry)
        return entry

    def request_clarification(
        self,
        item_id: str,
        reviewer_id: str,
        question: str,
        recipient: str,
    ) -> ClarificationRequest:
        entry = ClarificationRequest(
            item_id=item_id,
            reviewer_id=reviewer_id,
            question=question,
            recipient=recipient,
            created_at=datetime.now(UTC),
        )
        self._decisions.append(entry)
        return entry

    def history(self, item_id: str) -> tuple[ReviewDecision | ClarificationRequest, ...]:
        return tuple(entry for entry in self._decisions if entry.item_id == item_id)


def record_decision(
    item_id: str,
    reviewer_id: str,
    decision: ReviewStatus,
    rationale: str,
) -> ReviewDecision:
    return DecisionHistory().record_decision(item_id, reviewer_id, decision, rationale)
