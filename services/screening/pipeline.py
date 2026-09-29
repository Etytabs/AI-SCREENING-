from dataclasses import asdict
from pathlib import Path

from ml.duplicate_detection.service import find_candidate
from ml.eligibility.rules import evaluate_rules
from ml.explainability.evidence import Evidence
from ml.plagiarism.overlap import token_overlap
from ml.semantic_matching.service import compare_texts
from services.ingestion.document import extract_document

DEMO_RULES = {
    "has_title": True,
    "has_abstract": True,
    "has_methodology": True,
    "has_budget": True,
}

DEMO_HISTORICAL = [
    ("NRIF-2024-118", "AI-based crop disease detection using machine learning for maize farmers"),
    ("NRIF-2025-031", "Climate-smart irrigation analytics for smallholder agriculture"),
    ("NRIF-2024-074", "Digital health early warning and referral system"),
]

def _attributes(text: str) -> dict[str, bool]:
    lower = text.lower()
    return {
        "has_title": bool(text.strip()),
        "has_abstract": "abstract" in lower or "summary" in lower,
        "has_methodology": any(x in lower for x in ("methodology", "methods", "approach")),
        "has_budget": "budget" in lower,
    }

def screen_document(path: str, proposal_id: str) -> dict:
    doc = extract_document(path, proposal_id)
    if doc.extraction_status != "success":
        return {"proposal_id": proposal_id, "extraction": asdict(doc), "flags": [], "status": doc.extraction_status}

    checks = evaluate_rules(_attributes(doc.text), DEMO_RULES)
    flags = []
    evidence = []
    for check in checks:
        status = "pass" if check.passed else "flag"
        flags.append({"type":"eligibility" if check.criterion != "has_title" else "completeness","status":status,"confidence":1.0,"evidence_ids":[check.criterion]})
        evidence.append(asdict(Evidence(proposal_id, check.criterion, str(check.passed), check.evidence)))

    candidates = []
    for rid, rtext in DEMO_HISTORICAL:
        match = compare_texts(doc.text, rtext)
        candidates.append((rid, match.score, match.method))
    candidates.sort(key=lambda x:x[1], reverse=True)
    for rid, score, method in candidates[:3]:
        if score > 0:
            evidence.append(asdict(Evidence(rid, "historical_similarity", f"{score:.4f}", f"Compared with historical proposal using {method}.")))
    overlap = []
    for rid, rtext in DEMO_HISTORICAL:
        result = token_overlap(doc.text, rtext)
        if result.overlap_ratio > 0:
            overlap.append({"source_id":rid,"ratio":round(result.overlap_ratio,4),"shared_tokens":result.shared_tokens,"method":result.method})
    return {
        "proposal_id": proposal_id,
        "status": "screened",
        "extraction": asdict(doc),
        "completeness": {"passed": sum(c.passed for c in checks), "total": len(checks)},
        "eligibility_checks": [asdict(c) for c in checks],
        "similarity_candidates": [{"proposal_id":a,"similarity":round(b,4),"method":c} for a,b,c in candidates],
        "text_overlap": overlap,
        "flags": flags,
        "evidence": evidence,
        "model_versions": {"lexical_similarity":"token_jaccard_baseline-v0.1","rules":"nrif-demo-v0.1"},
        "human_review_required": True,
    }
