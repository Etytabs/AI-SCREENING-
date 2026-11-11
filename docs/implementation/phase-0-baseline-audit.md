# Phase 0 — Technical Baseline Audit

**Audit date:** 11 November 2026  
**Repository:** Etytabs/AI-SCREENING-  
**Audited ref:** main  
**Audited commit:** 9a3cda5b13cfd0ee066ff3e0a3b1f88e6f22d292  
**Status:** Initial static repository audit; runtime, deployment, CI execution and stakeholder validation remain outstanding.

## 1. Executive assessment

ShakaHive has a meaningful functional prototype and a modular codebase. It is not yet a production-ready institutional product. The most important gap is not the absence of AI features; it is the operational foundation around identity, authorization, persistent workflow state, secure file storage, durable jobs, tenant isolation and deployment controls.

The immediate objective should be to harden the existing product path before adding additional product modules. Grant lifecycle/M&E and publication reconciliation are present as architectural directions and partial source/API models, but should not distract the team from completing a secure, reliable grant-screening MVP.

## 2. Repository snapshot

| Area | Observed on main |
|---|---|
| Default branch | main |
| Repository visibility | Public |
| Tracked files | 241 |
| Backend | FastAPI / Python |
| Frontend | Next.js 14 / React 18 / TypeScript |
| Backend test modules | 25 Python test files |
| Frontend test files | 7 |
| GitHub Actions workflows | 4: CI plus three retrieval benchmark workflows |
| Persistence | WorkflowRepository protocol with InMemoryWorkflowRepository implementation |
| Job execution | In-process ThreadPoolJobRunner |
| Identity | X-User-Role / X-User-Id demo headers |
| Database configuration | PostgreSQL/pgvector service in docker-compose; no production repository adapter or migration path identified in inspected code |
| External integrations | RIGMS provider is an explicit authorization-dependent placeholder; OpenAlex is optional |
| Brand files in assets/brand | design-tokens.css only; supplied PNG logo exports are not yet in this directory |

This is a static inspection of the repository, not a runtime penetration test or deployment verification. The listed test-file count is not a statement that all tests currently pass.

## 3. Capability assessment

### Implemented foundations visible in code
- Next.js dashboard and grant workflow screens.
- FastAPI API with grant, workflow, NCST, publication, duplication and health route modules.
- Grant-call and RFP workflow with deterministic requirement extraction and administrator verification.
- Application upload, ZIP grouping and manual association flow.
- Document extraction and page/chunk provenance.
- Deterministic eligibility and completeness checks.
- Lexical, embedding and hybrid semantic retrieval, with optional cross-encoder reranking.
- Duplicate/overlap/novelty signal stages.
- Evidence validation and source coverage concepts.
- Reviewer decision and audit primitives.
- Synthetic demo data and retrieval benchmark datasets.
- Docker files and GitHub Actions workflows.

### Partial or unsuitable for institutional production
- WorkflowRepository is an interface, but the inspected implementation is in-memory. The Docker Compose PostgreSQL service is not evidence that the application persists workflow entities in PostgreSQL.
- ThreadPoolJobRunner executes jobs inside the API process. It is not a durable distributed queue and work can be lost on restart.
- Identity is represented by caller-supplied headers; the API documentation explicitly says these are not authenticated. This is a critical authorization blocker.
- The workflow guide states that read endpoints do not check a role. Sensitive read paths therefore require a systematic access-control review.
- The frontend API client sends role and user headers selected by the UI; this is demo behaviour, not an identity boundary.
- Upload handling, object storage, retention, malware/resource controls and production file access require a deeper security review.
- No tenant-aware relational persistence, database migration system, backup/restore evidence or disaster-recovery test was established by this static audit.
- RIGMS is not connected; its provider reports authorization/configuration requirements and does not invent an API.
- The supplied brand pack is not yet committed as source assets. The current home page uses a generic shield-style symbol rather than the supplied ShakaHive mark.
- CI workflow configuration exists, but the merge commit returned no combined status entries in the inspected GitHub status response. This audit does not claim that CI passed or failed.

## 4. Critical findings and recommended priority

