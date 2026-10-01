"""Plagiarism check: how much of the proposal's text already exists elsewhere.

Two independent measures run against every comparison record (other applications, archived
projects and, when configured, published literature retrieved from OpenAlex):

* verbatim overlap — maximal shared word runs (ml.plagiarism.overlap.shared_passages);
* paraphrase overlap — shared content-term phrases (ml.semantic_matching.duplication).

Both are reported as a percentage of *this* proposal, de-duplicated across sources so the
headline similarity index counts each covered word or phrase once. Passages that also occur
in the call's own RFP are excluded, because applicants legitimately quote the call.

A percentage is a text measure, never a verdict: a reviewer confirms whether overlap is
plagiarism, correct quotation, or the applicant's own earlier work.
"""
import os

from ml.evidence.state import EvidenceRelationship
from ml.plagiarism.overlap import shared_passages
from ml.scoring.confidence import calibrate_confidence
from ml.semantic_matching.duplication import compare_proposals, profile_proposal
from services.grant_workflow.models import (
    Finding,
    FindingEvidence,
    FindingStatus,
    FindingType,
    SimilarityMatch,
    new_id,
)
from services.grant_workflow.screening.context import ComparisonRecord, ScreeningContext
from services.grant_workflow.screening.evidence import document_evidence, record_evidence
from services.grant_workflow.screening.similarity import coverage_note
from services.grant_workflow.text_utils import normalize_for_match, shared_concepts

METHOD = "plagiarism_similarity_index_v1"
SHINGLE_SIZE = 8
MIN_PASSAGE_WORDS = 12
MIN_COVERAGE = 0.05
# Reworded overlap needs a far higher bar than verbatim text: two proposals on the same
# topic share content terms without either copying the other.
MIN_PHRASE_COVERAGE = 0.20
MAX_EVIDENCE_PASSAGES = 3
MAX_MATCHES = 10

# Similarity-index bands, reported as percentages of the proposal's own text.
MODERATE_INDEX = 0.15
HIGH_INDEX = 0.35

EXTERNAL_SOURCE_TYPES = {"published_work"}


def band(index: float, verbatim: float) -> str:
    if index >= HIGH_INDEX or verbatim >= MODERATE_INDEX:
        return "HIGH_SIMILARITY"
    if index >= MODERATE_INDEX or verbatim > 0:
        return "MODERATE_SIMILARITY"
    return "LOW_SIMILARITY"


class _RecordResult:
    """Per-record overlap: verbatim passages plus paraphrase-level phrase coverage."""

    def __init__(self, record: ComparisonRecord) -> None:
        self.record = record
        self.passages: list[tuple] = []          # (meta, doc, SharedPassage)
        self.verbatim_words: set[int] = set()    # positions in the combined narrative
        self.phrase_positions: frozenset[int] = frozenset()
        self.phrase_coverage = 0.0
        self.lexical_score = 0.0
        self.query_passage: str | None = None
        self.source_passage: str | None = None

    @property
    def verbatim_count(self) -> int:
        return len(self.verbatim_words)

    @property
    def longest_passage(self) -> int:
        return max((p.word_count for _, _, p in self.passages), default=0)


def _percent(value: float) -> float:
    return round(value * 100, 1)


def _match_explanation(result: _RecordResult, verbatim_share: float) -> str:
    parts = []
    if result.passages:
        parts.append(
            f"{len(result.passages)} verbatim passage(s), longest {result.longest_passage} words, "
            f"covering {verbatim_share:.1%} of this proposal"
        )
    if result.phrase_coverage > 0:
        parts.append(f"{result.phrase_coverage:.1%} of the proposal's content phrases also appear in this source")
    if not parts:
        parts.append("no reportable overlap")
    return "; ".join(parts).capitalize() + "."


def _source_label(record: ComparisonRecord) -> str:
    return record.title or record.record_id


