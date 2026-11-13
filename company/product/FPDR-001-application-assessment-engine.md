# FPDR-001: Application Assessment Engine

- **Document ID:** FPDR-001
- **Owner:** ShakaHive Founder / Product Decision Owner
- **Status:** Approved
- **Last updated:** 13 November 2026
- **Approval status:** Founder-approved product direction; approval recorded in the task brief
- **Version:** 1.0
- **Related decisions:** `docs/architecture/decisions/ADR-001-authentication-and-session-model.md`; `docs/architecture/decisions/ADR-002-authorization-and-organization-isolation.md`
- **Related documents:** `company/product/mvp-definition.md`; `docs/grant-workflow.md`; `docs/architecture/overview.md`; [TAIS-001](../../docs/architecture/TAIS-001-application-assessment-engine.md)
- **Related work:** Application Assessment Engine implementation roadmap in TAIS-001

## Change history

| Version | Date | Change | Approval |
|---|---|---|---|
| 1.0 | 13 November 2026 | Establish the approved product behaviour and governance boundaries for the Application Assessment Engine. | Founder-approved |

## 1. Authority and scope

This Founder Product Decision Record (FPDR) is authoritative for approved ShakaHive Application Assessment Engine product behaviour. The Technical Architecture & Implementation Specification (TAIS-001) translates these decisions into an engineering blueprint and is subordinate to this record and existing canonical architectural decisions.

This decision approves the product direction and required behaviour. It does not assert that the capability is implemented, validated, production-ready, authorized for institutional data, or connected to an external funding system. Implementation proposals, technical choices that remain open, and assumptions that need further approval are explicitly identified in TAIS-001. No implementation may weaken the requirements in this record.

The assessment engine extends the existing AI-assisted grant-screening workflow into an evidence-driven research funding assessment platform. It evaluates an application against the requirements and approved evaluation criteria of its specific funding call. It supports human judgment; it does not allocate or award funding.

## 2. Product purpose and assessment model

For each application and funding call, the engine must support:

- A separate assessment result for every applicable criterion.
- A weighted overall quality score, normalized for presentation on a 0–100 scale.
- Comparative ranking only within the same funding call and approved rubric version.
- Evidence-backed explanations, source provenance, and source-coverage information.
- Explicit completeness and uncertainty indicators.
- A preliminary AI recommendation with rationale and limitations.
- Mandatory human review before an assessment is treated as reviewed or used in a consequential process.

Eligibility is a distinct gate, not a component of the weighted quality score. A strong quality score cannot override a failed mandatory eligibility condition.

## 3. Call-specific rubric governance

1. Every funding call may have its own criteria, definitions, weights, applicability rules, and approved recommendation bands.
2. Authorized users configure criteria and weights for that call. Proposed weights in prior discussions or examples are illustrative only; they are not universal defaults.
3. Before operational use, an authorized human must approve the complete rubric version. A draft or unapproved rubric cannot be used to produce an operational score or ranking.
4. The weights of applicable scored criteria in an approved rubric version must total exactly 100%. Validation uses decimal arithmetic and rejects a version whose total is not exactly 100.00%.
5. An edit to any approved rubric creates a new version. Existing runs and ranking snapshots remain linked to the exact version used and are not rewritten.
6. Each criterion must identify whether it is scored, mandatory for eligibility, informational, or otherwise handled by an explicitly approved rule. Eligibility requirements do not receive quality-score weights.
7. If a criterion is not applicable to an individual application, its status and the approved treatment of its weight must be explicit in the rubric. The engine must not silently redistribute weights or treat an unapproved applicability decision as complete.

## 4. Eligibility and quality scoring

Eligibility outcomes are exactly:

- **Eligible**
- **Ineligible**
- **Pending verification**

Eligibility is evaluated separately from the weighted quality score. Each mandatory eligibility condition must have a rule, an outcome, and traceable evidence or a disclosed reason that it remains pending. Missing or ambiguous evidence yields **Pending verification**, not an inferred failure or pass.

An application with a failed mandatory eligibility condition must not receive a positive preliminary recommendation because of its quality score. It must not be included in the final competitive ranking. Pending eligibility is also insufficient for final competitive ranking.

### Criterion rating scale

The proposed quality-criterion rating scale is 0–4:

| Rating | Interpretation when the criterion has been assessed with sufficient evidence |
|---:|---|
| 0 | Does not meet the criterion; the evidence was reviewed and supports this conclusion. |
| 1 | Meets only a small portion; major substantiated gaps remain. |
| 2 | Partially meets; material gaps or limitations remain. |
| 3 | Meets the criterion as specified. |
| 4 | Exceeds the criterion; evidence supports performance materially beyond the stated requirement. |

The corresponding normalized presentation is `rating × 25`, producing 0, 25, 50, 75, or 100. A score of zero is a valid assessed rating only when sufficient evidence was reviewed and supports the rating. It is not a placeholder for absence, uncertainty, or non-assessment.

These are proposed rating anchors, not a universal interpretation of every funding call. An approved call rubric must provide criterion-specific anchors where the generic anchors are insufficient.

The following states are distinct and must remain visible:

- **Zero score:** assessed with sufficient evidence; the recorded rating is 0.
- **Not assessed:** no assessment has been completed.
- **Insufficient evidence:** the reviewer or evaluator cannot responsibly rate the criterion from available evidence.
- **Not applicable:** an approved rubric rule establishes that the criterion does not apply to this application.

