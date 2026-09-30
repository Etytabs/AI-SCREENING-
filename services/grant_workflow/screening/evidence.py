"""Evidence builders.

Application evidence is always an exact span located in the extracted document, checked
with services.evidence.citations.validate_citation and passed through the existing
EvidenceChain invariants before it is exposed as FindingEvidence.
"""
from ml.evidence.state import EvidenceRelationship
from services.evidence.chain import EvidenceChain
from services.grant_workflow.models import ApplicationDocument, FindingEvidence, RfpCriterion
from services.grant_workflow.screening.context import ComparisonRecord
from services.grant_workflow.text_utils import locate_span
from services.ingestion.document import ExtractedDocument


def document_evidence(
    finding_id: str,
    meta: ApplicationDocument,
    document: ExtractedDocument,
    snippet: str,
    *,
    field: str | None = None,
    status: str = "PENDING",
    relationship: EvidenceRelationship = EvidenceRelationship.SUPPORTS,
    confidence: float = 0.0,
) -> FindingEvidence | None:
    span = locate_span(document, snippet, version=meta.version)
    if span is None:
        return None
    chain = EvidenceChain.now(
        finding_id=finding_id,
        criterion_id=field or "",
        status=status,
        relationship=relationship.value,
        confidence=max(0.0, min(1.0, confidence)),
        document_id=meta.id,
        document_version=meta.version,
        page_number=span.page_number,
        chunk_id=None,
        evidence_span=span.text,
        source_id=meta.application_id,
        citation_locator=span.citation_locator,
    )
    return FindingEvidence(
        finding_id=finding_id,
        source_id=chain.source_id,
        source_type="application_document",
        document_id=chain.document_id,
        page=chain.page_number,
        section=span.section,
        text=chain.evidence_span,
        field=field,
        relationship=relationship,
        citation_locator=chain.citation_locator,
        citation_valid=span.citation_valid,
    )


def record_evidence(
    finding_id: str,
    record: ComparisonRecord,
    snippet: str,
    *,
    field: str | None = None,
) -> FindingEvidence:
    if record.document_meta is not None and record.document is not None:
        located = document_evidence(finding_id, record.document_meta, record.document, snippet, field=field)
        if located is not None:
            return located.model_copy(update={"source_type": record.source_type, "source_id": record.record_id})
    return FindingEvidence(
        finding_id=finding_id,
        source_id=record.record_id,
        source_type=record.source_type,
        text=snippet,
        field=field,
        section=record.title,
    )


def rfp_evidence(finding_id: str, criterion: RfpCriterion) -> FindingEvidence:
    return FindingEvidence(
        finding_id=finding_id,
        source_id=criterion.rfp_document_id or "administrator",
        source_type="rfp" if criterion.rfp_document_id else "administrator_requirement",
        document_id=criterion.rfp_document_id,
        page=criterion.source_page,
        section=criterion.source_section,
        text=criterion.requirement_text,
        field=criterion.criterion_code,
        citation_locator=criterion.citation_locator,
        citation_valid=True if criterion.citation_locator else None,
    )


def search_lines(
    documents: list[tuple[ApplicationDocument, ExtractedDocument]],
    predicate,
) -> tuple[ApplicationDocument, ExtractedDocument, str] | None:
    for meta, document in documents:
        for page in document.pages:
            for line in page.lines:
                if predicate(line):
                    return meta, document, line
    return None
