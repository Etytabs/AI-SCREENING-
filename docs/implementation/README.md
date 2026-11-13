# ShakaHive Product Implementation Programme

**Status:** Team implementation baseline for review  
**Company:** ShakaHive | **Category:** Research Intelligence | **First product:** AI-Assisted Grant Screening

Phase implementation reviews: [Phase 2 workflow audit](phase-2-workflow-audit.md) ·
[Phase 3 evidence quality audit](phase-3-evidence-quality-audit.md).

## Purpose and quality bar

This programme translates the agreed five-role team structure and the current MVP definition into an executable plan: workstreams, accountable owners, dependencies, deliverables, acceptance criteria and release gates.

A Silicon Valley-quality product is not defined by feature volume. It is a focused product with validated user needs, excellent workflow usability, reliable engineering, measurable quality, strong security, fast feedback loops and disciplined operations.

## Product boundary

The first product helps authorized grant administrators and reviewers process funding calls and applications using deterministic checks, AI-assisted retrieval and similarity signals, traceable evidence and human decisions.

**MVP:** grant-call creation; RFP versioning; requirement extraction and human verification; application upload and association; document extraction with provenance; deterministic eligibility/completeness checks; lexical and semantic candidate retrieval; evidence-backed findings; human review; audit history and reports; clearly labelled synthetic demo data.

**Not an MVP commitment:** automated funding decisions/rejection; automated plagiarism verdicts; autonomous scientific novelty judgements; production RIGMS or scholarly connectors without authorization and implementation; full grant lifecycle/M&E; publication reconciliation; scanned-PDF OCR until separately implemented and validated.

## Delivery principles

1. Complete the end-to-end workflow before expanding feature breadth.
2. Rules handle explicit configured requirements; ML/NLP finds and ranks candidates; people make consequential decisions.
3. Findings expose evidence, provenance, method/version and limitations.
4. Missing, inaccessible, unprocessed and not-searched are distinct states, never “no match”.
5. Security, privacy, accessibility, observability and auditability are product requirements.
6. Prefer modular, testable components and explicit contracts over premature microservices.
7. Ship small, reviewed changes with automated checks.
8. Separate synthetic benchmark results from authorized pilot evidence.

## Workstream ownership

| Workstream | Accountable role |
|---|---|
| Delivery coordination, stakeholder alignment, milestones and team decisions | Team Leader / Project Coordinator |
| User discovery, workflow validation, business model, partnerships and pilot coordination | Business & Project Manager |
| AI/ML methods, datasets, retrieval, similarity, model evaluation and responsible AI | AI/ML Engineer |
| Web app, API, database, persistence, auth implementation, integrations and deployment | Full-Stack Developer |
| Architecture, requirements alignment, engineering standards, integration oversight, quality and technical documentation | Software Developer / AI Platform Developer |

The team agreement remains authoritative if this guidance conflicts with it. Collaboration does not change role accountability.

## Phases and exit gates

| Phase | Focus | Exit evidence |
|---|---|---|
| 0. Baseline and discovery | Audit prototype, validate users/workflow/data constraints, confirm architecture | Approved MVP backlog, baseline audit, ADRs and measurable criteria |
| 1. Engineering foundation | Authentication, authorization, persistence, storage, environments, CI/CD, logs and audit | No demo identity or in-memory critical workflow dependency; security baseline passes |
| 2. Complete MVP workflow | Calls, requirements, applications, extraction, rules, findings, review and reports | End-to-end synthetic-data acceptance suite passes |
| 3. AI quality and evidence | Retrieval, similarity, ranking, provenance and evaluation | Reproducible evaluation report and reviewed error analysis |
| 4. Pilot readiness | User testing, security/privacy review, operations, training and support | Signed pilot-readiness checklist and authorization |
| 5. Controlled pilot | Limited authorized use, monitoring and iteration | Pilot report and explicit go/no-go decision |

## First execution priorities

1. Audit repository and deployed prototype: implemented, partial, missing, broken.
2. Validate user roles, workflow, formats, languages, data classification and success measures.
3. Agree deployment model, data residency, retention and institutional authorization requirements.
4. Replace demo identity with real authentication and server-side role/organization authorization.
5. Replace in-memory workflow state with persistent, tenant-aware storage and migrations.
6. Implement private object storage, upload validation, processing limits and durable background jobs.
7. Define versioned domain/API contracts for calls, requirements, applications, runs, findings, evidence and reviews.
8. Complete the call-to-review workflow with deterministic eligibility and completeness rules.
9. Implement retrieval/similarity as a separate evidence-producing stage.
10. Test usability, accessibility, security, performance, recovery and pilot acceptance.

## Definition of Ready

Every Issue states the user/problem, outcome, scope/exclusions, accountable owner, dependencies, acceptance criteria, test approach, security/data impact and documentation impact.

## Definition of Done

Acceptance criteria demonstrated with linked evidence; tests pass; changes reviewed; logs/metrics/audit/failure states considered; user and operational documentation updated; limitations/risks recorded; Issue and Project status updated.

## Scorecard

Establish a baseline before numerical targets. Track time to review-ready result; extraction success and field accuracy; eligibility correctness; retrieval Recall@k/MRR/nDCG; duplicate-candidate precision/recall; evidence validity and coverage; reviewer time saved and override rate; processing failures, queue age, latency and availability; security findings; recovery success; user task completion and satisfaction.

Never mix synthetic benchmark metrics with real pilot outcomes.

## Governance

Scope changes require a product decision record. Architecture changes require an ADR. Model/threshold changes require evaluation evidence. Data access changes require authorization and privacy/security review. This document does not grant permission to access institutional systems or confidential records.