def evaluate_text_similarity(ctx: ScreeningContext, run_id: str) -> list[Finding]:
    finding_id = new_id("finding")
    base = {
        "finding_id": finding_id, "screening_run_id": run_id, "application_id": ctx.application.id,
        "grant_call_id": ctx.grant_call.id, "type": FindingType.PLAGIARISM, "title": "Plagiarism check",
    }
    narrative = ctx.narrative
    external_available = any(r.source_type in EXTERNAL_SOURCE_TYPES for r in ctx.universe)
    details: dict = {
        "compared_records": len(ctx.universe),
        "published_works_compared": sum(1 for r in ctx.universe if r.source_type in EXTERNAL_SOURCE_TYPES),
        "min_passage_words": MIN_PASSAGE_WORDS,
        "min_coverage": MIN_COVERAGE,
        "min_phrase_coverage": MIN_PHRASE_COVERAGE,
        "moderate_index": MODERATE_INDEX,
        "high_index": HIGH_INDEX,
        "published_literature_searched": external_available,
        "source_coverage": [
            {"source_id": item.source_id, "state": item.state.value, "message": item.message}
            for item in ctx.coverage
        ],
        "coverage_complete": not ctx.unavailable_sources,
    }
    if not ctx.universe or not narrative:
        reason = ("No authorized comparison records were available."
                  if not ctx.universe else "No readable narrative text.")
        details["coverage_complete"] = False
        return [Finding(
            **base, status=FindingStatus.REVIEW_REQUIRED, signal="NOT_ASSESSABLE",
            explanation=reason + " Plagiarism could not be assessed; this is not evidence of originality."
                        + coverage_note(ctx),
            recommended_action="Assess manually or connect additional comparison sources.",
            method=METHOD, details=details,
        )]

    rfp_normalized = normalize_for_match(ctx.rfp_text)
    narrative_text = "\n\n".join(doc.text for _, doc in narrative)
    query_profile = profile_proposal(narrative_text)
    # Word offsets let per-document passage positions share one proposal-wide coordinate space.
    offsets, running = {}, 0
    for meta, doc in narrative:
        offsets[meta.id] = running
        running += len(doc.text.split())
    total_words = running or 1

    results: list[_RecordResult] = []
    for record in ctx.universe:
        result = _RecordResult(record)
        for meta, doc in narrative:
            overlap = shared_passages(doc.text, record.text, shingle_size=SHINGLE_SIZE)
            for passage in overlap.passages:
                if rfp_normalized and normalize_for_match(passage.left_text) in rfp_normalized:
                    continue
                result.passages.append((meta, doc, passage))
                result.verbatim_words.update(
                    position + offsets[meta.id] for position in passage.left_word_range
                )
        phrase = compare_proposals(query_profile, profile_proposal(record.text))
        result.phrase_positions = phrase.query_positions
        result.phrase_coverage = phrase.query_coverage
        result.lexical_score = phrase.lexical_score
        result.query_passage, result.source_passage = phrase.query_passage, phrase.source_passage
        results.append(result)

    def reportable(item: _RecordResult) -> bool:
        return bool(item.passages) and (
            item.longest_passage >= MIN_PASSAGE_WORDS or item.verbatim_count / total_words >= MIN_COVERAGE
        )

    flagged = [item for item in results if reportable(item) or item.phrase_coverage >= MIN_PHRASE_COVERAGE]
    flagged.sort(
        key=lambda item: (item.verbatim_count / total_words, item.phrase_coverage),
        reverse=True,
    )

    verbatim_union = set().union(*(item.verbatim_words for item in flagged)) if flagged else set()
    phrase_union = set().union(*(item.phrase_positions for item in flagged)) if flagged else set()
    verbatim_index = len(verbatim_union) / total_words
    phrase_index = len(phrase_union) / len(query_profile.terms) if query_profile.terms else 0.0
    similarity_index = max(verbatim_index, phrase_index)
    details.update(
        similarity_index=_percent(similarity_index),
        verbatim_index=_percent(verbatim_index),
        paraphrase_index=_percent(phrase_index),
        band=band(similarity_index, verbatim_index),
        matched_sources=len(flagged),
        narrative_words=total_words,
    )

    evidence, matches = [], []
    for item in flagged[:MAX_MATCHES]:
        record = item.record
        verbatim_share = item.verbatim_count / total_words
        item.passages.sort(key=lambda entry: entry[2].word_count, reverse=True)
        for meta, doc, passage in item.passages[:MAX_EVIDENCE_PASSAGES]:
            located = document_evidence(
                finding_id, meta, doc, passage.left_text, field="plagiarism",
                status="REVIEW_REQUIRED", relationship=EvidenceRelationship.UNCERTAIN, confidence=0.6,
            )
            if located:
                evidence.append(located)
            evidence.append(record_evidence(finding_id, record, passage.right_text, field="plagiarism"))
        query_passage = item.passages[0][2].left_text if item.passages else item.query_passage
        matched_passage = item.passages[0][2].right_text if item.passages else item.source_passage
        matches.append(SimilarityMatch(
            finding_id=finding_id,
            source_type=record.source_type,
            record_id=record.record_id,
            application_id=record.application_id,
            document_id=record.document_meta.id if record.document_meta else None,
            title=_source_label(record),
            similarity_score=round(max(verbatim_share, item.phrase_coverage), 4),
            lexical_score=round(item.lexical_score, 4),
            query_coverage=round(verbatim_share, 4),
            source_coverage=round(item.phrase_coverage, 4),
            query_passage=query_passage,
            matched_passage=matched_passage,
            matching_concepts=shared_concepts(query_passage or "", matched_passage or ""),
            authors=list(record.authors),
            published_on=record.published_on,
            publisher=record.publisher,
            source_url=record.source_url,
            doi=record.doi,
            year=record.year,
            outcome=record.outcome,
            explanation=_match_explanation(item, verbatim_share),
            method=f"word_shingle_{SHINGLE_SIZE}+content_phrase_overlap",
            data_origin=record.data_origin,
        ))

    if not flagged:
        return [Finding(
            **base, status=FindingStatus.PASS, signal="NO_SHARED_PASSAGES",
            confidence=calibrate_confidence(model_score=0.7, evidence_strength=0.6, agreement=1.0),
            explanation=(
                f"Similarity index 0.0%. No shared passage of {MIN_PASSAGE_WORDS}+ words and no "
                f"reworded content-phrase overlap above {MIN_PHRASE_COVERAGE:.0%} was found across "
                f"{len(ctx.universe)} compared record(s)"
                + (", including published literature from OpenAlex." if external_available
                   else "; published literature was not searched.")
                + " This applies only to the records searched and is not evidence of originality."
                + coverage_note(ctx)
            ),
            recommended_action=(
                "No action required." if external_available
                else "Configure OpenAlex to also compare this proposal against published literature."
            ),
            method=METHOD, details=details,
        )]

    top = flagged[0]
    return [Finding(
        **base, status=FindingStatus.REVIEW_REQUIRED, signal="SHARED_PASSAGES_FOUND",
        confidence=calibrate_confidence(
            model_score=min(1.0, similarity_index * 2), evidence_strength=0.9 if evidence else 0.5, agreement=1.0,
        ),
        explanation=(
            f"Similarity index {similarity_index:.1%} of this proposal's text matches "
            f"{len(flagged)} compared source(s): {verbatim_index:.1%} word-for-word and "
            f"{phrase_index:.1%} as reworded content phrases. Closest source: "
            f"{_source_label(top.record)}"
            + (f" ({top.record.published_on})" if top.record.published_on else "")
            + ". Text quoted from the call document is excluded. A percentage measures text overlap "
              "and is not proof of plagiarism; a reviewer must check attribution and authorship."
            + coverage_note(ctx)
        ),
        recommended_action="Open the matched passages, check whether each is quoted and cited, then confirm or dismiss.",
        method=METHOD, evidence=evidence, matches=matches, details=details,
    )]
