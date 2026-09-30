import json
from dataclasses import asdict
from pathlib import Path

from ml.evidence.state import AssessmentState, EvidenceRelationship, RunState
from ml.eligibility.rules import EligibilityRule, evaluate_rules
from ml.explainability.evidence import Evidence
from ml.plagiarism.overlap import token_overlap
from ml.semantic_matching.service import compare_texts
from services.evidence.chain import EvidenceChain
from services.evidence.citations import CitationLocator, validate_citation
from services.ingestion.document import extract_document
from services.screening.run_state import derive_run_state

RULES_PATH = Path(__file__).resolve().parents[2] / "data" / "rules" / "nrif_demo_eligibility.json"

DEMO_HISTORICAL = [
    ("NRIF-2024-118", "AI-based crop disease detection using machine learning for maize farmers"),
    ("NRIF-2025-031", "Climate-smart irrigation analytics for smallholder agriculture"),
    ("NRIF-2024-074", "Digital health early warning and referral system"),
]


def load_demo_rules() -> tuple[str, list[EligibilityRule]]:
    payload = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    ruleset_id = payload["ruleset_id"]
    rules = [
        EligibilityRule(
            criterion_id=item["criterion_id"],
            label=item["label"],
            field=item["field"],
            expected=item["expected"],
            evidence_required=item.get("evidence_required", True),
            missing_status=item.get("missing_status", "UNKNOWN"),
        )
        for item in payload["rules"]
    ]
    return ruleset_id, rules


def _attributes(text: str) -> dict[str, object]:
    lower = text.lower()
    return {
        "has_methodology": any(x in lower for x in ("methodology", "methods", "approach")),
        "eligible_institution": None,
        "within_funding_scope": None,
        "partner_letter_present": None,
        "ethics_approval_present": None,
        "within_funding_ceiling": None,
    }


def _assessment_state(status: str) -> AssessmentState:
    return {
        "PASS": AssessmentState.MET,
        "FAIL": AssessmentState.NOT_MET,
        "REVIEW": AssessmentState.CLARIFICATION_REQUIRED,
        "UNKNOWN": AssessmentState.NOT_ASSESSABLE,
    }[status]


def _citation_for_check(doc, criterion_id: str, evidence: str) -> tuple[CitationLocator, bool] | None:
    if not evidence or evidence.startswith("no observed value"):
        return None
    for page in doc.pages:
        position = page.text.lower().find(evidence.lower())
        if position >= 0:
            citation = CitationLocator(
                document_id=doc.source_id,
                document_version=1,
                page_number=page.page_number,
                start=position,
                end=position + len(evidence),
                evidence=page.text[position:position + len(evidence)],
            )
            return citation, validate_citation(doc, citation)
    return None


def screen_document(path: str, proposal_id: str) -> dict:
    doc = extract_document(path, proposal_id)
    if doc.extraction_status != "success":
        return {
            "proposal_id": proposal_id,
            "extraction": asdict(doc),
            "flags": [],
            "status": doc.extraction_status,
            "run_state": RunState.FAILED.value,
        }

    ruleset_id, rules = load_demo_rules()
    checks = evaluate_rules(_attributes(doc.text), rules)
    flags = []
    evidence = []
    evidence_chain = []

    for check in checks:
        assessment = _assessment_state(check.status)
        status = "pass" if assessment == AssessmentState.MET else "flag" if assessment == AssessmentState.NOT_MET else "review"
        flags.append({
            "type": "eligibility",
            "status": status,
            "assessment_state": assessment.value,
            "confidence": 1.0 if check.status in {"PASS", "FAIL"} else None,
            "evidence_ids": [check.criterion],
        })
        evidence.append(asdict(Evidence(
            proposal_id,
            check.criterion,
            str(check.observed),
            check.evidence,
        )))

        citation_result = _citation_for_check(doc, check.criterion, check.evidence)
        if citation_result:
            citation, valid = citation_result
            evidence_chain.append(asdict(EvidenceChain.now(
                finding_id=f"{proposal_id}:{check.criterion}",
                criterion_id=check.criterion,
                status=assessment.value,
                relationship=EvidenceRelationship.SUPPORTS.value,
                confidence=1.0 if check.passed is not None else 0.0,
                document_id=doc.source_id,
                document_version=1,
                page_number=citation.page_number,
                chunk_id=None,
                evidence_span=citation.evidence,
                source_id=proposal_id,
                citation_locator=citation.locator,
            )))
            flags[-1]["citation_valid"] = valid
        else:
            flags[-1]["citation_valid"] = False

    candidates = []
    for rid, rtext in DEMO_HISTORICAL:
        match = compare_texts(doc.text, rtext)
        candidates.append((rid, match.score, match.method))
    candidates.sort(key=lambda x: x[1], reverse=True)
    for rid, score, method in candidates[:3]:
        if score > 0:
            evidence.append(asdict(Evidence(
                rid,
                "historical_similarity",
                f"{score:.4f}",
                f"Compared with historical proposal using {method}.",
            )))
    overlap = []
    for rid, rtext in DEMO_HISTORICAL:
        result = token_overlap(doc.text, rtext)
        if result.overlap_ratio > 0:
            overlap.append({
                "source_id": rid,
                "ratio": round(result.overlap_ratio, 4),
                "shared_tokens": result.shared_tokens,
                "method": result.method,
            })

    run_state = derive_run_state(requested=1, completed=1)
    return {
        "proposal_id": proposal_id,
        "status": "screened",
        "run_state": run_state.value,
        "extraction": asdict(doc),
        "completeness": {
            "passed": sum(c.passed is True for c in checks),
            "total": len(checks),
        },
        "eligibility_checks": [asdict(c) for c in checks],
        "similarity_candidates": [
            {"proposal_id": a, "similarity": round(b, 4), "method": c}
            for a, b, c in candidates
        ],
        "text_overlap": overlap,
        "flags": flags,
        "evidence": evidence,
        "evidence_chain": evidence_chain,
        "evidence_coverage": {
            "internal_document": run_state.value,
            "citation_validated_findings": sum(
                flag["citation_valid"] for flag in flags
            ),
            "findings": len(flags),
        },
        "model_versions": {
            "lexical_similarity": "token_jaccard_baseline-v0.1",
            "rules": ruleset_id,
        },
        "human_review_required": True,
    }
