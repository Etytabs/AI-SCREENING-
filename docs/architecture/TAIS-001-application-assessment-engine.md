# TAIS-001: Application Assessment Engine

- **Document ID:** TAIS-001
- **Owner:** Software Developer / AI Platform Developer
- **Status:** Approved
- **Last updated:** 13 November 2026
- **Approval status:** Approved engineering specification for staged implementation; unresolved infrastructure and policy selections remain subject to the cited ADRs and product approvals
- **Version:** 1.0
- **Authority:** Subordinate to [FPDR-001](../../company/product/FPDR-001-application-assessment-engine.md) and existing canonical architectural decisions
- **Related decisions:** [ADR-001](decisions/ADR-001-authentication-and-session-model.md); [ADR-002](decisions/ADR-002-authorization-and-organization-isolation.md)
- **Related documents:** [Architecture overview](overview.md); [Platform and data plan](../implementation/platform-and-data.md); [Security and DevOps standard](../implementation/security-quality-and-devops.md); [AI/ML evaluation standard](../implementation/ai-ml-and-evaluation.md); [Current workflow](../grant-workflow.md); [FPDR-001](../../company/product/FPDR-001-application-assessment-engine.md)
- **Related work:** Eight implementation workstreams in §12

## Change history

| Version | Date | Change | Approval |
|---|---|---|---|
| 1.0 | 13 November 2026 | Specify the audited current state, target modular architecture, contracts, calculation behaviour, API/UI direction, controls, validation and implementation workstreams. | Approved for implementation planning |

## 1. Authority, status, and implementation boundary

This specification translates FPDR-001 into an engineering blueprint. FPDR-001 remains authoritative if any technical interpretation conflicts with an approved product decision. ADR-001 and ADR-002 remain canonical; this specification does not revise them.

Approval applies to the staged implementation approach and contracts below. It does **not** select an authentication vendor, persistence adapter or migration tool, queue, object-storage provider, retention period, model, or external integration. Resolve such selections under existing ADR processes before introducing them. No database migration or unfinished assessment functionality is authorized by this documentation change.

Use the existing modular FastAPI application and Next.js dashboard, with in-process service boundaries first. Do not introduce independently deployed microservices without a later architecture decision. Keep the existing screening workflow and its findings/review history; add assessment capability alongside it.

## 2. Current-state repository audit

This section records implementation visible in the repository as audited for this specification. It is not a runtime, deployment, authorization, or institutional-readiness certification.

### 2.1 Architecture, data, and existing components

| Area | Verified current state | Assessment-engine implication |
|---|---|---|
| API and application services | FastAPI routes under `/api/v1`; route handlers translate to `GrantWorkflowService` and read-only `WorkflowViews`. Business logic is in `services/grant_workflow/`. | Add assessment routes/schemas and a service module through the existing API/service boundary; do not put scoring in route handlers. |
| Domain contracts | Pydantic models in `services/grant_workflow/models.py`; frontend mirrors them in `apps/web/lib/types.ts`. IDs use prefixed UUID-derived strings; timestamps are UTC. | Add explicit assessment contracts and keep frontend/API types aligned. Existing `RfpCriterion` is an extracted/verified call requirement, not an assessment rubric criterion. |
| Call and RFP workflow | `GrantCall`, versioned `RfpDocument`, and `RfpCriterion`; rule-based extraction cites source page/section, administrators verify/edit/reject requirements, and confirmed active requirements gate screening. | Reuse call identity, requirement source links, verification workflow, and call status boundaries. Create a distinct versioned rubric; do not overload RFP requirements with weighted quality scores. |
| Application and document workflow | `Application`, versioned `ApplicationDocument`, `Applicant`, `Institution`, and pending uploads. PDF/DOCX/TXT parsing retains page text/lines and extraction metadata. | Reuse application and extracted-document identifiers as source references. Introduce explicit input-version snapshots because the application record itself has no immutable assessment input version. |
| Eligibility | `services/grant_workflow/screening/eligibility.py` turns verified call criteria into deterministic rules. Explicit observations can pass/fail; missing or ambiguous observations map to review required. Results are criterion findings with citations. `ml/eligibility/rules.py` also supports UNKNOWN/REVIEW missing states. | Reuse deterministic rule/evidence patterns, but preserve eligibility as its own gate. Existing outcomes are screening signals, not the new approved call-level eligibility enum. |
| Other screening stages | Orchestrator stages include requirement mapping, eligibility, completeness, duplication, text similarity, novelty, and evidence. Stage failures produce partial runs/review-required findings. | Keep these findings and source coverage; do not recast them as quality scores or plagiarism determinations. |
| Similarity and duplication | Same-call application comparisons, earlier applications, synthetic history and optional local archive; lexical matching is available, embeddings/reranking are optional. Findings can include paired query/source passages and source metadata. | Reuse retrieval methods and comparison evidence as inputs where the approved criterion calls for them; scores remain similarity signals only. |
| Literature and novelty | OpenAlex-backed literature comparison exists as an optional screening provider; it may be unsearched or partial. Research-source adapters exist, but listed external providers are not generally enabled. Novelty is a signal stage, not a scientific judgment. | Reuse provider adapters/coverage states only where authorized. No broad coverage or operational novelty claims. |
| Evidence and provenance | `FindingEvidence` carries source type/id, optional document, page/section, excerpt, relationship and citation validation. `CitationLocator` validates page/range/excerpt against extracted text. Runs retain pipeline version and coverage; source failures are not zero results. | Extend with immutable source version/checksum, exact offsets/locator, method/model provenance, and explicit evidence quality/availability. Avoid copying sensitive excerpts into audit events. |
| Review and audit | Existing `ReviewerDecision`, `ReviewerNote`, `ReviewState`, `WorkflowAudit`, and report read models preserve confirm/dismiss/request-review/escalate actions, notes, actor and timestamps. The separate `DecisionHistory` helper is process-local. | Reuse existing reviewer actions and actor attribution; persist append-only assessment-specific adjustments/reviews and preserve the original AI result. Do not treat demo audit storage as durable. |
| Ranking/recommendations | Repository search found no application-level weighted assessment engine, cross-application competitive ranking, or the four-category recommendation contract. Retrieval candidate ranking is not funding-call ranking. | Implement new domain behavior; do not present retrieval rank as a grant assessment rank. |
| Frontend | Next.js 14/React 18 dashboard with call selector, applications, screening, application workspace, `DocumentViewer`, `FindingList`, `EvidenceDrawer`, reports, theme and existing brand styles. API client sends demo role/user headers. | Extend existing dashboard/design system; reuse document/evidence/review patterns. Do not treat UI role gating or demo headers as authorization. |

