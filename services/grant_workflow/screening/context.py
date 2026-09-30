from dataclasses import dataclass, field

from ml.semantic_matching.hybrid import TextEmbedder
from ml.semantic_matching.reranker import CrossEncoderReranker
from services.evidence.coverage import SourceCoverage
from services.grant_workflow.documents import ApplicationMetadata
from services.grant_workflow.models import (
    Applicant,
    Application,
    ApplicationDocument,
    DataOrigin,
    GrantCall,
    Institution,
    RfpCriterion,
)
from services.ingestion.document import ExtractedDocument


@dataclass(frozen=True)
class ComparisonRecord:
    record_id: str
    source_type: str
    title: str | None
    text: str
    data_origin: DataOrigin
    application_id: str | None = None
    document_meta: ApplicationDocument | None = None
    document: ExtractedDocument | None = None
    year: int | None = None
    outcome: str | None = None


@dataclass
class ScreeningContext:
    grant_call: GrantCall
    application: Application
    applicant: Applicant | None
    institution: Institution | None
    documents: list[tuple[ApplicationDocument, ExtractedDocument | None]]
    criteria: list[RfpCriterion]
    rfp_text: str
    universe: list[ComparisonRecord]
    coverage: list[SourceCoverage]
    metadata: ApplicationMetadata
    embedder: TextEmbedder | None = None
    reranker: CrossEncoderReranker | None = None
    requirement_map: dict[str, int] = field(default_factory=dict)

    @property
    def readable(self) -> list[tuple[ApplicationDocument, ExtractedDocument]]:
        return [
            (meta, doc) for meta, doc in self.documents
            if doc is not None and doc.extraction_status == "success" and doc.text.strip()
        ]

    @property
    def narrative(self) -> list[tuple[ApplicationDocument, ExtractedDocument]]:
        proposals = [(meta, doc) for meta, doc in self.readable if meta.document_type == "proposal"]
        return proposals or self.readable

    @property
    def narrative_text(self) -> str:
        return "\n\n".join(doc.text for _, doc in self.narrative)

    @property
    def unavailable_sources(self) -> list[SourceCoverage]:
        return [item for item in self.coverage if item.state.value != "COMPLETE"]
