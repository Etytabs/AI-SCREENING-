"""Call-specific eligibility built on ml.eligibility.rules.

Each verified criterion becomes an EligibilityRule. Observations come only from cited
application evidence: True (supported), False (explicitly contradicted) or None (no
evidence). The deterministic rule engine maps None to REVIEW, never to FAIL.
"""
import re
from dataclasses import dataclass, field

from ml.eligibility.rules import (
    STATUS_FAIL,
    STATUS_PASS,
    STATUS_REVIEW,
    EligibilityRule,
    evaluate_rules,
)
from ml.evidence.state import EvidenceRelationship
from ml.scoring.confidence import calibrate_confidence
from services.evidence.retrieval import select_evidence
from services.grant_workflow.models import (
    ApplicationDocument,
    Finding,
    FindingStatus,
    FindingType,
    RfpCriterion,
    new_id,
)
from services.grant_workflow.screening.context import ScreeningContext
from services.grant_workflow.screening.evidence import document_evidence, rfp_evidence, search_lines
from services.grant_workflow.text_utils import parse_amounts, parse_durations
from services.ingestion.document import ExtractedDocument

METHOD = "call_criteria_rules_v0.1"
KEYWORD_COVERAGE_THRESHOLD = 0.6


@dataclass
class Observation:
    value: bool | None
    explanation: str
    method: str
    evidence: list[tuple[ApplicationDocument, ExtractedDocument, str, EvidenceRelationship]] = field(default_factory=list)
    strength: float = 0.7


def _phrase_found(line: str, phrase: str) -> bool:
    return re.search(rf"(?<![a-z]){re.escape(phrase.lower())}(?![a-z])", line.lower()) is not None


def _observe_country(ctx: ScreeningContext, criterion: RfpCriterion) -> Observation:
    required = str(criterion.parameters["country"])
    hit = search_lines(ctx.readable, lambda line: line.lower().startswith("country:"))
    if hit is None:
        return Observation(None, f"The application does not state the lead institution's country; required: {required}.", "metadata:country")
    meta, doc, line = hit
    stated = line.split(":", 1)[1].strip()
    matches = stated.lower() == required.lower()
    relationship = EvidenceRelationship.SUPPORTS if matches else EvidenceRelationship.CONTRADICTS
    explanation = (
        f"Application states country '{stated}', which matches the required '{required}'."
        if matches else f"Application states country '{stated}'; the call requires '{required}'."
    )
    return Observation(matches, explanation, "metadata:country", [(meta, doc, line, relationship)], 0.9)


def _find_amount(ctx: ScreeningContext):
    for key in ("requested amount", "total requested", "amount requested"):
        hit = search_lines(ctx.readable, lambda line, key=key: line.lower().startswith(key + ":"))
        if hit and parse_amounts(hit[2]):
            return hit, parse_amounts(hit[2])[0]
    return None, None


def _observe_amount(ctx: ScreeningContext, criterion: RfpCriterion) -> Observation:
    limit = float(criterion.parameters["max_amount"])
    currency = criterion.parameters.get("currency")
    hit, amount = _find_amount(ctx)
    if hit is None or amount is None:
        return Observation(None, f"No requested amount was found in the submission; the call ceiling is {currency} {limit:,.0f}.", "amount_parser")
    meta, doc, line = hit
    if currency and amount.currency != currency:
        return Observation(
            None, f"Requested amount is stated in {amount.currency}; the ceiling is in {currency}. Conversion requires reviewer confirmation.",
            "amount_parser", [(meta, doc, line, EvidenceRelationship.UNCERTAIN)], 0.5,
        )
    within = amount.value <= limit
    return Observation(
        within,
        f"Requested {amount.currency} {amount.value:,.0f} {'is within' if within else 'exceeds'} the ceiling of {currency} {limit:,.0f}.",
        "amount_parser",
        [(meta, doc, line, EvidenceRelationship.SUPPORTS if within else EvidenceRelationship.CONTRADICTS)],
        0.9,
    )


def _observe_duration(ctx: ScreeningContext, criterion: RfpCriterion) -> Observation:
    limit = float(criterion.parameters["max_months"])
    hit = search_lines(
        ctx.readable,
        lambda line: bool(parse_durations(line)) and ("duration" in line.lower()),
    )
    if hit is None:
        return Observation(None, f"No project duration was found in the submission; the maximum is {limit:g} months.", "duration_parser")
    meta, doc, line = hit
    months = parse_durations(line)[0].months
    within = months <= limit
    return Observation(
        within,
        f"Stated duration of {months:g} months {'is within' if within else 'exceeds'} the maximum of {limit:g} months.",
        "duration_parser",
        [(meta, doc, line, EvidenceRelationship.SUPPORTS if within else EvidenceRelationship.CONTRADICTS)],
        0.9,
    )