### 2.2 Persistence, identity, authorization, dependencies, and deployment

- `WorkflowRepository` is a protocol; `InMemoryWorkflowRepository` is the current workflow implementation. Application records, findings, audit and extracted content are lost on API process restart.
- The default `ThreadPoolJobRunner` is in-process and non-durable. Tests commonly use `InlineJobRunner`.
- A separate local duplication library uses SQLite. It is not persistence for the grant workflow.
- `docker-compose.yml` declares PostgreSQL/pgvector and sets `DATABASE_URL`, but no workflow repository adapter or migration system uses that database. `pyproject.toml` has no SQLAlchemy, database driver, or migration dependency. PostgreSQL/pgvector is a target in existing platform documentation, not an implemented assessment persistence layer.
- API actor identity is parsed from caller-supplied `X-User-Role` and `X-User-Id` headers (`apps/api/dependencies.py`). The frontend constructs these headers from a demo role. This is not authentication. Many read endpoints do not require an actor; service role checks on selected writes do not provide resource-level authorization. ADR-002 describes the intended future model, not an implemented one.
- Current role enums and grants are legacy/demo vocabulary. Preserve the approved separation between ShakaHive Team Administrator and Grant Administrator in ADR-002; do not map old role labels to production privileges without an approved mapping. Reviewer assignment and per-resource access are not implemented as production controls.
- `services/grant_workflow/providers.py` explicitly makes RIGMS authorization/API-spec dependent and unavailable. OpenAlex is optional and its literature search does not establish comprehensive scholarly coverage. Crossref, PMC, arXiv, DOAJ and CORE adapters/registry entries do not mean every service is authorized, configured, or wired into the core workflow.
- Scanned-PDF OCR is not implemented. Model-backed embeddings and reranking are optional extras and disabled unless configured. Current small synthetic retrieval evaluations are diagnostic only.
- Current CI uses GitHub Actions: backend install, Ruff and pytest; frontend Node 20, npm install, lint, TypeScript, Vitest and build. Deployment and live configuration are not established by this source audit.

### 2.3 Reuse, extension, and new implementation

**Reuse:** call/application/document IDs and lifecycle; requirement verification as source context; deterministic eligibility rule patterns; screening/evidence/source-coverage services; provider interfaces; audit and reviewer action concepts; Pydantic/FastAPI, API client/types, dashboard shell, document viewer, evidence drawer, report layout and current test runners.

**Extend:** persistence protocol only after an approved adapter/migration decision; input and rubric version snapshots; authorization policy at every read/write boundary; append-only durable review/audit; report models and frontend navigation/workspace; evaluation harness with assessment-specific labelled data.

**New:** rubric version and approval service; criterion assessment contracts; quality rating/normalization and weighted score calculator; final ranking snapshots; recommendation contract and constrained generation/evaluation; criterion score-adjustment workflow; assessment report generation; assessment-specific audit/versioning operations and user experience.

## 3. Target architecture and service boundaries

Implement these as internal modules/services in the existing application initially. Every public mutation and resource read must pass through trusted authentication and resource-level authorization before calling domain logic. AI-assisted interpretation returns evidence-linked proposals; deterministic rules own validation, weights, totals, normalization, gates, ranking, tie preservation, and version checks.

| Component | Responsibility and interface boundary |
|---|---|
| **1. Rubric Manager** | Create call-bound rubric drafts; validate criterion definitions, weights, applicability and rating anchors; submit for approval; approve/supersede versions with authorized actor and audit event. It returns an immutable approved snapshot to assessment runs. It does not score applications. |
| **2. Evidence Aggregator** | Resolve only evidence available to the authorized call/application; normalize references to extracted documents, verified call requirements, screening findings and explicitly authorized providers. Return evidence items, source provenance, availability/coverage, and missing-evidence records. It does not convert unavailable sources to no evidence. |
| **3. Eligibility Evaluator** | Apply deterministic, approved mandatory eligibility rules to extracted facts and cited evidence. Return `ELIGIBLE`, `INELIGIBLE`, or `PENDING_VERIFICATION` plus per-condition results and provenance. Never uses the weighted quality score to change eligibility. |
| **4. Criterion Assessment Service** | For each scored criterion, propose a 0–4 rating and evidence-linked rationale, or a non-score state. Store evaluator/model/prompt/config version and uncertainty. AI may interpret text but cannot decide missing evidence is zero. Human review can confirm/challenge/adjust without changing the original proposal. |
| **5. Score Calculator** | Pure deterministic function over a specific approved rubric and complete criterion assessments. Validate weights, status/applicability and input versions; normalize `rating × 25`; calculate exact weighted sum. Reject incomplete/unapproved input; never infer or impute. |
| **6. Ranking Service** | Select eligible, complete assessments for one call/rubric version and defined cohort; sort by unrounded overall score; preserve ties; write immutable snapshot and member run/version references. No award/allocation output. |
| **7. Recommendation Service** | Produce the constrained four-category advisory structure from approved rubric interpretation and versioned assessment/eligibility/evidence; enforce eligibility and uncertainty restrictions. It may not create a funding decision. |
| **8. Human Review Service** | Apply existing approved reviewer workflow to assigned resources; accept/challenge findings, adjust score with justification, request clarification, escalate, record notes, and confirm/dismiss findings. Append review events and maintain AI/human versions separately. |
| **9. Assessment Report Generator** | Build access-controlled reports from immutable assessment, rubric, recommendation, review, ranking and evidence references. Include data origin, coverage, limitations, versions, disclaimer and human actions. It does not recompute or silently change results. |
| **10. Audit and Versioning Service** | Issue stable version IDs; record who/what/when/resource/action/old-new references/correlation; protect immutable runs, rubric versions, ranking snapshots and review history. Define retention only after approved data policy; never place proposal text/secrets in ordinary audit detail. |

**Flow:** authorize request → resolve approved rubric/input versions → aggregate evidence and source coverage → independently evaluate eligibility → assess each quality criterion (AI proposals and/or human findings) → validate completeness → deterministic score → constrained recommendation → mandatory human review → eligible-cohort ranking snapshot → report and append-only audit.

## 4. Data contracts and lifecycle

