# Prioritised Implementation Backlog and Dependency Map

**Status:** Proposed backlog; it does not revise FPDR-001, TAIS-001 or the existing ADRs.

## P0 — Foundations and immediate product

| ID | Objective / scope | Reuse | Add or modify | API changes | Data changes | Security | Dependencies | Tests | Acceptance criteria | Owner role | Effort | Blocking decision |
|---|---|---|---|---|---|---|---|---|---|---|---:|---|
| P0-01 | Select and implement trusted identity | `apps/api/main.py`, `services/auth/demo_auth.py`, demo auth tests | Replace demo principal/session boundary with accepted provider; isolate test auth | `/api/v1/auth/*` replacement/session contract | User/session/invitation tables or provider mapping | Secrets, cookies/bearers, CSRF, revocation, MFA policy | ADR-001 revision/approval; provider technical evaluation | `tests/test_demo_auth.py`, `tests/test_workflow_api.py::test_demo_sessions_reject_forged_headers`; add expiry/revocation/invalid issuer tests | No protected route trusts headers; missing/expired/revoked identity denied | Full-Stack Developer | XL | Authentication provider/mechanism and named admin roster |
| P0-02 | Implement resource-level authorization | `apps/api/dependencies.py`, service permission checks | Central policy contract and assignment model | Every protected route; no anonymous read of private resources | User, role, workspace, membership, reviewer assignment | Deny by default; assignment and stale assignment enforcement | P0-01; ADR-002 revision/approval | Horizontal/vertical/cross-call/cross-document/export/job tests | Cross-resource and unassigned access denied; audit of privileged changes | Full-Stack Developer | XL | Role/permission matrix and reviewer delegation |
| P0-03 | Durable workflow persistence | `WorkflowRepository`, `InMemoryWorkflowRepository`, Pydantic models | Approved SQL repository adapter and migrations | None if contract preserved; correct 404/409 semantics | Call, RFP, applications, documents metadata, runs, findings, reviews, audit | Transactions, tenancy scoping, encryption, backup | ADR-003; P0-02 | Restart, migration, constraint and rollback tests | Workflow survives process restart and rollback | Full-Stack Developer | XL | Persistence/migration ADR |
| P0-04 | Private document storage and lifecycle | `services/ingestion/document.py`, `grant_workflow/documents.py` | Private object/file adapter and lifecycle service | Scoped downloads and metadata APIs | Opaque object keys, hashes, versions, retention/deletion | Signatures, limits, malware/archive controls, short-lived access | ADR-005; P0-02/P0-03 | Upload, traversal, limit, stale assignment and deletion tests | Unauthorized or revoked-user downloads denied; originals/derived artifacts deleted by policy | Full-Stack Developer | XL | Storage provider and retention policy |
| P0-05 | Durable screening jobs | `services/grant_workflow/jobs.py`, `screening/orchestrator.py` | Approved queue/worker and job state adapter | Durable accepted `202`; job status and replay/admin APIs | Job, attempt, idempotency, progress and terminal result | Actor/workspace/resource checks, bounded retry, resource limits | ADR-004; P0-02/P0-03 | Restart, duplicate, timeout, crash, retry and replay tests | No lost/duplicate work after restart; terminal state durable | Full-Stack Developer | XL | Queue/worker decision |
| P0-06 | Complete operations baseline | Docker, CI, deployment docs | Staging, observability, backup/restore, incident/runbooks | Health/readiness and protected status endpoints | Backup and secret inventory | Secret management, least privilege, privacy logs | ADR-006; P0-03/P0-04/P0-05 | Deployment, restore, alert and smoke tests | RPO/RTO, restore and rollback evidence pass | Platform Developer | L | Environment/topology/retention decisions |
| P0-07 | FPDR-002 applicant intake decision and implementation | `Applicant`, `Application`, `ApplicationDocument`, demo applicant UI | Canonical decision, draft/submission/receipt/document/version/withdrawal/clarification workflow | Proposed `/applicant/calls`, `/applications`, `/applications/{id}/draft`, `/submit`, `/withdraw`, `/clarifications` | Draft/immutable submission snapshots, ownership, receipt, document version, state history | Owner-only access, secure downloads, immutable snapshots | P0-01/P0-03/P0-04; FPDR-002 governance | Add API/workflow/e2e tests | Submit/receipt/snapshot/withdraw/clarify journeys pass | Full-Stack Developer | XL | Locate canonical FPDR-002 or approve replacement |
| P0-08 | Assessment foundation: rubric and eligibility contracts | `RfpCriterion`, `services/grant_workflow/screening/eligibility.py`, Pydantic/API patterns | Separate assessment domain, immutable rubric/run/criterion contracts | `/grants/{call_id}/assessment-rubrics/*`, `/assessments/*` proposed in TAIS-001 | Rubric, criterion, assessment run, criterion assessment, eligibility result | Rubric approval privilege, resource authorization | TAIS-001; P0-01/P0-02/P0-03 | Contract/calculation/immutability tests | Weight, applicability, eligibility and state invariants pass | Full-Stack + Platform | XL | Rubric approver, call-specific content and N/A policy |

## P1 — Research integrity and intelligent review

