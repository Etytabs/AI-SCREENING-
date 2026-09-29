import json
from dataclasses import asdict
from pathlib import Path

from ml.eligibility.rules import EligibilityRule, evaluate_rules
from ml.explainability.evidence import Evidence
from ml.plagiarism.overlap import token_overlap
from ml.semantic_matching.service import compare_texts
from services.ingestion.document import extract_document

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


def screen_document(path: str, proposal_id: str) -> dict:
    doc = extract_document(path, proposal_id)
    if doc.extraction_status != "success":
        return {
            "proposal_id": proposal_id,
            "extraction": asdict(doc),
            "flags": [],
            "status": doc.extraction_status,
        }

    ruleset_id, rules = load_demo_rules()
    checks = evaluate_rules(_attributes(doc.text), rules)
    flags = []
    evidence = []
    for check in checks:
        status = "pass" if check.status == "PASS" else "flag" if check.status == "FAIL" else "review"
        flags.append({
            "type": "eligibility",
            "status": status,
            "confidence": 1.0 if check.status in {"PASS", "FAIL"} else None,
            "evidence_ids": [check.criterion],
        })
        evidence.append(asdict(Evidence(
            proposal_id,
            check.criterion,
            str(check.observed),
            check.evidence,
        )))

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
    return {
        "proposal_id": proposal_id,
        "status": "screened",
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
        "model_versions": {
            "lexical_similarity": "token_jaccard_baseline-v0.1",
            "rules": ruleset_id,
        },
        "human_review_required": True,
    }
