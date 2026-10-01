"""Duplication review signals against authorized applications and project archives."""
import math
from dataclasses import dataclass

from ml.evidence.state import EvidenceRelationship
from ml.scoring.confidence import calibrate_confidence
from ml.semantic_matching.duplication import (
    EXACT,
    NONE,
    POSSIBLE,
    SEVERITY,
    DuplicationScore,
    compare_proposals,
    profile_proposal,
)
from ml.semantic_matching.embedding import cosine_similarity
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
from services.grant_workflow.text_utils import shared_concepts

METHOD = "proposal_duplication_v1"
TOP_K = 5


def _document_text(document) -> str:
    # Preserve extraction lines for excluding form fields; passages retain their spelling.
    return "\n\n".join("\n".join(page.lines) if page.lines else page.text for page in document.pages) or document.text


def best_sentence_pair(left: str, right: str) -> tuple[str, str, float] | None:
    result = compare_proposals(profile_proposal(left), profile_proposal(right))
    if result.query_passage and result.source_passage:
        return result.query_passage, result.source_passage, result.score
    return None


def _locate_application_sentence(documents, finding_id: str, sentence: str):
    for meta, doc in documents:
        item = document_evidence(
            finding_id, meta, doc, sentence, field="duplication", status="REVIEW_REQUIRED",
            relationship=EvidenceRelationship.UNCERTAIN, confidence=0.5,
        )
        if item:
            return item
    return None


def coverage_note(ctx: ScreeningContext) -> str:
    if not ctx.unavailable_sources:
        return ""
    return " " + " ".join(source_failure_message(item.source_id) for item in ctx.unavailable_sources)


@dataclass
class _Candidate:
    record: ComparisonRecord
    overlap: DuplicationScore
    match_type: str
    score: float
    semantic_score: float | None = None
    reranker_score: float | None = None


def _optional_models(ctx: ScreeningContext, candidates: list[_Candidate], limitations: list[str]) -> str:
    method = "normalized_content_and_passage_overlap"
    if ctx.embedder is None:
        limitations.append("Semantic embeddings are disabled; extensive paraphrases without shared wording may be missed.")
    else:
        try:
            passages = list(dict.fromkeys(
                passage for item in candidates
                for passage in (item.overlap.query_passage, item.overlap.source_passage) if passage
            ))
            vectors = ctx.embedder.encode(passages)
            if len(vectors) != len(passages):
                raise ValueError("Embedding output count mismatch")
            by_passage = dict(zip(passages, vectors))
            scores = []
            for item in candidates:
                left, right = item.overlap.query_passage, item.overlap.source_passage
                score = cosine_similarity(by_passage[left], by_passage[right]) if left and right else 0.0
                if not math.isfinite(score):
                    raise ValueError("Non-finite embedding score")
                scores.append(max(0.0, min(1.0, score)))
            for item, score in zip(candidates, scores):
                item.semantic_score = score
                # Semantic topic similarity alone does not establish project duplication.
                if item.match_type == NONE and score >= 0.88 and item.overlap.shared_terms >= 8 and item.overlap.lexical_score >= 0.35:
                    item.match_type = POSSIBLE
                    item.score = max(item.score, 0.35 * item.overlap.lexical_score + 0.65 * score)
            method += f"+passage_embeddings:{ctx.embedder.model_name}"
            limitations.append("Semantic scores compare retrieved evidence passages; they are not an exhaustive semantic search or duplication probabilities.")
        except Exception as exc:
            limitations.append(f"Semantic model unavailable ({type(exc).__name__}); deterministic text comparison completed.")

    if ctx.reranker is not None and candidates:
        # Cross-encoders score relevance on arbitrary scales. Use only within the
        # same classification, never reinterpret a raw logit as a probability.
        candidates.sort(key=lambda item: (SEVERITY[item.match_type], item.score), reverse=True)
        shortlist = candidates[:max(TOP_K, 20)]
        try:
            scores = []
            for item in shortlist:
                values = ctx.reranker.score(item.overlap.query_passage or "", [(item.record.record_id, item.overlap.source_passage or "")])
                if len(values) != 1 or not math.isfinite(float(values[0])):
                    raise ValueError("Invalid reranker output")
                scores.append(float(values[0]))
            for item, score in zip(shortlist, scores):
                item.reranker_score = score
            method += f"+passage_reranker:{ctx.reranker.model_name}"
            limitations.append(f"Reranker relevance scores order up to {len(shortlist)} candidates within the same match category; they do not confirm duplication.")
        except Exception as exc:
            limitations.append(f"Reranker unavailable ({type(exc).__name__}); deterministic ranking retained.")
    return method


