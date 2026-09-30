from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class EvidenceChain:
    finding_id: str
    criterion_id: str
    status: str
    relationship: str
    confidence: float
    document_id: str
    document_version: int
    page_number: int | None
    chunk_id: str | None
    evidence_span: str
    source_id: str
    retrieved_at: datetime
    citation_locator: str
    review_status: str = "PENDING"

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.document_version < 1:
            raise ValueError("document_version must be positive")
        if not self.evidence_span.strip():
            raise ValueError("evidence_span must not be empty")
        if not self.citation_locator.strip():
            raise ValueError("citation_locator must not be empty")

    @classmethod
    def now(
        cls,
        *,
        finding_id: str,
        criterion_id: str,
        status: str,
        relationship: str,
        confidence: float,
        document_id: str,
        document_version: int,
        page_number: int | None,
        chunk_id: str | None,
        evidence_span: str,
        source_id: str,
        citation_locator: str,
        review_status: str = "PENDING",
    ) -> "EvidenceChain":
        return cls(
            finding_id=finding_id,
            criterion_id=criterion_id,
            status=status,
            relationship=relationship,
            confidence=confidence,
            document_id=document_id,
            document_version=document_version,
            page_number=page_number,
            chunk_id=chunk_id,
            evidence_span=evidence_span,
            source_id=source_id,
            retrieved_at=datetime.now(UTC),
            citation_locator=citation_locator,
            review_status=review_status,
        )