These are conceptual API/domain contracts, not an instruction to immediately migrate the database. Use stable non-guessable IDs, UTC timestamps, decimal values for weights/scores, immutable version references, explicit nullable fields, and validated enumerations. Every resource belongs to a grant call/workspace and inherits its resource-level authorization scope. The exact SQL representation, constraints and migration tool require the persistence ADR decision.

### 4.1 `AssessmentRubric`

| Field | Type | Requirement / validation |
|---|---|---|
| `rubric_id` | opaque string/UUID | Required stable logical rubric identifier. |
| `grant_call_id` | opaque string/UUID | Required FK to one call; call scope is immutable. |
| `version` | positive integer | Required, unique per rubric; monotonically increases; never edited in place once approved. |
| `state` | enum | `DRAFT`, `IN_REVIEW`, `APPROVED`, `SUPERSEDED`; only approved versions can be used operationally. |
| `title`, `description` | string, optional description | Non-empty title; versioned content. |
| `criteria` | ordered list of `AssessmentCriterion` | At least one applicable scored criterion; IDs unique within version. |
| `scoring_policy` | object | Scale, normalization, exact weight precision, applicability/N/A and completeness rules; no hidden defaults. |
| `recommendation_policy` | object, optional | Call-specific bands/rules only if separately approved; otherwise no score threshold is implied. |
| `created_by`, `created_at` | principal ID, UTC timestamp | Required; server-attributed. |
| `approved_by`, `approved_at` | principal ID, UTC timestamp, nullable | Required only when approved; approver must have explicitly authorized rubric-approval permission; cannot be the caller-supplied identity. |
| `supersedes_version` | positive integer, nullable | Required when a version replaces an approved version. |
| `content_hash` | string, nullable until canonicalized | Hash of canonical rubric content for reproducibility. |

**Validation:** every scored applicable criterion has weight `> 0`; weights are decimal percentages and sum exactly to `100.00` for the approved version; non-scored/eligibility criteria carry no score weight; required anchors and N/A behavior are explicit; approval is an append-only state transition; any post-approval change creates a new version. A concurrently edited draft must fail optimistic version checks rather than overwrite another update.

### 4.2 `AssessmentCriterion`

Required: `criterion_id`, `rubric_id`, `rubric_version`, stable `code`, `title`, `description`, `kind` (`QUALITY_SCORED`, `ELIGIBILITY`, `INFORMATIONAL`), `required`, `applicability_rule`, `weight` (decimal percentage for scored items only), `rating_anchors` for 0–4, `evidence_expectations`, `order`, `created_at`.

Optional: `parent_criterion_id`, `source_requirement_ids`, `source_document_version`, `guidance`, `not_applicable_policy`, `updated_at` (draft only). Enforce unique criterion IDs/codes per version, valid parent links, rating anchors for all 0–4 values, no quality weight on eligibility or informational criteria, and approved explicit N/A/weight treatment. Rubric approval freezes the criterion; edits create a new rubric version.

### 4.3 `AssessmentRun`

Required: `assessment_id`, `grant_call_id`, `application_id`, `rubric_id`, `rubric_version`, `state`, `created_by`, `created_at`, `assessment_input_version`, `call_requirement_version`, `evaluator_version`, `calculation_version`, `criterion_assessment_ids`, and `eligibility_result_id`.

Optional: `started_at`, `completed_at`, `batch_id`, `supersedes_assessment_id`, `model/provider/build/prompt/config identifiers`, `source_coverage[]`, `completeness`, `uncertainty_summary`, `overall_score` (decimal 0–100 only when score is valid), `recommendation_id`, `failure_code`.

States: `QUEUED`, `RUNNING`, `COMPLETE`, `PARTIAL`, `BLOCKED`, `FAILED`, `CANCELLED`, `SUPERSEDED`. A run is immutable after terminal completion; corrections/re-runs create a new run linked to the prior one. Store exact application-document IDs/versions and hashes, call/RFP versions, rubric snapshot hash, evaluator/model version and deterministic calculator version. Do not overwrite an existing run when a source or model changes.

### 4.4 `CriterionAssessment`

Required: `criterion_assessment_id`, `assessment_id`, `criterion_id`, `criterion_version`, `state`, `evaluator_type` (`AI`, `HUMAN`, `RULE`), `rationale`, `evidence_ids[]`, `created_at`, `evaluator_version` (for machine/rule outputs).

Optional: `rating` integer 0–4, `normalized_score` decimal 0–100, `uncertainty` structured value, `limitations[]`, `supersedes_assessment_id`, `review_state`, `human_adjustment_id`.

States: `ASSESSED`, `NOT_ASSESSED`, `INSUFFICIENT_EVIDENCE`, `NOT_APPLICABLE`, `FAILED`. `ASSESSED` requires a rating and rationale; other states must not carry a numeric rating. `NOT_APPLICABLE` requires rubric permission and a recorded applicability rationale. `INSUFFICIENT_EVIDENCE` requires an explanation and, where possible, missing-evidence references. Machine results are immutable; human adjustment is a linked new record with actor, justification and old/new value. Do not use a model confidence as a calibrated probability unless separately validated.

The uncertainty object carries a qualitative `level` (`LOW`, `ELEVATED`, `HIGH`, `NOT_ASSESSED`) and one or more reasons, such as missing evidence, unavailable sources, conflicting evidence, or evaluator disagreement. Its derivation must be versioned and explainable; these labels are not probabilities or accuracy claims.

### 4.5 `AssessmentEvidence`

Required: `evidence_id`, `assessment_id`, `criterion_assessment_id` or `eligibility_result_id`, `source_type`, `source_id`, `source_version`, `relationship` (`SUPPORTS`, `CONTRADICTS`, `PARTIALLY_SUPPORTS`, `UNCERTAIN`, `NOT_RELEVANT`), `provenance`, `retrieved_at`.

Optional: `document_id`, `page`, `section`, `start_offset`, `end_offset`, `excerpt`, `excerpt_hash`, `citation_locator`, `citation_valid`, `provider_record_id`, `source_url`, `coverage_state`.

Reference original protected content rather than duplicate it unnecessarily. A citation must resolve to the exact authorized source/version and excerpt; failed citation validation is explicit. Never expose private object keys or external content outside access policy. Similarity findings require both query and match passages plus source provenance; an unavailable source remains a coverage state, not a zero-match evidence item.

### 4.6 `AssessmentRecommendation`

