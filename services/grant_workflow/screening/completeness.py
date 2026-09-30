"""Call-specific completeness from verified mandatory-document requirements."""
import re

from ml.evidence.state import EvidenceRelationship
from ml.scoring.confidence import calibrate_confidence
from services.grant_workflow.models import (
    Finding,
    FindingEvidence,
    FindingStatus,
    FindingType,
    new_id,
)
from services.grant_workflow.rfp_extraction import DOCUMENT_LABELS, DOCUMENT_TYPES
from services.grant_workflow.screening.context import ScreeningContext
from services.grant_workflow.screening.evidence import document_evidence, rfp_evidence, search_lines

METHOD = "call_document_checklist_v0.1"


def evaluate_completeness(ctx: ScreeningContext, run_id: str) -> list[Finding]:
    findings = []
    criteria = [c for c in ctx.criteria if c.screening_use == "completeness"]
    unreadable = [meta for meta, doc in ctx.documents if doc is None or doc.extraction_status != "success"]
    inventory = ", ".join(f"{meta.filename} ({meta.document_type})" for meta, _ in ctx.documents) or "none"

    for criterion in criteria:
        doc_type = str(criterion.parameters.get("document_type") or "other")
        label = DOCUMENT_LABELS.get(doc_type, doc_type.replace("_", " "))
        conditional = bool(criterion.parameters.get("conditional"))
        finding_id = new_id("finding")
        evidence = [rfp_evidence(finding_id, criterion)]
        matching = [(meta, doc) for meta, doc in ctx.documents if meta.document_type == doc_type]
        readable_match = [(meta, doc) for meta, doc in matching if doc is not None and doc.extraction_status == "success" and doc.pages]
        confidence: float | None = None

        if readable_match:
            meta, doc = readable_match[0]
            first_line = next((line for page in doc.pages for line in page.lines), "")
            item = document_evidence(finding_id, meta, doc, first_line, field=doc_type, status="PASS", confidence=0.9) if first_line else None
            if item:
                evidence.append(item)
            status = FindingStatus.PASS
            explanation = f"{label} submitted as {meta.filename}."
            action = "Open the document to confirm it meets the requirement."
            confidence = calibrate_confidence(model_score=0.9, evidence_strength=1.0 if item else 0.5, agreement=1.0)
        elif matching:
            status = FindingStatus.REVIEW_REQUIRED
            explanation = f"{label} was submitted ({matching[0][0].filename}) but its text could not be extracted."
            action = "Open the original file or request a readable copy."
        else:
            terms = DOCUMENT_TYPES.get(doc_type, (doc_type,))
            pattern = re.compile(r"(?<![a-z])(" + "|".join(re.escape(t) for t in terms) + r")(?![a-z])")
            section = search_lines(
                ctx.readable,
                lambda line, pattern=pattern: len(line.split()) <= 8 and pattern.search(line.lower()) is not None,
            )
            if section is not None:
                meta, doc, line = section
                item = document_evidence(finding_id, meta, doc, line, field=doc_type, status="REVIEW_REQUIRED",
                                         relationship=EvidenceRelationship.PARTIALLY_SUPPORTS, confidence=0.5)
                if item:
                    evidence.append(item)
                status = FindingStatus.REVIEW_REQUIRED
                explanation = f"No separate {label.lower()} was submitted; a matching section was found in {meta.filename}."
                action = "Decide whether the section satisfies the requirement."
            elif conditional:
                status = FindingStatus.REVIEW_REQUIRED
                explanation = f"{label} not found. The requirement is conditional, so applicability must be confirmed."
                action = "Confirm whether the condition applies to this application."
            elif unreadable:
                status = FindingStatus.REVIEW_REQUIRED
                explanation = f"{label} not found, but {len(unreadable)} document(s) could not be read, so absence cannot be confirmed."
                action = "Inspect the unreadable documents."
            elif criterion.required:
                status = FindingStatus.FAIL
                explanation = f"{label} not found among {len(ctx.documents)} submitted document(s)."
                action = "Confirm the document is missing or request it from the applicant."
                confidence = calibrate_confidence(model_score=0.8, evidence_strength=0.8, agreement=1.0)
            else:
                status = FindingStatus.REVIEW_REQUIRED
                explanation = f"Optional {label.lower()} not found."
                action = "No action unless the reviewer considers it necessary."
            evidence.append(FindingEvidence(
                finding_id=finding_id,
                source_id=ctx.application.id,
                source_type="submission_inventory",
                text=f"Submitted documents: {inventory}",
                field=doc_type,
                relationship=EvidenceRelationship.UNCERTAIN,
            ))

        findings.append(Finding(
            finding_id=finding_id,
            screening_run_id=run_id,
            application_id=ctx.application.id,
            grant_call_id=ctx.grant_call.id,
            criterion_id=criterion.id,
            type=FindingType.COMPLETENESS,
            status=status,
            title=f"{criterion.criterion_code} · {label}",
            confidence=confidence,
            explanation=explanation,
            recommended_action=action,
            method=METHOD,
            evidence=evidence,
            details={"criterion_code": criterion.criterion_code, "document_type": doc_type, "conditional": conditional},
        ))
    return findings
