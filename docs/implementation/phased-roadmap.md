# Phased Implementation Roadmap

## Decision gates

No P0 implementation begins around institutional data until:
- FPDR-002 is located or replaced by a canonical applicant-intake decision.
- ADR-001 authentication mechanism and account lifecycle are approved.
- ADR-002 permission matrix and reviewer assignment policy are approved.
- The targeted data classification, retention and provider terms are approved.

## Phase 0 — Governance and baseline

**Objective:** Establish canonical decisions and an evidence-backed foundation.

- Complete route, model, persistence and authorization inventory.
- Locate or approve FPDR-002.
- Revise ADR-001 and ADR-002 through normal decision process.
- Approve tenant/workspace and programme-manager scope.
- Define rubric governance and call-specific approval owner.
- Create missing ADR-003 through ADR-006 decisions.
- Do not tune operational thresholds.

**Exit:** approved decisions, named roles/owners, threat model, ADR inventory and this audit baseline.

## Phase 1 — P0 foundations

**Objective:** secure and durable existing grant workflow.

- Trusted auth and server-side identity.
- RBAC/resource/assignment enforcement.
- PostgreSQL adapter/migrations or another decision-resulting persistence adapter.
- Private document storage.
- Durable queue/worker.
- Staging, observability, backup/restore and incident procedures.
- Applicant submission foundation and immutable snapshots once FPDR-002 is approved.

**Parallel:** route and negative authorization tests; data lifecycle policy; synthetic E2E suite.

**Exit:** no in-memory critical state or thread-pool critical path; negative authorization/document/job/restore tests pass.

## Critical-path reconciliation

- Security and durable data foundations are the prerequisite for any institutional or applicant workflow. Authentication, resource authorization, PostgreSQL or the decision-resulting persistence adapter, private document storage, durable jobs and recovery must complete before real submission data is handled.
- FPDR-001 assessment contracts may be prepared in parallel with foundations. Contract design, rubric lifecycle, eligibility/quality separation and test models do not require a persistent database or deployed provider, but operational scoring/ranking must wait for approved ADR-001/002, persistence and call-specific rubric decisions.
- Purpose-overlap and textual plagiarism/plagiarism-source engines remain separate. They share extraction, retrieval and evidence primitives but must not share outcome labels or misconduct thresholds.
- Applicant intake is blocked on recovery or approval of canonical FPDR-002 requirements. The implementation can prepare neutral data contracts, but status values, ownership and submission behavior must not be invented.
- Funding overlap remains P2 and requires authorized award/commitment data. It is not inferred from proposal text.
- P2 award/finance/impact and P3 repository/STI/multi-institution capabilities remain outside the immediate MVP and require institutional authority and data access.

## Phase 2 — Assessment engine MVP

**Objective:** implement FPDR-001 on the hardened workflow.

- Rubric draft/in-review/approved lifecycle.
- Criterion type, weight, applicability and 0–4 anchors.
- Eligibility separate from quality.
- Criterion assessment and evidence sufficiency states.
- Deterministic weighted score.
- Advisory recommendation.
- Human adjustment history.
- Immutable ranking snapshots.
- Assessment report.

**Exit:** synthetic end-to-end assessment passes FPDR invariants; no real-world accuracy claim; mandatory human review.

## Phase 3 — Research integrity

**Objective:** operationalize purpose, plagiarism and unified integrity evidence.

- Purpose-overlap structured profiles and disposition.
- Source snapshot, retrieval and provenance.
- Quote/citation/boilerplate classification.
- OpenAlex/Gemini or other approved source adapter.
- Unified integrity reporting.
- Clarifications and appeals.

**Exit:** authorized label set, expert review, source precision/coverage, and no unsupported coverage claims.

## Phase 4 — Funding-to-impact

**Objective:** add award/contract and financial/milestone operations after assessment and authority decisions.

- Award/contract and final-decision authority.
- Funding commitment and overlap model.
- Disbursement and ledger.
- Milestones and progress reports.
- Closeout and impact evidence.

**Exit:** institutionally approved workflows and audited financial evidence.

## Phase 5 — Research Intelligence expansion

**Objective:** selectively expand repository and STI capabilities.

- Research repository/discovery reconciliation.
- IP/commercialization.
- STI policy analytics.
- Second institution only after separate tenant isolation.

**Exit:** approved source/data policy and representative validation.