Required: `recommendation_id`, `assessment_id`, `category` (`STRONGLY_ALIGNED`, `ALIGNED_WITH_CONDITIONS`, `FURTHER_ASSESSMENT_REQUIRED`, `NOT_CURRENTLY_ALIGNED`), `summary`, `rationale`, `supporting_finding_ids[]`, `evidence_ids[]`, `missing_evidence[]`, `uncertainty`, `limitations[]`, `reviewer_attention[]`, `evaluator_version`, `human_review_status`, `created_at`.

Optional: `supersedes_recommendation_id`, `policy_version`, `human_reviewed_by`, `human_reviewed_at`. Machine recommendations are immutable; changed recommendation is a new version. Enforce that eligibility failure cannot map to either positive category, and incomplete/insufficient evidence cannot be represented as a definitive completed assessment. Output must carry an advisory/non-funding-decision declaration in API and report.

### 4.7 `AssessmentRanking`

Required: `ranking_snapshot_id`, `grant_call_id`, `rubric_id`, `rubric_version`, `cohort_definition`, `members[]`, `eligibility_policy_version`, `calculation_version`, `created_by`, `created_at`.

Each member includes `application_id`, `assessment_id`, `assessment_input_version`, `eligibility_result_id`, `overall_score`, and `rank`. Optional: snapshot label, reviewer note, superseding snapshot ID.

Only complete, sufficiently assessed, eligible applications for the exact call/rubric version may be included. Preserve ties using the unrounded deterministic score; default display uses shared competition ranks (e.g. 1, 1, 3), with no tie-break. Snapshot is immutable; refresh creates another snapshot. No funding allocation or award fields are inferred from rank.

### 4.8 `HumanReviewRecord`

Required: `review_record_id`, `assessment_id`, `resource_scope`, `actor_id`, `action`, `created_at`, `previous_state`, `new_state`, `reviewer_assignment_id` or authorized assignment reference.

Actions include existing `ACCEPT`, `CHALLENGE`, `REQUEST_CLARIFICATION`, `ESCALATE`, `ADD_NOTE`, `CONFIRM_FINDING`, `DISMISS_FINDING`, and `ADJUST_SCORE`. `ADJUST_SCORE` requires criterion ID, prior AI/human result reference, new rating, and non-empty justification. A reviewer may only act within their active call/application assignment. Records are append-only and do not mutate the source AI assessment.

Optional: `criterion_assessment_id`, `finding_id`, `note`, `justification`, `linked_review_record_id`, `resolution`, `resolved_by`, `resolved_at`. Clarification record requires a question and authorized recipient; never assume a direct applicant-contact integration exists.

### 4.9 `AssessmentAuditEvent`

Required: `event_id`, `event_type`, trusted `actor_id` or explicit system principal, `resource_type`, `resource_id`, `grant_call_id`, `occurred_at` (UTC), `correlation_id`, `resource_version`, and minimal structured `details`.

Events include rubric create/edit/submit/approve/supersede; assessment start/complete/fail; evidence link/validation; recommendation creation; review/adjustment; ranking snapshot; report generation/export; access-policy denial and final-decision recording if separately approved. Old/new values should reference version IDs and changed fields, not repeat sensitive proposal content. Append-only retention, tamper protection, access and deletion rules require approved retention policy and platform controls.

## 5. Scoring, completeness, eligibility, and ranking

### 5.1 Deterministic rating and aggregation

For each valid assessed quality criterion `i`:

```text
normalized_i = rating_i × 25
overall_score = Σ(weight_i × normalized_i) / 100
```

`weight_i` is a decimal percentage from the approved rubric, and approved scored weights sum to exactly 100. Use decimal arithmetic with a specified precision/rounding mode; serialize/display to two decimals without using rounded display values for ranking or tie detection. Validate `rating ∈ {0,1,2,3,4}` and reject an out-of-range value. No averaging of missing ratings, implicit zero, or hidden score imputation.

**Deterministic example:** weights `40%, 35%, 25%`; ratings `3, 2, 4`; normalized scores `75, 50, 100`; weighted total `(40×75 + 35×50 + 25×100)/100 = 72.50`. This is a calculation example, not an approved universal rubric.

### 5.2 Assessment completeness and missing evidence

Track count and weighted coverage independently of score. At minimum return:

- `completed_weight_percent`: sum of rubric weights for criteria with a valid assessed rating, divided by 100 × 100.
- `required_criteria_complete`: boolean, false for any required criterion not assessed or approved N/A.
- `insufficient_evidence_count`, `not_assessed_count`, `not_applicable_count`.
- `source_coverage[]` with explicit `COMPLETE`, `PARTIAL`, `UNAVAILABLE`, `NOT_SEARCHED`, `FAILED` (and relevant record counts).
- Qualitative uncertainty (`LOW`, `ELEVATED`, `HIGH`, `NOT_ASSESSED`) and reasons, plus limitations, separate from score and not described as probability absent calibration.

An overall weighted score and final ranking eligibility exist only when every applicable weighted criterion has a valid rating and the approved N/A treatment preserves a valid 100% denominator. Otherwise return score `null` with a reason; the run cannot be marked complete for competitive ranking. Evidence availability does not itself imply criterion failure.

### 5.3 Eligibility gate

Evaluate each mandatory condition deterministically when it can be expressed as a rule; otherwise return `PENDING_VERIFICATION` with an evidence-backed reason. Aggregate per call with strict precedence: any failed mandatory condition → `INELIGIBLE`; otherwise any unresolved mandatory condition → `PENDING_VERIFICATION`; all required conditions passed → `ELIGIBLE`. The implementation must preserve a complete per-condition trace.

Eligibility does not enter the weighted quality formula. An ineligible application cannot receive a positive recommendation or final rank. A pending application receives `FURTHER_ASSESSMENT_REQUIRED` or another stricter approved advisory category and cannot enter final rank.

### 5.4 Ranking and reproducibility

Rank only complete eligible assessments from one call and one approved rubric version. Require a caller to identify a cohort or use an explicitly defined call cohort; persist the cohort membership and query/snapshot version. Sort by exact score descending; equal exact scores share rank. No implicit secondary sort (application ID, date, applicant identity, or recommendation) breaks ties. If an approved tie policy is later adopted, store its policy version and input in the snapshot.

Reproduction requires the same assessment/input snapshots, rubric content hash, eligibility policy, evaluator/model versions, calculation version, numeric precision, and ranking membership. Later model/rubric changes generate new runs/snapshots and never rewrite old output.

## 6. Recommendation contract and safeguards

Example response shape:

```json
{
  "recommendation_id": "rec_...",
  "assessment_id": "assessment_...",
  "category": "FURTHER_ASSESSMENT_REQUIRED",
  "summary": "One or two sentence advisory summary.",
  "rationale": "Explain how approved call criteria and evidence support this category.",
  "supporting_findings": [{"criterion_id": "criterion_...", "finding_id": "finding_..."}],
  "evidence_refs": ["evidence_..."],
  "missing_evidence": [{"criterion_id": "criterion_...", "reason": "Not supplied"}],
  "uncertainty": {"level": "MATERIAL", "reasons": ["Eligibility pending verification"]},
  "limitations": ["Only the listed sources and document versions were assessed."],
  "reviewer_attention": ["Verify the stated lead-institution country."],
  "eligibility": {"outcome": "PENDING_VERIFICATION", "condition_refs": ["eligibility_..."]},
  "evaluator": {"type": "AI", "version": "versioned-id"},
  "human_review": {"status": "PENDING", "review_record_ids": []},
  "advisory_only": true,
  "funding_decision": null
}
```

The example is illustrative, not a claim that the evaluator or source has been implemented. Runtime schema must validate category enum, required explanation/evidence/limitations/attention fields, version presence, valid evidence references, and human-review status. `advisory_only` is always true and no recommendation API field may be interpreted as an award decision. Eligibility failure and incomplete/insufficient assessment constraints are enforced by deterministic service validation after generation, not merely by prompt instructions. Store model/provider/prompt/config version where used; redact sensitive provider errors.

## 7. API and frontend contracts

### 7.1 API endpoint plan

All paths below are proposed under `/api/v1`; exact schemas must be published through FastAPI OpenAPI. Every path requires verified authentication, server-side role authorization and call/application assignment checks, except explicitly public health/documentation routes. `X-User-Role`/`X-User-Id` demo headers are never authority.

| Method and path | Request / response | Authorization and behavior |
|---|---|---|
| `POST /grants/{call_id}/assessment-rubrics` | Draft rubric body → rubric/version | Call-config permission; creates a draft and audit event. |
| `GET /grants/{call_id}/assessment-rubrics` | Optional state/version filters → authorized rubric versions | Call resource read permission. |
| `GET /assessment-rubrics/{rubric_id}/versions/{version}` | None → immutable rubric snapshot | Resource-level authorization. |
| `PATCH /assessment-rubrics/{rubric_id}/versions/{version}` | Draft patch + expected version → updated draft | Draft only; optimistic concurrency; approved version returns `409`. |
| `POST /assessment-rubrics/{rubric_id}/versions/{version}/submit` | Expected version → `IN_REVIEW` version | Call-config permission; validates completeness and weight sum. |
| `POST /assessment-rubrics/{rubric_id}/versions/{version}/approve` | Approval note + expected version → approved snapshot | Explicitly authorized rubric approver, separate from ShakaHive platform administration; full validation and audit. |
| `POST /grants/{call_id}/assessments` | `{application_ids, rubric_version, idempotency_key?}` → `202` run/batch refs | Assessment-start permission for call and each application; only approved rubric; persist accepted work before reporting durable acceptance. |
| `GET /assessments/{assessment_id}` | None → run, versions, eligibility, score/completeness, recommendation and state | Assigned application read permission. |
| `GET /assessments/{assessment_id}/criteria` | None → per-criterion results, evidence refs, missing/uncertainty | Same assignment check; page/limit if needed. |
| `GET /assessments/{assessment_id}/criteria/{criterion_id}` | None → criterion assessment history and evidence | Same assignment check. |
| `GET /grants/{call_id}/assessment-rankings` | `{rubric_version, cohort?, snapshot?}` → snapshot | Grant-call read/ranking permission; may return only the allowed cohort. Incomplete entries excluded and reasons reported. |
| `POST /grants/{call_id}/assessment-rankings` | `{rubric_version, cohort, calculation_version}` → immutable snapshot | Explicit ranking permission; server verifies all membership, eligibility, completeness, and scope. |
| `POST /assessments/{assessment_id}/reviews` | `{action, note?, criterion_id?, rating?, justification?}` → append-only review record | Active assigned reviewer; adjustment requires justification; cannot overwrite AI result. Existing confirm/dismiss/request-review/escalate semantics remain. |
| `GET /assessments/{assessment_id}/reviews` | None → append-only review history | Assignment-scoped read. |
| `POST /applications/{application_id}/final-decisions` | Approved decision vocabulary + rationale/reference → immutable decision record | **Not enabled until final-decision authority, role permission, vocabulary and workflow are separately approved.** Never triggers allocation. |
| `GET /assessments/{assessment_id}/report` | Format/options → authorized report or short-lived authorized download | Assignment-scoped; includes source/uncertainty/disclaimer/version and review history. |

### 7.2 Validation, errors, and authorization

- Use Pydantic request/response schemas, decimal/enum validation, bounded strings/lists/uploads, and explicit nullable fields. Reject unknown rubric states, non-finite/out-of-range scores, missing justifications, unapproved rubric versions, weight totals not equal to 100.00%, inconsistent call/application relationships, unsupported N/A, and invalid evidence references.
- Use repository-standard HTTP errors: `400` malformed/action invalid; `401` missing/invalid identity; `403` authenticated but not permitted; `404` resource absent or intentionally concealed by resource-access policy; `409` stale version/state, unapproved rubric, conflicting snapshot or idempotency conflict; `422` schema/field validation; `202` accepted assessment batch only after durable enqueue is implemented. Do not expose private content, storage keys, model traces, tokens, or exception messages.
- All assessments, list filters, rankings, evidence, documents, reports, audit events and background jobs enforce the same call/application/workspace/assignment scope server-side. Never authorize from UI state, caller-supplied role, IDs alone, or a role label without resource scope.
- Record an idempotency key and request fingerprint for assessment start; duplicate requests return the original accepted operation or a documented conflict without duplicate work.

### 7.3 Frontend integration

Extend the existing dashboard shell, call picker, design tokens, status/message components, responsive styles, API client, typed contracts, and report patterns. The proposal is an **Assessment** workspace:

- **Rubric configuration:** call-specific criterion list, anchors/weights, eligibility separation, remaining total, version state, validation messages, approval identity/time, and change history. Disable run/rank until approved.
- **Application assessment workspace:** reuse `DocumentViewer`, `FindingList`, `EvidenceDrawer`, citation highlighting and review history. Add criterion score/state, explanatory evidence, missing information, uncertainty/coverage, normalized overall score, eligibility gate, and recommendation summary. Display AI proposal and human-adjusted result separately.
- **Call comparison view:** same-call/same-rubric cohort, rank and tied rank, eligibility and completeness gates, score breakdown, snapshot/version, and clear "not a funding decision" notice. Ineligible/incomplete entries appear separately as not rank-eligible, never silently intermixed.
- **Evidence panel:** source/version, method, exact passage/page, relationship, citation validity, coverage/unavailable state, limitations, and link back to document. Use "similarity" wording, never a plagiarism percentage.
- **Reports:** include data origin, call/rubric/run/model/calculation versions, weighted breakdown, eligibility, recommendation, evidence/coverage, human changes/history and disclaimer.

Meet keyboard, screen-reader, responsive, contrast, long-text, empty/error/partial-state, and mobile drawer expectations. Frontend permissions improve usability only; server authorization remains decisive.

## 8. Security, privacy, and auditability

1. **Identity:** implement ADR-001 trusted server-verified principal before any non-public application access. Caller-controlled demo role headers are not authentication and must not reach pilot protection paths.
2. **Resource authorization:** implement ADR-002 deny-by-default policy for every list/detail/document/evidence/report/ranking/review/export/job route. Check workspace, call/application ownership, active reviewer assignment and workflow state at read and mutation time.
3. **Role boundaries:** keep ShakaHive Team Administrator and Grant Administrator separate. Team Administrator's platform account/assignment duties do not imply grant scoring authority; Grant Administrator's call operation does not imply user/role administration. Reviewers receive only assigned resource access and defined review actions. Do not add a role or broad permission to satisfy an endpoint.
4. **Rubric approval and final decisions:** require a named, server-authorized approver under an approved permission matrix. Until the approver policy is settled, keep approval/decision operation unavailable; do not infer privilege from a demo enum.
5. **Immutability:** approved rubrics, completed AI results, run inputs, ranking snapshots, review adjustments and final decisions are append-only/versioned. Any correction creates a linked version. Use transaction/uniqueness/concurrency constraints when persistence is approved.
6. **Sensitive documents:** handle proposal content, extracted text, evidence excerpts, model inputs/outputs, exports and backups as sensitive. Require private storage, scoped downloads, encryption, safe upload/parser limits, retention/deletion policy, provider review, and least-privilege service access before real data.
7. **Error/log redaction:** do not log proposal text, prompts, credentials, private URLs/keys or PII unnecessarily. Return stable codes and generic internal errors; preserve correlation IDs and exception class without sensitive values.
8. **Isolation:** apply the configured single-workspace/resource boundaries from ADR-002 to relational queries, private files, caches, search indexes, reports, logs, jobs and backups. A stored `organization_id` alone does not establish isolation. Before another institution, perform the separate tenant-isolation review required by ADR-002.
9. **Audit:** record rubric transitions, assessment/re-run, evidence provenance, human score adjustments, reviewer actions, ranking/report/export and access denial. Protect audit access and integrity; define retention only under approved policy. Do not invent a retention duration in this specification.
10. **Not a production authorization:** existing role headers, UI hiding, synthetic fixtures, local process-memory state and demo seeds provide no production security guarantee.

## 9. Testing, validation, and operational evaluation

### 9.1 Software test plan

| Level | Required coverage |
|---|---|
| Unit | Rating bounds and anchors; exact 100% weight validation; decimal formula and rounding; distinct zero/not-assessed/insufficient/N/A states; N/A policy; eligibility precedence; score/recommendation gates; tie equality; immutable version transitions; citation/source-version validation; redaction. |
| Integration | Rubric create/edit/approve/supersede lifecycle; application/RFP/input version snapshot; deterministic calculator from stored run inputs; stage/provider partial coverage; assessment/review/audit transactions; retry/idempotency and rerun history; ranking snapshot reproduction. |
| API/authorization | Request validation/error codes; approved rubric only; guessed IDs; cross-call and cross-workspace access; assigned/unassigned reviewers; denied role escalation; document/evidence/report/export reads; adjustment justification; forbidden final-decision route until approved; audit coverage. |
| Frontend | Rubric total/validation and approval state; evidence panel citations/coverage; separate AI/human values; eligibility gate; recommendation warnings; incomplete/unranked states; ties; responsive/keyboard/accessibility; error/partial states. |
| End-to-end/regression | Synthetic call → configure/approve rubric → upload → assess → inspect evidence → review/adjust → compare/rank eligible cohort → generate report; regression of existing requirement extraction, screening, duplication, review, audit and report workflow. |
| Security/reliability | Deny-by-default and horizontal/vertical access cases; private document authorization; stale assignments; payload/file limits; worker restart/retry/idempotency; immutable audit, no sensitive log/error leakage; persistence migration/restore once the approved adapter exists. |

CI conventions are the existing GitHub Actions backend (`ruff check .`, `pytest`) and frontend (`npm run lint`, `npx tsc --noEmit`, `npm test`, `npm run build`) jobs. Add narrowly scoped tests to existing Python and Vitest suites. Do not treat synthetic API tests as security or operational authorization proof.

### 9.2 Assessment quality and evaluation evidence

Before any operational quality claims, define a representative, authorized, expert-labelled evaluation set with source permission/provenance, criterion-specific rating guidance, independent review/adjudication, protected data controls, and disjoint applicant/call splits to avoid leakage. Report sample size, score distribution, missing labels, confidence intervals where appropriate, subgroup/context slices permitted by governance, evaluator/model/rubric versions, baseline and error analysis.

Measure at minimum:

- Criterion-rating agreement with expert adjudication (weighted kappa/ICC as appropriate), exact and within-one agreement, per-anchor confusion matrix.
- Evidence citation validity, evidence sufficiency, correct attribution, criterion coverage, and reviewer usefulness.
- Eligibility per-condition precision/recall, false positive/negative analysis, and pending-verification rate.
- Overall-score agreement/rank correlation against adjudicated scores; rank stability under uncertainty and rubric-version changes.
- Recommendation agreement, unsafe-positive rate when ineligible, further-assessment rate, and reviewer override/disagreement.
- Bias/error slices across lawful, consented, relevant context groups; reviewer burden, time, appeal/clarification and accessibility outcomes.
- Operational latency, failure/partial rate, source coverage, cost and version reproducibility.

