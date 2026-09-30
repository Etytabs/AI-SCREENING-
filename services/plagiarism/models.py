from dataclasses import dataclass, field


@dataclass(frozen=True)
class SourceAttribution:
    title: str = ""
    authors: tuple[str, ...] = ()
    publisher: str | None = None
    published_date: str | None = None
    source_url: str = ""
    rights_holder: str | None = None
    attribution_basis: str = "search metadata"
    metadata_confidence: float = 0.0


@dataclass(frozen=True)
class SourceCandidate:
    source_id: str
    title: str
    url: str
    snippet: str = ""
    search_query: str = ""
    attribution: SourceAttribution = field(default_factory=SourceAttribution)


@dataclass(frozen=True)
class PlagiarismEvidence:
    finding_id: str
    status: str
    match_type: str
    similarity: float
    applicant_passage: str
    source_passage: str
    source: SourceCandidate
    explanation: str
    confidence: float
    human_review_required: bool = True
