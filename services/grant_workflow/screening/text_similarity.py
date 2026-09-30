"""Text-similarity signal: shared verbatim passages via ml.plagiarism.overlap.shared_passages.

Passages that also occur in the call's RFP are excluded (applicants legitimately quote
the call). The result is a signal for reviewer inspection, never a plagiarism finding.
"""
import os

from ml.evidence.state import EvidenceRelationship
from ml.plagiarism.overlap import shared_passages
from ml.scoring.confidence import calibrate_confidence
from services.grant_workflow.models import (
    Finding,
    FindingEvidence,
    FindingStatus,
    FindingType,
    SimilarityMatch,
    new_id,
)
from services.grant_workflow.screening.context import ScreeningContext
from services.grant_workflow.screening.evidence import document_evidence, record_evidence
from services.grant_workflow.screening.similarity import coverage_note
from services.grant_workflow.text_utils import normalize_for_match
from services.plagiarism.service import check_public_sources

METHOD = "shared_passage_overlap_v0.1"
SHINGLE_SIZE = 8
MIN_PASSAGE_WORDS = 12
MIN_COVERAGE = 0.05
MAX_EVIDENCE_PASSAGES = 3


def evaluate_text_similarity(ctx: ScreeningContext, run_id: str) -> list[Finding]:
    finding_id = new_id("finding")
    base = {
        "finding_id": finding_id, "screening_run_id": run_id, "application_id": ctx.application.id,
        "grant_call_id": ctx.grant_call.id, "type": FindingType.PLAGIARISM, "title": "Text similarity",
    }
    narrative = ctx.narrative
    if not ctx.universe or not narrative:
        reason = "No authorized comparison records were available." if not ctx.universe else "No readable narrative text."
        return [Finding(
            **base, status=FindingStatus.REVIEW_REQUIRED, signal="NOT_ASSESSABLE",
            explanation=reason + " Text similarity could not be assessed." + coverage_note(ctx),
            recommended_action="Assess manually or connect additional comparison sources.", method=METHOD,
        )]

    rfp_normalized = normalize_for_match(ctx.rfp_text)
    total_words = sum(len(doc.text.split()) for _, doc in narrative) or 1
    evidence, matches, flagged_records = [], [], 0
    highest_coverage = 0.0
    for record in ctx.universe:
        kept = []
        for meta, doc in narrative:
            overlap = shared_passages(doc.text, record.text, shingle_size=SHINGLE_SIZE)
            for passage in overlap.passages:
                if rfp_normalized and normalize_for_match(passage.left_text) in rfp_normalized:
                    continue
                kept.append((meta, doc, passage))
        if not kept:
            continue
        coverage = sum(p.word_count for _, _, p in kept) / total_words
        longest = max(p.word_count for _, _, p in kept)
        highest_coverage = max(highest_coverage, coverage)
        if longest < MIN_PASSAGE_WORDS and coverage < MIN_COVERAGE:
            continue
        flagged_records += 1
        kept.sort(key=lambda item: item[2].word_count, reverse=True)
        for meta, doc, passage in kept[:MAX_EVIDENCE_PASSAGES]:
            item = document_evidence(finding_id, meta, doc, passage.left_text, field="text_similarity",
                                     status="REVIEW_REQUIRED", relationship=EvidenceRelationship.UNCERTAIN, confidence=0.6)
            if item:
                evidence.append(item)
            evidence.append(record_evidence(finding_id, record, passage.right_text, field="text_similarity"))
        top = kept[0][2]
        matches.append(SimilarityMatch(
            finding_id=finding_id,
            source_type=record.source_type,
            record_id=record.record_id,
            application_id=record.application_id,
            document_id=record.document_meta.id if record.document_meta else None,
            title=record.title,
            similarity_score=round(coverage, 4),
            lexical_score=round(coverage, 4),
            matched_passage=top.right_text,
            explanation=(
                f"{len(kept)} shared passage(s); longest {longest} words; {coverage:.1%} of the application's narrative "
                f"text. {'Exact' if top.exact else 'Normalized'} match (case and punctuation ignored)."
            ),
            method=f"word_shingle_{SHINGLE_SIZE}",
            data_origin=record.data_origin,
        ))

    public_sources = []
    public_source_status = "disabled"
    if os.getenv("AI_SCREENING_PUBLIC_SOURCE_CHECK_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}:
        if os.getenv("GEMINI_API_KEY"):
            try:
                public_sources = [item for _, doc in narrative for item in check_public_sources(doc.text, limit=5)]
                public_source_status = "completed"
                for item in public_sources:
                    evidence.append(FindingEvidence(
                        finding_id=finding_id,
                        source_id=item.source.url,
                        source_type="external_web",
                        text=item.source_passage,
                        field="public_source_similarity",
                        section=item.source.attribution.title or item.source.title,
                        relationship=EvidenceRelationship.UNCERTAIN,
                    ))
            except (RuntimeError, ValueError, OSError):
                public_source_status = "failed"
        else:
            public_source_status = "not_configured"

    if matches:
        matches.sort(key=lambda m: m.similarity_score, reverse=True)
        top = matches[0]
        return [Finding(
            **base, status=FindingStatus.REVIEW_REQUIRED, signal="SHARED_PASSAGES_FOUND",
            confidence=calibrate_confidence(model_score=0.7, evidence_strength=0.9 if evidence else 0.4, agreement=1.0),
            explanation=(
                f"Shared passages found with {flagged_records} record(s); highest coverage {top.similarity_score:.1%} "
                f"with {top.title or top.record_id}. Passages quoted from the call document are excluded. "
                "Shared text is a signal for review, not proof of plagiarism; attribution and authorship must be checked."
                + coverage_note(ctx)
            ),
            recommended_action="Inspect each shared passage and its source before confirming or dismissing.",
            method=METHOD, evidence=evidence, matches=matches,
            details={
                "compared_records": len(ctx.universe),
                "min_passage_words": MIN_PASSAGE_WORDS,
                "min_coverage": MIN_COVERAGE,
                "public_source_similarity": {
                    "status": public_source_status,
                    "findings": [
                        {
                            "finding_id": item.finding_id,
                            "similarity": item.similarity,
                            "match_type": item.match_type,
                            "applicant_passage": item.applicant_passage,
                            "source_passage": item.source_passage,
                            "source": {
                                "title": item.source.attribution.title or item.source.title,
                                "url": item.source.url,
                                "authors": list(item.source.attribution.authors),
                                "publisher": item.source.attribution.publisher,
                                "published_date": item.source.attribution.published_date,
                                "metadata_confidence": item.source.attribution.metadata_confidence,
                            },
                        }
                        for item in public_sources
                    ],
                    "human_review_required": True,
                },
            },
        )]
    return [Finding(
        **base, status=FindingStatus.PASS, signal="NO_SHARED_PASSAGES",
        confidence=calibrate_confidence(model_score=0.7, evidence_strength=0.6, agreement=1.0),
        explanation=(
            f"No shared passage of {MIN_PASSAGE_WORDS}+ words (or {MIN_COVERAGE:.0%} coverage) found across "
            f"{len(ctx.universe)} compared records; highest coverage {highest_coverage:.1%}." + coverage_note(ctx)
        ),
        recommended_action="No action required.", method=METHOD,
        details={"compared_records": len(ctx.universe)},
    )]
