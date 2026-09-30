import fitz

from ml.evidence.state import AssessmentState, EvidenceRelationship, ReviewStatus, RunState
from services.audit.events import AuditStream
from services.evidence.citations import CitationLocator, validate_citation
from services.human_review.decision import DecisionHistory
from services.screening.pipeline import screen_document
from services.screening.run_state import derive_run_state
from services.sources.health import SourceHealth, SourceHealthRecord
from services.sources.registry import SourceAccessStatus, SourceRecord, SourceRegistry


def test_assessment_and_run_states_are_explicit():
    assert AssessmentState.MET.value == "MET"
    assert AssessmentState.CLARIFICATION_REQUIRED.value == "CLARIFICATION_REQUIRED"
    assert RunState.PARTIAL.value == "PARTIAL"
    assert derive_run_state(requested=3, completed=2, failed=1) == RunState.PARTIAL
    assert derive_run_state(requested=2, completed=0, blocked=2) == RunState.BLOCKED


def test_citation_locator_requires_exact_document_text(tmp_path):
    path = tmp_path / "doc.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Methodology uses annotated maize images.")
    document.save(path)
    document.close()

    from services.ingestion.document import extract_document

    extracted = extract_document(str(path), "DOC-1")
    citation = CitationLocator(
        document_id="DOC-1",
        document_version=1,
        page_number=1,
        start=0,
        end=11,
        evidence="Methodology",
    )
    assert validate_citation(extracted, citation) is True

    invalid = CitationLocator(
        document_id="DOC-1",
        document_version=1,
        page_number=1,
        start=0,
        end=11,
        evidence="Not in document",
    )
    assert validate_citation(extracted, invalid) is False


def test_source_failure_is_not_zero_evidence():
    source = SourceRecord(
        source_id="crossref",
        provider="Crossref",
        source_name="Crossref Works",
        source_type="external",
        access_status=SourceAccessStatus.UNAVAILABLE,
    )
    registry = SourceRegistry([source])
    assert registry.availability("crossref") == SourceAccessStatus.UNAVAILABLE

    health = SourceHealthRecord(
        source_id="crossref",
        status=SourceHealth.UNAVAILABLE,
        last_success=None,
        last_attempt="2026-09-30T06:00:00Z",
    )
    assert health.searchable is False


def test_review_history_is_append_only():
    history = DecisionHistory()
    first = history.record_decision(
        "F-1", "reviewer-1", ReviewStatus.UPHELD, "Evidence supports the finding."
    )
    second = history.record_decision(
        "F-1", "reviewer-1", ReviewStatus.DISMISSED, "New evidence changed the assessment."
    )

    decisions = history.history("F-1")
    assert decisions == (first, second)
    assert decisions[0].decision == ReviewStatus.UPHELD
    assert decisions[1].decision == ReviewStatus.DISMISSED


def test_audit_stream_preserves_history():
    audit = AuditStream()
    audit.append("FINDING_CREATED", "system", "F-1", {"criterion": "C03"})
    audit.append("FINDING_UPHELD", "reviewer-1", "F-1", {"rationale": "confirmed"})

    events = audit.history("F-1")
    assert [event.event_type for event in events] == ["FINDING_CREATED", "FINDING_UPHELD"]


def test_screening_exposes_validated_evidence_chain(tmp_path):
    path = tmp_path / "proposal.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Abstract\nMethodology\nBudget")
    document.save(path)
    document.close()

    result = screen_document(str(path), "TEST-EVIDENCE")

    assert result["run_state"] == RunState.COMPLETE.value
    assert result["evidence_chain"]
    chain = next(item for item in result["evidence_chain"] if item["criterion_id"] == "C03")
    assert chain["status"] == AssessmentState.MET.value
    assert chain["relationship"] == EvidenceRelationship.SUPPORTS.value
    assert chain["page_number"] == 1
    assert chain["evidence_span"] == "Methodology"
    assert chain["review_status"] == "PENDING"