| ID | Objective / scope | Reuse | Proposed changes | API changes | Data | Security | Dependencies | Tests | Acceptance | Owner | Effort | Blocking decision |
|---|---|---|---|---|---|---|---|---|---|---|---:|---|
| P1-01 | Structured purpose-overlap service | Duplication retrieval, evidence, `FindingEvidence`, novelty | New `services/purpose_overlap/` and ML profile service | Purpose-overlap screening/report/disposition routes | Dimension profile, candidate, explanation, disposition | Same-call/workspace assignment; source snapshots | P0-02/P0-03; structured field schema | Synthetic same-purpose/different-purpose/replication/follow-on tests | Dispositions and evidence passed for all 10 demo scenarios | AI/ML + Full-Stack | XL | Sector field taxonomy and expert labels |
| P1-02 | Source-corpus and plagiarism provenance | `services/plagiarism`, `services/research_sources`, evidence citations | Snapshot/source registry; institutional adapter seam | Search/check/report endpoints with coverage and snapshot refs | Source identity, snapshot, URL/hash/date/version, match offsets | Private authorized source access; provider redaction | P0-04; external authorization | Mocked adapter + live approved-source integration tests | Traceable match, unavailable and no-match distinct | AI/ML + Full-Stack | L | Institutional corpus authorization |
| P1-03 | Quote/citation and boilerplate handling | Text normalization, public/plagiarism overlap | Passage type classifier and citation parser | Match metadata: quoted/cited/uncited/boilerplate | Match provenance and disposition | No proof of misconduct | P1-02; expert labels | `similarity_benchmark.json` expansion and expert cases | Citation/quote/boilerplate negatives pass | AI/ML | M | Citation policy |
| P1-04 | Complete assessment scoring/recommendation/ranking | Existing screening evidence, TAIS contracts | Calculator, eligibility assessor, recommendation and ranking services | TAIS-001 proposed endpoints | Rubric snapshot, run, criterion, recommendation, ranking snapshot | Approver/reviewer roles and immutable audit | P0-02/P0-03/P0-08 | Unit/API/e2e/tie/rerun tests | FPDR invariants demonstrably pass | Full-Stack + AI/ML | XL | Recommendation/tie/N/A policy |
| P1-05 | Unified integrity report | Existing findings, reviewer decisions, report views | Integrity aggregation and export | One integrity/report route plus source-specific detail | Cross-finding references/dispositions | Authorized export/audit | P1-01/P1-02/P1-04 | Report export/disposition tests | Separates purpose, text, plagiarism, funding and unresolved evidence | Full-Stack | L | Reporting policy |
| P1-06 | Clarifications, appeals and notifications | Reviewer actions and notes | Notification/clarification/appeal workflows | Applicant and reviewer scoped endpoints | Thread, message, deadline, disposition | Ownership/assignment and delivery audit | P0-07/P0-02 | Message, expiry, escalation and denied access tests | Applicant can respond; appeal/human resolution is auditable | Full-Stack | L | Appeal authority, delivery channels |

## P2 — Funding-to-impact operations

| ID | Objective | Reuse | Add | Data/API | Security | Dependencies | Tests | Acceptance | Owner | Effort | Blocker |
|---|---|---|---|---|---|---|---|---|---|---:|---|
| P2-01 | Award and contract management | Application/call, human decisions, audit | Award/contract model and controlled final-decision record | Award/contract APIs, snapshot | Human authority and role | P1-04/P0-02 | State, immutability, access tests | Human creates award/contract; no AI auto-funding | Full-Stack | XL | Final decision authority/vocabulary |
| P2-02 | Funding-overlap detection | Project archive, funding fields, evidence | Separate commitment and overlap service | Commitment/import/check APIs | Authorized award data and resource access | P2-01 or equivalent institution award data | Synthetic different-wording and period/budget/deliverable tests | Structured overlap report with source and uncertainty | AI/ML + Full-Stack | XL | Funding data access |
| P2-03 | Disbursement and budget tracking | Audit/report patterns | Ledger, disbursement and reconciliation | Ledger APIs | Financial read/write roles and audit | P2-01/P2-02 | Ledger, reversal and reconciliation tests | No duplicate/discrepant transaction accepted silently | Full-Stack | XL | Finance system policy |
| P2-04 | Milestone/progress monitoring | NCST indicators, evidence chain, report | Project report and milestone evidence workflow | Report/submission/review APIs | Award/project assignment | P2-01/P0-04 | Versioned report and evidence tests | Progress/variance has immutable source evidence | Full-Stack + AI/ML | L | Institutional monitoring indicators |
| P2-05 | Closeout/impact reporting | Lifecycle models, evidence/report/audit | Closeout, outputs, outcomes and commercialization evidence | Closeout APIs/report | Project/award assignment | P2-01/P2-04 | End-to-end closeout tests | All required evidence and final human approval recorded | Full-Stack | XL | Closeout criteria |

## P3 — Research Intelligence expansion

P3-01 repository/discovery reconciliation; P3-02 IP/commercialization; P3-03 STI analytics/policy intelligence; P3-04 second-institution/multi-tenant onboarding. Each remains blocked until its institutional data, privacy and architecture decision is approved. Reuse publication reconciliation, entity resolution and evidence components, but do not claim authorized coverage.

## Critical path

1. Governance: locate/approve FPDR-002 and revise/approve ADR-001/ADR-002 from proposed status.
2. P0-01/P0-02/P0-03/P0-04/P0-05/P0-06 foundations.
3. P0-07 applicant intake and P0-08 rubric/eligibility contracts.
4. P1-01 purpose overlap and P1-02 source provenance can proceed in parallel after foundation contracts.
5. P1-04 assessment score/ranking/recommendation depends on P0-08 and approved rubric content.
6. P2 work depends on P1-04 and award/funding authorization.
7. P3 depends on P2 data and separate institutional decisions.

## Parallel workstreams

- **Platform foundation:** P0-01–P0-06.
- **Product intake:** P0-07 after FPDR-002 and P0-01/P0-02.
- **Assessment domain:** P0-08 and P1-04 after TAIS data contracts.
- **Research integrity:** P1-01/P1-02/P1-03 with authorized expert labelling.
- **Operations/policy:** P2/P3 only after institutional authority and data access.