def evaluate_duplication(ctx: ScreeningContext, run_id: str) -> list[Finding]:
    finding_id = new_id("finding")
    base = {
        "finding_id": finding_id, "screening_run_id": run_id, "application_id": ctx.application.id,
        "grant_call_id": ctx.grant_call.id, "type": FindingType.DUPLICATION, "title": "Proposal duplication check",
    }
    # A readable CV/budget must not stand in for an unreadable or missing proposal.
    proposals = [(meta, doc) for meta, doc in ctx.documents if meta.document_type == "proposal"]
    documents = [(meta, doc) for meta, doc in proposals if doc is not None and doc.extraction_status == "success" and doc.text.strip()]
    if not proposals:
        documents = [(meta, doc) for meta, doc in ctx.readable if meta.document_type in {"other", "unknown"}]
    query = profile_proposal("\n\n".join(_document_text(doc) for _, doc in documents))
    unreadable_query = len(proposals) - len(documents) if proposals else 0
    limitations = [
        "The check covers only readable, authorized comparison records; a no-match result is not proof of originality.",
        "Similarity scores and overlap coverage are text measures, not probabilities of duplication.",
    ]
    if unreadable_query:
        limitations.append(f"{unreadable_query} proposal document(s) could not be read; only extracted proposal text was assessed.")
    candidates = []
    skipped = 0
    for record in ctx.universe:
        if record.application_id == ctx.application.id:
            continue
        text = _document_text(record.document) if record.document is not None else record.text
        source = profile_proposal(text)
        if not source.assessable or (record.document is not None and record.document.extraction_status != "success"):
            skipped += 1
            continue
        overlap = compare_proposals(query, source)
        candidates.append(_Candidate(record, overlap, overlap.match_type, overlap.score))
    if skipped:
        limitations.append(f"{skipped} comparison record(s) had no usable substantive text and were excluded.")
    details = {
        "match_type": "NOT_ASSESSABLE", "compared_records": len(candidates) if query.assessable else 0,
        "available_records": len(ctx.universe), "skipped_records": skipped, "flagged": 0,
        "displayed_matches": 0, "coverage_complete": not ctx.unavailable_sources and not skipped and not unreadable_query,
        "unavailable_sources": [item.source_id for item in ctx.unavailable_sources],
        "source_coverage": [{"source_id": item.source_id, "state": item.state.value, "message": item.message} for item in ctx.coverage],
        "limitations": limitations, "query_documents": len(documents),
    }
    if not query.assessable or not candidates:
        reason = "No readable, substantive proposal narrative was available." if not query.assessable else "No authorized comparison records with usable substantive text were available."
        details["coverage_complete"] = False
        return [Finding(
            **base, status=FindingStatus.REVIEW_REQUIRED, signal="NOT_ASSESSABLE",
            explanation=reason + " Duplication could not be assessed; this is not evidence of originality." + coverage_note(ctx),
            recommended_action="Provide readable proposals and prior applications or funded project records, then run screening again.",
            method=METHOD, details=details,
        )]

    method = _optional_models(ctx, candidates, limitations)
    candidates.sort(key=lambda item: (
        SEVERITY[item.match_type], item.reranker_score if item.reranker_score is not None else -math.inf,
        item.score, item.record.record_id,
    ), reverse=True)
    flagged = [item for item in candidates if item.match_type != NONE]
    shown = flagged[:TOP_K] if flagged else candidates[:1]
    evidence, matches = [], []
    for item in shown:
        record, overlap = item.record, item.overlap
        query_evidence = _locate_application_sentence(documents, finding_id, overlap.query_passage) if overlap.query_passage else None
        source_evidence = record_evidence(finding_id, record, overlap.source_passage, field="duplication") if overlap.source_passage else None
        if item.match_type != NONE:
            if query_evidence:
                evidence.append(query_evidence)
            if source_evidence:
                evidence.append(source_evidence)
        label = item.match_type.replace("_", " ").capitalize()
        explanation = (
            f"{label}. Informative phrase overlap covers {overlap.query_coverage:.0%} of this proposal "
            f"and {overlap.source_coverage:.0%} of the comparison record; {overlap.shared_terms} shared content terms. "
            "Scores are text similarity measures, not a probability or funding decision."
        )
        if item.match_type == EXACT:
            explanation = "The complete extracted texts are identical after case, punctuation and whitespace normalization. Reviewer confirmation is required."
        matches.append(SimilarityMatch(
            finding_id=finding_id, source_type=record.source_type, record_id=record.record_id,
            application_id=record.application_id, document_id=record.document_meta.id if record.document_meta else None,
            title=record.title, similarity_score=round(item.score, 4), lexical_score=round(overlap.lexical_score, 4),
            semantic_score=round(item.semantic_score, 4) if item.semantic_score is not None else None,
            reranker_score=item.reranker_score, matched_passage=overlap.source_passage,
            matched_page=source_evidence.page if source_evidence else None,
            matched_section=source_evidence.section if source_evidence else None,
            matching_concepts=shared_concepts(overlap.query_passage or "", overlap.source_passage or ""),
            explanation=explanation, method=method, data_origin=record.data_origin,
            match_type=item.match_type, query_passage=overlap.query_passage,
            query_page=query_evidence.page if query_evidence else None,
            query_document_id=query_evidence.document_id if query_evidence else None,
            query_coverage=round(overlap.query_coverage, 4), source_coverage=round(overlap.source_coverage, 4),
            year=record.year, outcome=record.outcome,
        ))
    details.update(match_type=shown[0].match_type, flagged=len(flagged), displayed_matches=len(shown), method=method)
    if flagged:
        top = flagged[0]
        status, signal = FindingStatus.REVIEW_REQUIRED, "POSSIBLE_DUPLICATION"
        explanation = (
            f"{len(flagged)} of {len(candidates)} compared records need duplication review; "
            f"strongest match: {top.match_type.replace('_', ' ').lower()} with {top.record.title or top.record.record_id}. "
            "Similarity is a signal only; it does not establish duplication."
        )
        action = "Compare the proposal and source passages, project scope and funding history; confirm or dismiss the finding."
        confidence = calibrate_confidence(model_score=top.score, evidence_strength=0.8 if evidence else 0.4, agreement=1.0)
    else:
        status, signal = FindingStatus.PASS, NONE
        explanation = f"No significant duplication signal was found among {len(candidates)} readable comparison records. This result applies only to the searched records and is not evidence of originality."
        action = "Review the source coverage and add missing prior applications or funded projects when available."
        confidence = None
        if unreadable_query:
            status, signal = FindingStatus.REVIEW_REQUIRED, "NOT_ASSESSABLE"
            details["match_type"] = "NOT_ASSESSABLE"
            explanation = (
                f"The readable proposal portions had no significant match among {len(candidates)} records, "
                f"but {unreadable_query} proposal document(s) could not be read. "
                "The complete submission could not be assessed; this is not evidence of originality."
            )
            action = "Provide readable copies of the missing proposal documents and run screening again."
    if skipped or unreadable_query:
        explanation += " Coverage is partial because some proposal or comparison text was unavailable."
    return [Finding(
        **base, status=status, signal=signal, confidence=confidence,
        explanation=explanation + coverage_note(ctx), recommended_action=action,
        method=f"{METHOD}:{method}", evidence=evidence, matches=matches, details=details,
    )]
