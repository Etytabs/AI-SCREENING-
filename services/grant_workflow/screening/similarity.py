"""Duplication signal: whole-proposal similarity against the authorized comparison universe.

Uses ml.semantic_matching.hybrid.rank_candidates (lexical, or hybrid when an embedder is
configured) and the optional cross-encoder reranker. The output is a signal for reviewer
inspection; it never declares duplication.
"""
from ml.evidence.state import EvidenceRelationship
from ml.scoring.confidence import calibrate_confidence
from ml.semantic_matching.hybrid import rank_candidates
from ml.semantic_matching.reranker import rerank_candidates
from ml.semantic_matching.service import compare_texts
from services.evidence.coverage import source_failure_message
from services.grant_workflow.models import (
    Finding,
    FindingStatus,
    FindingType,
    SimilarityMatch,
    new_id,
)
from services.grant_workflow.screening.context import ComparisonRecord, ScreeningContext
from services.grant_workflow.screening.evidence import document_evidence, record_evidence
from services.grant_workflow.text_utils import shared_concepts, split_sentences

METHOD = "whole_proposal_similarity_v0.1"
THRESHOLDS = {"lexical": 0.3, "hybrid": 0.75}
TOP_K = 5
MAX_SENTENCES = 250


def _sentences(text: str) -> list[str]:
    return [s for s in split_sentences(" ".join(text.split())) if len(s.split()) >= 6][:MAX_SENTENCES]


def best_sentence_pair(left: str, right: str) -> tuple[str, str, float] | None:
    best: tuple[str, str, float] | None = None
    right_sentences = _sentences(right)
    for sentence in _sentences(left):
        for other in right_sentences:
            score = compare_texts(sentence, other).score
            if best is None or score > best[2]:
                best = (sentence, other, score)
    return best


def _locate_application_sentence(ctx: ScreeningContext, finding_id: str, sentence: str, status: str):
    for meta, doc in ctx.narrative:
        item = document_evidence(finding_id, meta, doc, sentence, field="duplication", status=status,
                                 relationship=EvidenceRelationship.UNCERTAIN, confidence=0.5)
        if item:
            return item
    return None


def coverage_note(ctx: ScreeningContext) -> str:
    missing = ctx.unavailable_sources
    if not missing:
        return ""
    return " " + " ".join(source_failure_message(item.source_id) for item in missing)


def evaluate_duplication(ctx: ScreeningContext, run_id: str) -> list[Finding]:
    finding_id = new_id("finding")
    query = ctx.narrative_text
    base = {
        "finding_id": finding_id, "screening_run_id": run_id, "application_id": ctx.application.id,
        "grant_call_id": ctx.grant_call.id, "type": FindingType.DUPLICATION, "title": "Possible duplication",
    }
    if not ctx.universe or not query.strip():
        reason = "No authorized comparison records were available." if not ctx.universe else "No readable narrative text."
        return [Finding(
            **base, status=FindingStatus.REVIEW_REQUIRED, signal="NOT_ASSESSABLE",
            explanation=reason + " Duplication could not be assessed; this is not evidence of originality." + coverage_note(ctx),
            recommended_action="Assess manually or connect additional comparison sources.",
            method=METHOD, details={"compared_records": len(ctx.universe)},
        )]

    records: dict[str, ComparisonRecord] = {r.record_id: r for r in ctx.universe}
    ranked = rank_candidates(query, [(r.record_id, r.text) for r in ctx.universe], embedder=ctx.embedder, top_k=TOP_K)
    method_key = "hybrid" if ctx.embedder is not None else "lexical"
    threshold = THRESHOLDS[method_key]
    reranked = {}
    if ctx.reranker is not None and ranked:
        reranked = {
            item.candidate_id: item.reranker_score
            for item in rerank_candidates(
                query, [(c.candidate_id, records[c.candidate_id].text, c.fused_score) for c in ranked],
                reranker=ctx.reranker, top_k=len(ranked),
            )
        }

    flagged = [c for c in ranked if c.fused_score >= threshold]
    shown = flagged or ranked[:1]
    evidence, matches = [], []
    for candidate in shown:
        record = records[candidate.candidate_id]
        pair = best_sentence_pair(query, record.text)
        is_flagged = candidate in flagged
        if pair and is_flagged:
            app_item = _locate_application_sentence(ctx, finding_id, pair[0], "REVIEW_REQUIRED")
            if app_item:
                evidence.append(app_item)
            evidence.append(record_evidence(finding_id, record, pair[1], field="duplication"))
        concepts = shared_concepts(query, record.text)
        matches.append(SimilarityMatch(
            finding_id=finding_id,
            source_type=record.source_type,
            record_id=record.record_id,
            application_id=record.application_id,
            document_id=record.document_meta.id if record.document_meta else None,
            title=record.title,
            similarity_score=round(candidate.fused_score, 4),
            lexical_score=round(candidate.lexical_score, 4),
            semantic_score=None if candidate.semantic_score is None else round(candidate.semantic_score, 4),
            reranker_score=reranked.get(candidate.candidate_id),
            matched_passage=pair[1] if pair else None,
            matching_concepts=concepts,
            explanation=(
                f"Similarity {candidate.fused_score:.2f} ({candidate.method}); threshold {threshold:.2f}. "
                + ("Shared concepts: " + ", ".join(concepts) + "." if concepts else "No shared multi-word concepts.")
            ),
            method=candidate.method,
            data_origin=record.data_origin,
        ))

    if flagged:
        top = flagged[0]
        status = FindingStatus.REVIEW_REQUIRED
        signal = "POSSIBLE_DUPLICATION"
        explanation = (
            f"{len(flagged)} of {len(ctx.universe)} compared records exceed the {method_key} similarity threshold "
            f"({threshold:.2f}); highest {top.fused_score:.2f} with {records[top.candidate_id].title or top.candidate_id}. "
            "Similarity is a signal only; it does not establish duplication."
        )
        action = "Compare the matched passages side by side and confirm or dismiss."
        confidence = calibrate_confidence(model_score=min(1.0, top.fused_score), evidence_strength=0.8 if evidence else 0.4, agreement=1.0)
    else:
        status = FindingStatus.PASS
        signal = "NO_SIGNIFICANT_SIMILARITY"
        best = ranked[0].fused_score if ranked else 0.0
        explanation = (
            f"No record among {len(ctx.universe)} compared exceeds the {method_key} threshold ({threshold:.2f}); "
            f"highest similarity {best:.2f}."
        )
        action = "No action required unless reviewer knowledge suggests otherwise."
        confidence = calibrate_confidence(model_score=0.6, evidence_strength=0.6, agreement=1.0)

    return [Finding(
        **base, status=status, signal=signal, confidence=confidence,
        explanation=explanation + coverage_note(ctx), recommended_action=action,
        method=f"{METHOD}:{method_key}", evidence=evidence, matches=matches,
        details={"compared_records": len(ctx.universe), "threshold": threshold, "flagged": len(flagged)},
    )]
