# Product Workflow Implementation Specification

## Domain entities

| Entity | Purpose and minimum requirements |
|---|---|
| Organization | Tenant boundary, stable ID and status |
| User/Membership | Identity, organization membership, role and status |
| Grant Call | Funding opportunity, owner, dates, configuration and status |
| Call Document | RFP source, immutable version, checksum and storage reference |
| Requirement | Type, rule, source passage, confidence and verification state |
| Application | Reference, call/organization link and status |
| Application Document | Version, safe storage key, checksum and parser status |
| Screening Run | Input versions, rule/model versions, status and timestamps |
| Finding | Category, state, method, explanation and severity |
| Evidence | Exact source document/version, page, offsets/chunk and excerpt/hash |
| Review Decision | Reviewer, disposition, rationale and timestamp |
| Audit Event | Actor, action, resource, timestamp and correlation ID |

## Workflow states

Grant call: Draft → Requirements Extracted → Requirements In Review → Approved/Open → Closed/Archived.

Application ingestion: Received → Validating → Association Required / Queued → Processing → Ready for Screening / Failed / Rejected.

Screening run: Queued → Running → Completed / Completed With Warnings / Failed / Cancelled.

Finding: Generated → Needs Review → Confirmed / Dismissed / Escalated / Insufficient Evidence.

Validate every transition server-side and record it in audit history.

## Functional sequence

### A. Grant call and RFP
- Create/edit/archive grant calls.
- Upload/version RFPs; retain original checksum and metadata.
- Extract candidate requirements with page/source references.
- Display source excerpt, confidence and ambiguous/missing state.
- Allow authorized administrators to edit, accept, reject or defer requirements.
- Only verified requirements may drive eligibility rules.
- Preserve approved versions and the version used by each screening run.

### B. Application upload and association
- Support explicitly approved file formats and configurable size/count limits.
- Validate file signatures, not only extensions.
- Store originals in private object storage.
- Associate by explicit reference or controlled manual workflow.
- Ambiguous/unmatched files enter Association Required.
- Show per-file processing state and actionable errors.
- Use checksum/idempotency controls to prevent duplicate ingestion.

### C. Document extraction
- Extract text and structural metadata from supported digital documents.
- Preserve page, section, paragraph/chunk offsets and source version.
- Track parser version, extraction timestamp and warnings.
- Detect empty, encrypted, corrupted and unsupported documents.
- Do not claim OCR for scanned documents until implemented and evaluated.

### D. Deterministic eligibility/completeness
- Convert approved requirements into typed, testable rules.
- Outcomes: Pass, Fail, Needs Review, Not Assessable.
- Missing/ambiguous evidence is not automatically Fail.
- Show rule, evaluated value, evidence, rule version and reason.
- Authorize and audit rule changes.
- Regression-test rules against labelled fixtures.

### E. Similarity/duplication signals
- Establish exact/checksum and lexical retrieval baselines first.
- Add embedding-based semantic retrieval only with a versioned evaluation set.
- Use reranking only when measured improvement justifies latency/cost.
- Show candidate pairs, method/score, matching passages and source coverage.
- Calibrate thresholds on representative labelled data.
- Signals are review candidates, not plagiarism verdicts or funding decisions.

### F. Review and reporting
- Evidence-first review: finding, method, source coverage, passages and limitations.
- Record Confirm, Dismiss, Escalate or Insufficient Evidence with rationale.
- Preserve decision history; never overwrite audit history.
- Reports identify call/application/run versions, actions, coverage and limitations.
- Exports respect authorization.

## API contract requirements

Platform owns contract standards; Full-Stack implements application endpoints; AI/ML owns model-service interfaces. Every endpoint defines method/path/version, auth requirement, request/response schema, stable error codes, retry semantics, pagination, idempotency where applicable, audit/correlation IDs and rate/payload limits. Never expose stack traces, private storage keys or proposal content in errors.

## End-to-end acceptance scenario

Using labelled synthetic data: create a call and upload RFP; extract requirements with page references; administrator approves requirements; upload multiple application files; associate or flag ambiguity; extract text and provenance; run deterministic rules; retrieve similarity candidates with passages/coverage; reviewer records decisions and rationale; authorized manager generates report/audit history; a second organization cannot access the first organization's records; retrying a job creates no duplicate or corrupt history.