Synthetic datasets can test schema, deterministic calculations, state transitions and user flows only. They cannot establish real-world scoring accuracy, ranking validity, fairness or operational acceptability. Current retrieval benchmarks are for retrieval and do not validate this assessment engine.

## 10. Dependencies, assumptions, and limitations

### Existing internal dependencies

- `GrantWorkflowService`, `WorkflowRepository` protocol, Pydantic domain and API models, `WorkflowViews`, current call/application/RFP/document workflows.
- Existing deterministic eligibility, evidence/citation validation, source coverage, similarity/duplication methods, provider boundary, `WorkflowAudit`, `ReviewerDecision`/`ReviewerNote`, and dashboard report patterns.
- Next.js dashboard/API client/types, `DocumentViewer`, `FindingList`, `EvidenceDrawer`, CSS tokens and frontend test setup.
- Python 3.11+, FastAPI, Pydantic, PDF/DOCX extraction dependencies; optional `.[ml]` for model-backed embedding/reranking; Node 20 CI and current npm toolchain.

### External and governance dependencies

- An approved funding-call source and an authorized human to define/approve each call's criteria, ratings, weights, applicability/N/A treatment and any recommendation bands.
- Trusted identity and a reviewed server-side permission/assignment matrix under ADR-001/002; named rubric approver; explicit data owner authorization.
- A selected and implemented durable repository/migration, private object-storage and durable-job approach under the existing ADR workflow. PostgreSQL/pgvector is documented as target/planned, but no workflow adapter exists; do not claim it is active.
- Human expert-labelled, representative, authorized evaluation datasets and adjudication protocol.
- Model/provider versions, evaluation evidence, data-processing terms and explicit approval before application content is sent to any external model.
- Institutional approvals, data-sharing terms, retention, privacy/security review, deployment environment and recovery controls before real applicant submissions.

### Limitations and unresolved assumptions

- This repository does not show a production authorization system, persistent workflow database, durable queue, private object-storage lifecycle, calibrated assessor, approved rubric, or competitive ranking/recommendation implementation.
- The state of the sample data, current rules and existing evaluation are synthetic or prototype-level; they are not evidence of operational accuracy.
- RIGMS is a placeholder requiring authorized API specification and access. No RIGMS integration or institutional authorization is claimed.
- OpenAlex is optional and limited to retrieved records/abstracts; other source adapters are not proof of source access or complete search coverage. Scanned-PDF OCR is unavailable.
- Recommendation thresholds, criterion N/A weight behavior, tie-break policy, final-decision authority/vocabulary, audit/data retention periods, supported assessor models and human adjudication workflow remain unresolved until specifically approved.
- The organization/workspace model is the controlled single-institution test direction in ADR-002, not implemented multi-institution isolation.
- Current review actions may be reused, but score-adjustment UI, permissions and durable version history require new implementation and tests.

## 11. Conflicts and precedence

- FPDR-001 extends the product beyond current MVP documentation describing signal-based screening; it does not replace existing screening stages or imply those new capabilities exist.
- ADR-001 and ADR-002 are existing canonical records and remain unchanged. Their documented statuses still require technical/team decisions; this specification does not convert those records into implemented controls.
- The proposed modular services, schemas and endpoints are new engineering work, not existing components. Persistence and deployment technology must remain within the reviewed architectural baseline and any subsequent ADR.
- If an endpoint, role, data rule or algorithm conflicts with FPDR-001, FPDR-001 prevails. If a technology or access design conflicts with an ADR, stop that implementation and resolve it through the ADR process rather than silently changing the record.

## 12. Implementation roadmap

Each workstream is independently reviewable; implementation should be delivered through separate pull requests linked to issues, with no bundled migration or unfinished feature release. File paths below are likely touchpoints, not a mandate to change every file.

### 1. Assessment foundation and data contracts

- **Objective:** Establish typed immutable rubric/run/evidence/review/audit contract boundaries without activating assessment behavior.
- **Dependencies:** FPDR-001; this specification; ADR-001/002 review; persistence/identifier decisions before durable schema.
- **Likely files/components:** `services/grant_workflow/models.py` or a focused assessment domain module; `apps/api/schemas/`; `apps/web/lib/types.ts`; `services/grant_workflow/repository.py`; tests and OpenAPI.
- **Deliverables:** Contract enums/models, ID/version conventions, lifecycle transitions, data-flow diagram/update and explicit migration proposal only after database decision.
- **Tests:** Contract validation, cross-reference checks, version immutability and serialization compatibility.
- **Acceptance:** All nine conceptual contracts in §4 have required/optional fields and validation; no invented production persistence/auth claim; existing API types/tests remain compatible.
- **Risks:** Conflating existing `RfpCriterion` with quality criterion; migration against unselected database.
- **Completion:** Reviewed contract PR and any required ADR/issues approved; no schema migration unless separately authorized.

### 2. Call-specific rubric management

- **Objective:** Configure, version, validate and approve call-specific rubrics.
- **Dependencies:** Workstream 1; trusted identity, authorization and named approver policy; call-specific rubric governance.
- **Likely files/components:** Assessment rubric service and API routes/schemas; call dashboard pages; API client/types; audit integration.
- **Deliverables:** Draft/edit/submit/approve/supersede lifecycle; exact 100% validator; explicit anchors, eligibility separation, applicability/N/A rule; immutable approved snapshot.
- **Tests:** Weight under/over/precision edge cases; draft vs approved; edit produces new version; unauthorized/stale approval denied; scope checks.
- **Acceptance:** No operational assessment can start against draft; approved content immutable; all scored weights total exactly 100.00%; every approved version retains actor/time/hash.
- **Risks:** Unapproved criteria or weights mistaken for standard; ambiguous N/A semantics.
- **Completion:** Rubric workflow passes authorization and audit suite; product owner approves call-specific rubric before operational use.

### 3. Evidence-backed criterion assessment

- **Objective:** Produce per-criterion proposals with attributable evidence, missing evidence, limitations and uncertainty.
- **Dependencies:** Workstreams 1–2; Evidence Aggregator; authorized sources and assessor/model decision; versioned source input.
- **Likely files/components:** `services/grant_workflow/screening/`, `services/evidence/`, provider/source coverage modules, new assessment service, schemas, `DocumentViewer`/`EvidenceDrawer`.
- **Deliverables:** Evidence aggregation contract; criterion result status; evaluator adapter; exact citation provenance; source coverage and failure disclosure.
- **Tests:** Valid/invalid citation, insufficient evidence distinct from 0, no-source/unavailable states, prompt/model version, sensitive error redaction, partial evaluator failure.
- **Acceptance:** Every scored proposal traces to source/version and model/evaluator version; missing evidence never becomes 0; similarity behavior remains separate and cannot emit plagiarism percentages/verdicts.
- **Risks:** Excerpt hallucination or citation drift; unapproved external data flow; uncalibrated model scores presented as fact.
- **Completion:** Reviewers can inspect and verify evidence end-to-end; evaluation design and model limitations are documented before claims.

