# ShakaHive First Product — MVP Definition

**Company:** ShakaHive  
**Category:** Research Intelligence  
**Product:** AI-Assisted Grant Screening  
**Working product name:** HiveScreen (proposed, pending team approval)  
**Status:** Draft for product and stakeholder validation.

## 1. Problem

Grant administrators must review funding calls and large volumes of applications. Eligibility, completeness, duplicate research, text overlap, semantic similarity and evidence review can require substantial manual effort. Simple keyword rules cannot reliably identify proposals that describe similar research using different terminology.

## 2. Product outcome

Help authorised grant administrators and reviewers process proposal information more efficiently and consistently by combining deterministic checks, ML/NLP-assisted discovery, evidence retrieval and human review.

## 3. Target users

- Grant administrators who configure calls, verify requirements and manage submissions.
- Reviewers who inspect findings, evidence and record review outcomes.
- Programme managers who need progress visibility and reports.
- System administrators who manage access, configuration and auditability.

Applicants are not the primary user of the first internal screening workflow.

## 4. Core workflow

Create grant call → upload/version RFP → extract requirements → administrator verifies requirements → open submissions → upload applications → process documents → run screening → inspect findings and evidence → record human decisions and rationale → audit and report.

## 5. MVP scope

### Included
- Grant-call creation and configuration.
- RFP upload, versioning and requirement extraction.
- Human verification, editing and approval of requirements.
- Single, multiple and ZIP application upload with association workflow.
- Document text extraction and provenance.
- Deterministic eligibility and completeness checks.
- Lexical and optional embedding-based semantic retrieval.
- Candidate duplication and text-overlap signals.
- Optional cross-encoder reranking.
- Evidence chunks, source references and coverage states.
- Reviewer decisions, notes and rationale.
- Audit history and screening reports.
- Synthetic demo data clearly labelled as synthetic.

### Excluded or conditional
- Automated funding decisions or automatic rejection.
- Automated plagiarism verdicts.
- Autonomous scientific novelty judgements.
- Production RIGMS access without formal authorization and integration specification.
- External scholarly database integrations until implemented and approved.
- Full grant lifecycle/M&E product workflows.
- Publication reconciliation as a first-release requirement.
- OCR for scanned PDFs unless separately implemented and validated.

## 6. AI and rules responsibilities

- Deterministic rules: explicit funding ceilings, duration, country requirements and configured mandatory conditions.
- ML/NLP: semantic retrieval, candidate similarity, reranking and pattern discovery.
- Evidence retrieval: relevant passages, page/chunk location, source identity and provenance.
- LLM/search grounding: only defined tasks with citations and provider/version traceability.
- Human review: confirms, dismisses, requests further review or escalates findings with rationale.

A missing value must not silently become a failure. A similarity score is not proof of plagiarism. A novelty signal is not a scientific judgement. A source that was unavailable must be shown as not searched, not as having no matches.

## 7. Acceptance criteria

A pilot candidate should demonstrate:
1. A grant call can be configured and its source RFP version retained.
2. Extracted requirements are traceable and require authorised verification before activation.
3. Applications can be uploaded and correctly associated or held for manual association.
4. Screening results distinguish assessed, review-required, blocked, partial and not-assessable states.
5. Consequential findings expose supporting evidence and source coverage.
6. Reviewers can record decisions and rationale.
7. Audit records identify actor, time and action.
8. Reports communicate synthetic/real data origin and system limitations.
9. Access control, persistence, backup and operational monitoring are validated before institutional production use.

## 8. Production-readiness gates

The repository's current workflow documentation identifies in-memory workflow storage and demo identity headers. These are not production controls. Before a real institutional pilot with confidential submissions, implement and validate persistent storage, real authentication, role-based authorization, secure file storage, retention/deletion controls, backups, monitoring, recovery and security testing.

RIGMS and external source integrations remain authorization-dependent. Obtain written permission, data-sharing terms, API specifications and security review before integration.

## 9. Evaluation

Evaluate document extraction, eligibility rule correctness, completeness classification, retrieval Recall@k/MRR/nDCG, duplicate candidate precision/recall, evidence validity, reviewer time, false-positive patterns, failure rates and user satisfaction. Use representative, authorized and appropriately labelled evaluation data. Publish sample size, methodology and limitations alongside results.

## 10. Product decisions requiring approval

- Confirm official product name and whether HiveScreen is adopted.
- Confirm first pilot institution and users.
- Confirm supported file formats, size limits and languages.
- Agree retention, data residency, access and deployment requirements.
- Agree pilot success thresholds with stakeholders.
- Approve which AI providers and public-source discovery methods are acceptable.
