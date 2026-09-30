"""Novelty signal stage wrapping ml.novelty.engine.assess_novelty. Never produces FAIL."""
from ml.evidence.state import EvidenceRelationship
from ml.novelty import engine
from services.grant_workflow.models import (
    Finding,
    FindingStatus,
    FindingType,
    SimilarityMatch,
    new_id,
)
from services.grant_workflow.screening.context import ScreeningContext
from services.grant_workflow.screening.evidence import document_evidence, record_evidence
from services.grant_workflow.screening.similarity import coverage_note
from services.grant_workflow.text_utils import split_sentences

SIGNAL_LABELS = {
    engine.HIGH: "HIGH",
    engine.MEDIUM: "MEDIUM",
    engine.LOW: "LOW",
    engine.REVIEW_REQUIRED: "REVIEW_REQUIRED",
}


def evaluate_novelty(ctx: ScreeningContext, run_id: str) -> list[Finding]:
    finding_id = new_id("finding")
    records = {r.record_id: r for r in ctx.universe}
    assessment = engine.assess_novelty(
        ctx.narrative_text, [(r.record_id, r.text) for r in ctx.universe], embedder=ctx.embedder,
    )
    signal = SIGNAL_LABELS[assessment.signal]
    status = FindingStatus.PASS if signal in {"HIGH", "MEDIUM"} else FindingStatus.REVIEW_REQUIRED

    evidence, matches = [], []
    for dimension in assessment.dimensions:
        first = next(iter(split_sentences(dimension.statement)), dimension.statement)
        for meta, doc in ctx.narrative:
            item = document_evidence(finding_id, meta, doc, first, field=f"novelty:{dimension.dimension}",
                                     status=status.value, relationship=EvidenceRelationship.UNCERTAIN, confidence=0.5)
            if item:
                evidence.append(item)
                break
        record = records.get(dimension.closest_source_id or "")
        if record is None or dimension.max_similarity is None:
            continue
        closest = next(iter(split_sentences(dimension.closest_statement or "")), dimension.closest_statement or "")
        if dimension.signal == engine.LOW:
            evidence.append(record_evidence(finding_id, record, closest, field=f"novelty:{dimension.dimension}"))
        matches.append(SimilarityMatch(
            finding_id=finding_id,
            source_type=record.source_type,
            record_id=record.record_id,
            application_id=record.application_id,
            title=record.title,
            similarity_score=dimension.max_similarity,
            matched_section=dimension.dimension,
            matched_passage=closest,
            explanation=f"{dimension.dimension.replace('_', ' ')}: closest similarity {dimension.max_similarity:.2f} "
                        f"({SIGNAL_LABELS[dimension.signal]} novelty signal).",
            method=assessment.method,
            data_origin=record.data_origin,
        ))

    actions = {
        "HIGH": "Reviewer to judge scientific novelty; the signal only reflects the compared records.",
        "MEDIUM": "Reviewer to judge scientific novelty against the closest records.",
        "LOW": "Inspect the closest records per dimension before any judgement.",
        "REVIEW_REQUIRED": "Assess novelty manually; the automated signal could not be computed.",
    }
    return [Finding(
        finding_id=finding_id, screening_run_id=run_id, application_id=ctx.application.id,
        grant_call_id=ctx.grant_call.id, type=FindingType.NOVELTY, status=status, signal=signal,
        title="Novelty signal", confidence=assessment.confidence,
        explanation=assessment.explanation + coverage_note(ctx), recommended_action=actions[signal],
        method=assessment.method, evidence=evidence, matches=matches,
        details={
            "compared_records": assessment.compared_sources,
            "dimensions": [
                {"dimension": d.dimension, "max_similarity": d.max_similarity, "signal": SIGNAL_LABELS[d.signal],
                 "closest_source_id": d.closest_source_id}
                for d in assessment.dimensions
            ],
        },
    )]