| ID | Finding | Severity | Recommended owner | Required outcome |
|---|---|---|---|---|
| P0-01 | Demo header identity permits caller-controlled role/user claims | Critical | Full-Stack; Platform oversight | Real authentication and server-side authorization; remove demo identity from pilot |
| P0-02 | Workflow persistence is in-memory; PostgreSQL runtime adapter/migrations not established | Critical | Full-Stack; Platform oversight | Durable database-backed repository, migrations, transaction and restore tests |
| P0-03 | Sensitive read routes and resource-level authorization require complete review | Critical | Full-Stack; Platform oversight | Deny-by-default policy and endpoint/resource authorization matrix with tests |
| P0-04 | In-process thread-pool jobs are not durable across restarts | High | Full-Stack; Platform oversight | Durable queue/worker, idempotency, retry, failure and recovery handling |
| P0-05 | Upload/storage security and confidential-document lifecycle not proven | High | Full-Stack; Platform oversight | Private object storage, file validation, resource limits, retention/deletion and access tests |
| P0-06 | Frontend brand pack not integrated; supplied source PNG assets absent from assets/brand | Medium | Full-Stack; Team Leader/brand owner | Add original assets, manifest validation and use approved logo/icon/fonts/tokens in UI |
| P0-07 | AI evaluation is based on small synthetic benchmark sets; no authorized representative pilot set | High for claims | AI/ML Engineer | Versioned labelled evaluation protocol, error analysis and stakeholder-approved thresholds |
| P0-08 | Deployment, secrets, monitoring, backups, restore and incident procedures need operational verification | High | Platform; Full-Stack | Staging readiness evidence, runbooks, alerting and tested recovery |
| P0-09 | README product scope spans grant screening, lifecycle/M&E and publication reconciliation | Medium | Business Manager; Team Leader | Keep first release backlog bounded to approved grant-screening MVP; track later modules separately |

Severity is a prioritization recommendation, not a formal external security certification.

## 5. Phase 0 work plan

### Track A — Identity and access
1. Inventory every API route and classify public, authenticated, role-protected and organization-scoped operations.
2. Select the pilot identity provider and authentication/session model.
3. Define roles and permissions with the intended institution.
4. Enforce authorization in backend dependencies/services, not the frontend.
5. Add negative tests for missing identity, forged roles, cross-user access and cross-organization access.

### Track B — Persistence and data
1. Define relational schema and organization ownership boundaries.
2. Implement PostgreSQL repository adapter behind the existing repository protocol.
3. Add schema migrations, constraints, indexes and transaction boundaries.
4. Persist extracted document metadata/content and screening results appropriately.
5. Define object storage, encryption, retention, deletion and backup policies.
6. Prove backup restoration and data migration behaviour.

### Track C — Durable processing
1. Select a durable job system compatible with the deployment environment.
2. Define job states, idempotency, retries, timeouts, cancellation and dead-letter handling.
3. Move long-running parsing/screening out of API-process memory.
4. Add restart/retry/failure integration tests and queue observability.

### Track D — AI/ML validation
1. Freeze the current synthetic benchmark versions as baselines.
2. Document label definitions and evaluation protocol.
3. Add difficult edge cases and independent review of labels.
4. Report per-stage precision/recall, retrieval metrics, false-positive analysis and coverage.
5. Keep real institutional data out of experiments until authorization and data terms are explicit.

### Track E — Product and brand
1. Confirm the first release is grant-call screening; keep lifecycle/M&E and publication reconciliation as later roadmap modules unless separately approved.
2. Validate the current workflow with intended administrators/reviewers.
3. Add the original supplied PNG logo assets and correct brand fonts to the repository.
4. Replace temporary/generic brand marks and verify accessible colour contrast.
5. Validate core user journeys with usability and accessibility testing.

### Track F — Operations and release
1. Establish development, CI, staging and pilot environments.
2. Review secrets and environment-variable handling.
3. Add structured privacy-aware logs, metrics, tracing and alerting.
4. Define deployment, rollback, incident response and support runbooks.
5. Verify security scans, backup/restore, smoke tests and release sign-off.

## 6. Exit criteria for Phase 0

Phase 0 is complete when:
- Product and Business owners confirm the MVP scope and priority user journeys.
- Platform Developer publishes an approved architecture decision set and non-functional requirements.
- Full-Stack publishes route/access inventory, data model and persistence plan.
- AI/ML Engineer publishes a reproducible baseline evaluation report and limitations.
- Security risks have owners, mitigation plans and release-blocking classification.
- Brand assets and current UI implementation are reconciled.
- Phase 1 issues have acceptance criteria, owners by role, dependencies and priority.
- Stakeholders clarify whether the next environment is synthetic demo, controlled internal test or authorized institutional pilot.

## 7. Explicit limitations of this audit

This audit did not execute the application, run pytest/npm tests, inspect live Cloudflare/Render configuration, test production endpoints, conduct penetration testing, inspect private institutional systems, verify legal data permissions or confirm actual deployment secrets. Those require separate authorized checks. No RIGMS integration or institutional endorsement is implied.

## 8. Source files inspected

- README.md
- pyproject.toml
- docker-compose.yml
- Dockerfile
- .env.example
- .github/workflows/ci.yml
- apps/api/main.py
- apps/api/dependencies.py
- apps/api/routes/workflow.py
- apps/web/package.json
- apps/web/lib/api.ts
- apps/web/app/page.tsx
- services/grant_workflow/repository.py
- services/grant_workflow/jobs.py
- services/grant_workflow/service.py
- services/grant_workflow/providers.py
- services/grant_workflow/models.py
- docs/grant-workflow.md
- data/evaluation/*
- tests/*
- assets/brand/*