### 4. Overall scoring and comparative ranking

- **Objective:** Implement deterministic weighted scoring, completeness gates, eligibility restrictions and reproducible same-call ranking snapshots.
- **Dependencies:** Approved rubric; workstreams 1–3; eligibility rule mapping; persistence needed for immutable snapshots.
- **Likely files/components:** deterministic calculator and ranking modules; assessment/run persistence contract; API ranking routes; call comparison view; tests.
- **Deliverables:** Pure calculator, missing/N/A handling, complete/eligible filter, exact-tie behavior, immutable ranking snapshot with source versions.
- **Tests:** Formula example 72.50; 0 vs missing; weights; eligibility ineligible/pending exclusions; incomplete exclusion; shared ties; reproducibility/rounding.
- **Acceptance:** Only complete eligible same-call/same-rubric applications rank; no hidden imputation or tiebreak; old snapshots reproduce exactly; ranking is visibly not a funding decision.
- **Risks:** Denominator changes, display rounding causing false ties, unsupported N/A renormalization.
- **Completion:** Deterministic suite and stored-snapshot replay pass; authorized rubric and policy for N/A is explicit.

### 5. Preliminary AI recommendations

- **Objective:** Generate constrained advisory recommendations linked to criterion findings and evidence.
- **Dependencies:** Workstreams 2–4; approved call-specific mapping/thresholds or a no-threshold fallback; evaluator governance.
- **Likely files/components:** recommendation service/schema, assessment endpoint/read models, reports and workspace UI, model evaluation assets.
- **Deliverables:** Four-category contract, eligibility/completeness guards, evidence and limitations, model version, mandatory advisory marker.
- **Tests:** Four enum values; fail-eligibility cannot produce positive; incomplete evidence forces further assessment; invalid evidence refs rejected; no funding decision fields.
- **Acceptance:** Every recommendation includes rationale/evidence/missing evidence/uncertainty/limitations/attention/model version/human-review state; cannot be interpreted as a funding decision.
- **Risks:** Unapproved cutoff values; plausible-sounding unsupported explanation; recommendation leakage into allocation decisions.
- **Completion:** Contract and expert-reviewed evaluation protocol pass; call-specific recommendation bands separately approved before operational use.

### 6. Human review and audit workflow

- **Objective:** Add assigned-reviewer assessment actions and justified adjustments while preserving original AI outputs and immutable history.
- **Dependencies:** Workstream 1; ADR-001/002 controls; role/assignment policy; run/evidence contracts.
- **Likely files/components:** `services/human_review/`, `services/grant_workflow/service.py`, audit model/service, review routes/schemas, `DecisionPanel`/`EvidenceDrawer`.
- **Deliverables:** Accept/challenge/adjust/request clarification/escalate/notes/confirm/dismiss; append-only adjustment records; before/after view; authorization and audit.
- **Tests:** Justification required; wrong assignment/role denied; original AI record remains unchanged; action lifecycle; append-only history; audit redaction.
- **Acceptance:** Human reviewer can act only in assigned scope; adjustments are attributed and justified; AI and human results remain separately retrievable; existing reviewer workflow is not broken.
- **Risks:** Legacy/demo roles mistaken as approved role mapping; process-memory audit lost at restart.
- **Completion:** Authenticated resource-scoped review and durable audit controls verified before any real proposal use.

### 7. Assessment workspace and reports

- **Objective:** Present rubric, criterion evidence, score, eligibility, recommendation, ranking, review history and limitations coherently.
- **Dependencies:** Workstreams 2–6; frontend contracts/API; approved role policy.
- **Likely files/components:** `apps/web/app/dashboard/`, `components/workflow/`, `lib/api.ts`, `lib/types.ts`, dashboard/workspace styles, frontend tests.
- **Deliverables:** Rubric builder, application assessment workspace, same-call comparison and tied rank view, evidence panel, versioned report.
- **Tests:** Component/Vitest for all states; API tests; keyboard/screen-reader/responsive checks; report provenance and no-funding-decision notice.
- **Acceptance:** Existing design system and navigation reused; incomplete/not-searched/tied/ineligible states explicit; source passages navigable; user actions available only when allowed by backend.
- **Risks:** UI simplification obscures uncertainty or lets sorting imply allocation.
- **Completion:** User-journey acceptance and accessibility checks pass; no frontend-only authorization claim.

### 8. Validation, governance, and production readiness

- **Objective:** Establish quality evidence, data approvals, security, operations, release gates and monitored evaluation.
- **Dependencies:** Workstreams 1–7; production authentication/persistence/jobs/storage and environment decisions; authorized institutional data and experts.
- **Likely files/components:** `data/evaluation/`, `ml/evaluation/`, `tests/`, `.github/workflows/`, governance and pilot documentation, deployment configuration only under approved decisions.
- **Deliverables:** Expert-labelled evaluation dataset/protocol; bias/error analysis; security/privacy review; retention/provider approvals; migration/backup/recovery; release checklist and go/no-go.
- **Tests:** Full regression, API/E2E/security/authorization, reliability/recovery, evaluation reproducibility and staging smoke test.
- **Acceptance:** Real-world quality claims only supported by representative authorized evaluation; all production gates in existing pilot/security docs are evidenced; no critical/high security issue silently waived; stakeholder authorization and sign-off recorded.
- **Risks:** Synthetic results misrepresented; unavailable institutional integrations treated as coverage; premature launch with in-memory/demo boundaries.
- **Completion:** Authorized decision owners sign a readiness decision; unfinished functionality remains disabled; no deployment is implied by this documentation.

## 13. Definition of done for the assessment capability

An implementation slice is complete only when its workstream acceptance conditions are demonstrated, tests and review pass, resource authorization and failure behavior are covered, evidence/version/audit records are inspectable, documentation and known limitations are updated, and the linked issue/PR records the approving owner. The capability is not production-ready until Workstream 8 and the existing authentication, authorization, persistence, secure-storage, durable-job, privacy, recovery, and pilot-readiness gates are satisfied.