def _observe_phrases(ctx: ScreeningContext, criterion: RfpCriterion) -> Observation:
    phrases = [str(p) for p in criterion.parameters["any_of"] if str(p).strip()]
    for phrase in phrases:
        hit = search_lines(ctx.readable, lambda line, phrase=phrase: _phrase_found(line, phrase))
        if hit:
            meta, doc, line = hit
            return Observation(True, f"Found '{phrase}' in {meta.filename}.", "phrase_match", [(meta, doc, line, EvidenceRelationship.SUPPORTS)], 0.75)
    return Observation(None, "None of the expected terms were found: " + ", ".join(phrases) + ".", "phrase_match")


def _observe_keywords(ctx: ScreeningContext, criterion: RfpCriterion) -> Observation:
    keywords = [str(k).lower() for k in criterion.parameters.get("keywords", [])]
    best = None
    for meta, doc in ctx.readable:
        for candidate in select_evidence(criterion.requirement_text, doc, embedder=ctx.embedder, top_k=1):
            if best is None or candidate.score > best[2].score:
                best = (meta, doc, candidate)
    if best is None or not keywords:
        return Observation(None, "No passage addressing this requirement was retrieved.", "hybrid_retrieval")
    meta, doc, candidate = best
    text = candidate.text.lower()
    coverage = sum(1 for k in keywords if k in text) / len(keywords)
    if coverage >= KEYWORD_COVERAGE_THRESHOLD:
        return Observation(
            True, f"Retrieved passage covers {coverage:.0%} of the requirement's key terms.", candidate.method,
            [(meta, doc, candidate.text, EvidenceRelationship.SUPPORTS)], 0.6,
        )
    return Observation(
        None, f"Closest retrieved passage covers only {coverage:.0%} of the requirement's key terms; reviewer check required.",
        candidate.method, [(meta, doc, candidate.text, EvidenceRelationship.UNCERTAIN)],
    )


def observe(ctx: ScreeningContext, criterion: RfpCriterion) -> Observation:
    parameters = criterion.parameters
    if parameters.get("country"):
        return _observe_country(ctx, criterion)
    if parameters.get("max_amount") is not None:
        return _observe_amount(ctx, criterion)
    if parameters.get("max_months") is not None:
        return _observe_duration(ctx, criterion)
    if parameters.get("any_of"):
        return _observe_phrases(ctx, criterion)
    return _observe_keywords(ctx, criterion)


_STATUS = {STATUS_PASS: FindingStatus.PASS, STATUS_FAIL: FindingStatus.FAIL}
_ACTIONS = {
    FindingStatus.PASS: "Verify that the cited evidence satisfies the requirement.",
    FindingStatus.FAIL: "Confirm the contradiction against the cited evidence before any decision.",
    FindingStatus.REVIEW_REQUIRED: "Locate evidence manually or request clarification from the applicant.",
}


def evaluate_eligibility(ctx: ScreeningContext, run_id: str) -> list[Finding]:
    criteria = [c for c in ctx.criteria if c.screening_use == "eligibility"]
    observations = {c.criterion_code: observe(ctx, c) for c in criteria}
    rules = [
        EligibilityRule(criterion_id=c.criterion_code, label=c.title, field=c.criterion_code, expected=True, missing_status=STATUS_REVIEW)
        for c in criteria
    ]
    checks = {check.criterion: check for check in evaluate_rules({k: o.value for k, o in observations.items()}, rules)}

    findings = []
    for criterion in criteria:
        observation = observations[criterion.criterion_code]
        check = checks[criterion.criterion_code]
        status = _STATUS.get(check.status, FindingStatus.REVIEW_REQUIRED)
        finding_id = new_id("finding")
        evidence = [rfp_evidence(finding_id, criterion)]
        for meta, doc, snippet, relationship in observation.evidence:
            item = document_evidence(
                finding_id, meta, doc, snippet, field=criterion.criterion_code,
                status=status.value, relationship=relationship, confidence=observation.strength,
            )
            if item:
                evidence.append(item)
        cited = any(e.citation_valid for e in evidence if e.source_type == "application_document")
        confidence = None
        if status != FindingStatus.REVIEW_REQUIRED:
            confidence = calibrate_confidence(model_score=observation.strength, evidence_strength=1.0 if cited else 0.4, agreement=1.0)
        findings.append(Finding(
            finding_id=finding_id,
            screening_run_id=run_id,
            application_id=ctx.application.id,
            grant_call_id=ctx.grant_call.id,
            criterion_id=criterion.id,
            type=FindingType.ELIGIBILITY,
            status=status,
            title=f"{criterion.criterion_code} · {criterion.title}",
            confidence=confidence,
            explanation=observation.explanation,
            recommended_action=_ACTIONS[status],
            method=f"{METHOD}:{observation.method}",
            evidence=evidence,
            details={"criterion_code": criterion.criterion_code, "rule_status": check.status, "observed": observation.value},
        ))
    return findings