Missing, unreadable, inaccessible, or unavailable evidence must never silently become zero or a completed assessment. A numeric score is not produced for an unassessed or insufficient-evidence criterion. A non-applicable criterion and its effect on the denominator must follow the approved rubric; no silent weight renormalization is permitted.

## 5. Similarity and duplication

- Text similarity is not plagiarism.
- A duplication or similarity risk is not proof of misconduct.
- Plagiarism conclusions require contextual human review.
- Every similarity finding must provide traceable source passages and provenance, including which passages were compared, source identity/version, method, and relevant coverage limitations.
- Similarity values describe the configured comparison method only. They must never be labelled or displayed as a plagiarism percentage or probability of misconduct.
- An unavailable, unauthorized, or unsearched source is not a no-match result.

## 6. Comparative ranking

Final competitive ranking must:

1. Compare applications only within the same funding call and same approved rubric version.
2. Respect mandatory eligibility requirements; only eligible applications may enter a final competitive ranking.
3. Exclude applications whose assessments are incomplete, have insufficient evidence for a required scored criterion, or are otherwise not assessable under the approved rubric.
4. Preserve equal scores as ties unless a separately approved tie-breaking rule applies. Display rounding must not manufacture or remove a tie.
5. Retain an immutable ranking snapshot linked to its exact assessment runs, application versions, rubric version, eligibility results, and calculation version.
6. Be described as comparative assessment information, never as an award, funding allocation, or final decision.

No tie-break order or funding allocation policy is approved by this record.

## 7. Preliminary AI recommendation

The engine produces exactly one preliminary category:

1. **Strongly aligned**
2. **Aligned with conditions**
3. **Further assessment required**
4. **Not currently aligned**

Every recommendation includes a concise summary, rationale, supporting findings, evidence references, missing evidence, uncertainty and limitations, reviewer-attention points, the evaluator/model version, and human-review status. A recommendation is advisory and is not an eligibility determination, reviewer decision, funding decision, or award.

Eligibility failure prevents the first two positive categories. Pending eligibility, incomplete criteria, insufficient evidence, or materially unresolved uncertainty must produce **Further assessment required** unless an approved rubric rule requires a more restrictive advisory result. Recommendation score thresholds or mappings are call-specific and require approval; this record establishes no universal cut-offs.

## 8. Human authority and governance

Human review is mandatory. Within their authorized call/application assignment, reviewers must be able to:

- Accept an assessment.
- Challenge a finding.
- Adjust a criterion score and record a justification.
- Request clarification.
- Escalate an issue.
- Record review notes.
- Submit and confirm or dismiss findings using the existing approved reviewer workflow.

Every human action is attributed, timestamped, scoped to the authorized resource, and retained in review history. A human adjustment never overwrites the original AI assessment; both versions and the relationship between them remain inspectable.

The distinction between **ShakaHive Team Administrator** and **Grant Administrator** is preserved exactly as established in ADR-002. This FPDR creates no roles, grants no platform-administration privilege to a Grant Administrator, and does not merge platform administration with grant operations. An individual holding both roles requires explicit assignment of each. Reviewer assignments and resource scope remain server-enforced.

Recording an external or institutional final decision is separate from making a score or recommendation. The assessment engine never makes that decision. The authority, outcome vocabulary, and access policy for recording such a decision must follow separately approved workflow policy; no new role or funding authority is implied here.

## 9. Responsible AI principles

All assessment behaviour must preserve:

- **Evidence traceability:** material findings link to the source passages that support or contradict them.
- **Source provenance:** identify source, version, retrieval or extraction method, and coverage where applicable.
- **Explainability:** expose the criterion, rating rationale, calculation, and limitations in reviewer-understandable form.
- **Uncertainty disclosure:** distinguish missing, insufficient, unavailable, not searched, and uncertain states.
- **Bias evaluation:** evaluate performance and error patterns across relevant, lawfully available groups and contexts before operational claims; do not infer protected attributes.
- **Human accountability:** authorized people remain accountable for review and decisions.
- **Versioned assessments:** retain rubric, input, evaluator/model, and calculation versions.
- **Auditability:** preserve who performed each action, when, on which resource/version, and what changed.
- **No autonomous funding decisions:** no score, ranking, or AI output awards, rejects, or allocates funding.
- **No unsupported coverage or accuracy claims:** do not imply source completeness or model accuracy without representative, authorized evaluation evidence.

## 10. Decision boundaries and approval required

**Approved product decisions in this record:** purpose, call-specific approved rubrics, separated eligibility and quality scoring, rating/status distinctions, evidence and similarity safeguards, ranking constraints, recommendation categories and advisory status, mandatory review, immutable AI history, role separation, and responsible-AI requirements.

**Implementation proposals, not additional product decisions:** internal service boundaries, API and data schemas, database mapping, score calculation representation, UI layout, observability, and test design described by TAIS-001.

**Require separate approval before implementation or operational use:** any universal score weights or recommendation thresholds; the call-specific rubric's criteria, weights, rating anchors and N/A treatment; an external final-decision vocabulary or delegated authority; any new privilege; storage/retention periods for confidential data; external model/provider processing of applications; real-world model performance claims; new institutional integrations; and any change to existing ADRs or this FPDR.

## 11. Review triggers

Revisit this record only through a reviewed product decision if stakeholders change the intended use, rubric governance, eligibility boundary, rating semantics, ranking scope, human authority, role separation, or prohibition on autonomous funding decisions. Evidence of systematic bias, unsafe reviewer use, or a material gap in traceability also triggers review. Existing runs and audit records remain immutable when policy changes.
