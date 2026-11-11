# Phase 1 — Production Foundations: Architecture and Implementation Plan

**Status:** Draft for team review  
**Repository:** Etytabs/AI-SCREENING-  
**Baseline:** Phase 0 static technical audit, merged to `main`  
**Product:** ShakaHive — AI-Assisted Grant Screening  
**Decision authority:** Team agreement and authorized stakeholder decisions remain authoritative

## 1. Purpose

Phase 1 hardens the existing grant-screening workflow so it can progress from a functional prototype toward a controlled, secure, reliable institutional pilot. It prioritizes identity, authorization, persistence, durable processing, confidential-document handling and operational readiness over new product modules.

This is a planning document. It does not claim that any Phase 1 control has been implemented, tested, deployed or approved for institutional data.

## 2. Baseline and constraints

The Phase 0 audit identified the following blockers or gaps in the inspected repository:

- API identity is based on caller-supplied `X-User-Role` and `X-User-Id` demo headers.
- Sensitive read routes and resource-level authorization require systematic review.
- The workflow repository has an in-memory implementation; a production PostgreSQL adapter and migration path were not established.
- Screening jobs run in the API process through a thread-pool runner and are not durable across restarts.
- Private document storage, upload hardening, retention/deletion, backup and recovery controls are not yet proven.
- Deployment, monitoring, secrets, incident response and restore procedures need operational verification.
- RIGMS remains authorization-dependent and must not be represented as integrated.
- Existing AI benchmarks are diagnostic and synthetic; they do not establish institutional pilot performance.

The audit was static. Runtime tests, production configuration, penetration testing, stakeholder authorization and data permissions remain separate verification activities.

## 3. Phase 1 objectives

By the end of Phase 1, the team should be able to demonstrate:

1. A trusted, server-verified user identity for every protected request.
2. Deny-by-default authorization enforced by the backend, including organization and resource boundaries where applicable.
3. Durable workflow state in PostgreSQL with repeatable, reviewed migrations.
4. Screening work that survives API restarts and handles retries/idempotency safely.
5. Private document storage with validated uploads and an explicit data lifecycle.
6. A reproducible staging/release process with observable services and tested recovery.
7. Automated evidence that the critical security and reliability controls work.

Phase 1 does not itself authorize real institutional data use. A pilot requires explicit stakeholder authorization, appropriate data terms, security review and a separate go/no-go decision.

## 4. Architecture decisions required before implementation

The Software Developer / AI Platform Developer coordinates these decisions and records each accepted decision as an ADR under `docs/architecture/decisions/`. Full-Stack owns implementation proposals for application infrastructure. The AI/ML Engineer is consulted on screening-job contracts and data handling. The Team Leader coordinates approval and stakeholder constraints.

### ADR-001 — Authentication and session model

Decide:
- Pilot identity provider and whether institutional SSO is required.
- Browser authentication/session mechanism, token lifetime, refresh/revocation and logout behaviour.
- Backend token/session validation, issuer/audience checks and key rotation.
- Local development and automated-test identity strategy that cannot be enabled accidentally in staging/pilot.
- Account provisioning, deactivation and recovery responsibilities.

Selection criteria: institutional compatibility, security posture, operational burden, supported protocols, auditability, cost and ability to test locally.

Do not select a provider solely because it is easy to integrate. Confirm intended pilot-user and institutional requirements first.

### ADR-002 — Authorization and organization isolation

Define:
- Canonical user, organization/tenant, membership and role model.
- Permission matrix for grant administrators, reviewers, programme managers and platform operators.
- Resource ownership and sharing rules for calls, applications, documents, screening runs, findings, exports and audit records.
- Whether organization isolation is enforced in application services, database row-level security, or both.
- Privileged support/operations access, break-glass procedure and audit requirements.
- Policy for users with multiple organization memberships and reviewer assignment.

Required principle: deny by default. Frontend visibility is not authorization. Every read, write, export, download and background-job action must be authorized against the trusted actor and target resource.

### ADR-003 — Relational persistence and migrations

Decide:
- PostgreSQL schema boundaries and organization ownership strategy.
- Mapping of existing repository protocol to a PostgreSQL implementation.
- Migration tool and migration ownership/review process.
- Transaction boundaries, uniqueness constraints, indexes and concurrency strategy.
- Connection management, pooling and test database strategy.
- Backup, restore and migration rollback/forward-fix approach.

Preserve existing domain/service interfaces where practical. Avoid rewriting the workflow domain merely to introduce persistence.

### ADR-004 — Durable job execution

Decide:
- Queue/worker technology compatible with the intended deployment environment.
- Job state model, queue ownership and persistence.
- Idempotency key and duplicate submission semantics.
- Retry policy, exponential backoff, timeout, cancellation and dead-letter handling.
- Worker isolation, concurrency limits and resource ceilings for document parsing.
- How screening stages report progress and partial failure to the UI.
- Recovery behaviour after worker or database restart.

The API must not report a screening job as durably accepted until the job record/enqueue operation has safely committed.

### ADR-005 — Document storage and confidential-data lifecycle

Decide:
- Private object-storage provider and environment separation.
- Object key strategy, access model, signed-download policy and encryption requirements.
- Upload limits, allowed file types, content inspection and archive extraction protections.
- Malware scanning requirement and deployment feasibility.
- Retention schedule, deletion semantics, legal holds and deletion of derived artifacts.
- Whether extracted text is stored, for how long, and under what access controls.
- Logging/redaction rules and whether external AI providers may receive document content.

Do not send real proposals to external AI services until data processing terms, permissions, retention and provider configuration have been approved.

### ADR-006 — Staging, observability and recovery

Decide:
- Environment topology: local, CI/test, staging and any later pilot environment.
- Secret management and service-account permissions.
- Structured logs, metrics, tracing, correlation IDs and privacy redaction.
- Alert ownership and incident severity/escalation.
- Backup frequency, recovery-point/recovery-time objectives and restore-test cadence.
- Deployment, migration, smoke-test and rollback/forward-fix procedure.

## 5. Implementation sequence and work packages

The sequence below is a dependency-aware proposal. Owners are roles from the approved team responsibility matrix, not named individuals.

| Order | Work package | Accountable role | Key dependencies | Exit evidence |
|---|---|---|---|---|
| 0 | Confirm pilot assumptions, threat model and ADRs 001–006 | Software Developer / AI Platform Developer | Team Leader and Business Manager stakeholder inputs | Reviewed ADRs, assumptions register and threat model |
| 1 | Trusted authentication and server-side identity | Full-Stack Developer | ADR-001 | Forged/missing/expired identity tests deny access; demo headers removed from protected paths |
| 2 | Authorization matrix and resource/tenant enforcement | Full-Stack Developer | ADR-002; trusted identity | Endpoint/resource matrix; negative tests for role escalation and cross-tenant access |
| 3 | PostgreSQL repository and migrations | Full-Stack Developer | ADR-003; organization model | Persistent workflow tests; migration from clean DB; transaction and isolation tests |
| 4 | Durable job queue and workers | Full-Stack Developer | ADR-004; persisted job model | Restart/retry/idempotency/failure tests; observable job state |
| 5 | Private document storage and lifecycle | Full-Stack Developer | ADR-005; identity/authorization | Private access tests; upload/resource-limit tests; retention/deletion evidence |
| 6 | Staging, monitoring, backup and recovery | Software Developer / AI Platform Developer | ADR-006; packages 1–5 | Staging smoke test, alert checks, restore exercise and runbooks |
| 7 | Security, integration and release verification | Software Developer / AI Platform Developer | Packages 1–6 | Evidence-based release checklist and explicit go/no-go decision |

### Work package 0 — Architecture and threat model

Deliver:
- Context/container diagram reflecting the intended pilot deployment.
- Authentication and authorization sequence diagrams.
- Permission matrix and resource ownership model.
- Data-flow map for proposals, extracted text, AI providers, logs, exports and backups.
- Threat model with likelihood, impact, controls, residual risk, owner and verification method.
- ADRs with options, rationale, consequences and unresolved questions.

No provider, queue, storage service or tenant-isolation mechanism is considered selected until its ADR is reviewed and accepted.

### Work package 1 — Authentication

Acceptance criteria:
- Protected routes derive actor identity only from a verified credential/session.
- Caller-supplied role/user headers cannot establish or elevate identity.
- Missing, malformed, expired, revoked or wrong-issuer credentials are rejected.
- Account disabled/revoked state is enforced according to the chosen identity model.
- Development/test identity helpers are isolated from staging/pilot configuration.
- Authentication failures do not disclose secrets or sensitive account details.
- Tests cover success, failure, expiry, revocation and forged-header attempts.

### Work package 2 — Authorization

Acceptance criteria:
- Every API route is inventoried and classified as public or protected with required permissions.
- Every resource read/write/download/export is checked server-side.
- Role permissions are explicit and least-privilege.
- Organization/resource ownership is enforced consistently in service/repository queries.
- Background jobs re-check authorization/ownership at enqueue and execution boundaries as appropriate.
- Negative tests cover horizontal and vertical privilege escalation, cross-organization access and unassigned reviewer access.
- Sensitive actions create tamper-evident or appropriately protected audit records.

### Work package 3 — Persistence

Acceptance criteria:
- Main workflow entities survive API restart.
- PostgreSQL implementation satisfies the existing repository contract or a reviewed replacement contract.
- Migrations work from an empty database and are exercised in CI.
- Foreign keys, uniqueness and organization scoping prevent invalid relationships.
- Multi-step state changes use explicit transactions.
- Tests verify concurrent updates and failure rollback where relevant.
- Backup and restore strategy is documented and tested before pilot.

### Work package 4 — Durable processing

Acceptance criteria:
- Screening work is processed outside the API process.
- Job state and progress survive API/worker restart.
- Duplicate enqueue/retry does not create duplicate side effects.
- Retry limits, timeout and terminal failure states are explicit.
- Failed jobs are inspectable and safely replayable by authorized operators.
- File parsing and ML work have bounded CPU, memory, file size and execution time.
- Tests cover worker crash, retry, duplicate delivery, timeout and partial-stage failure.

### Work package 5 — Document security

Acceptance criteria:
- Documents are stored privately and are not accessible through predictable public URLs.
- Downloads require authorization and short-lived access where signed URLs are used.
- Uploads enforce size, type, archive and parser resource limits.
- ZIP extraction prevents path traversal and decompression/resource exhaustion.
- Filenames and document contents are treated as untrusted input.
- Retention and deletion cover originals, extracted text, chunks, generated artifacts and backups according to policy.
- Sensitive proposal content, credentials and tokens are excluded from ordinary logs and error responses.
- External provider data flows are documented and explicitly approved.

### Work package 6 — Operations

Acceptance criteria:
- Staging is isolated from development and any real institutional environment.
- Secrets are injected from an approved secret store or deployment secret mechanism and never committed.
- Health/readiness checks distinguish application, database, queue and storage dependencies.
- Logs/metrics expose operational status without leaking proposal content or personal data.
- Alerts have an owner and documented response.
- Backup restoration is demonstrated and measured.
- Deployment and migration procedures are repeatable; rollback/forward-fix steps are documented.
- Staging smoke tests run after deployment.

## 6. Cross-cutting engineering gates

Every Phase 1 pull request must:
- Link the relevant GitHub issue and ADR(s).
- State scope, non-goals, risks and migration/security implications.
- Include tests for changed behaviour, especially negative authorization cases.
- Pass applicable lint, type, unit, integration, migration and build checks.
- Avoid secrets, real proposals and unauthorized institutional data.
- Update API/data-flow/security documentation when behaviour changes.
- Include observability and failure behaviour for asynchronous or external operations.
- Be reviewed by the relevant accountable role and Platform Developer for architecture/security-sensitive changes.

Do not combine all work packages into one large implementation PR. Keep changes small, independently reviewable and reversible where practical.

## 7. Suggested GitHub issue/PR breakdown

Use existing Phase 0 issues as the starting point; do not create duplicate issues without checking their current state.

- Issue #3: authentication and trusted identity — implementation after ADR-001.
- Issue #5: endpoint/resource authorization — implement with ADR-002 and identity contract.
- Issue #4: PostgreSQL repository and migrations — implement after schema/tenant decisions.
- Issue #6: durable background jobs — implement after job persistence contract.
- Issue #7: private storage and document lifecycle — implement after data-flow/storage decisions.
- Issue #9: staging, monitoring and recovery — implement incrementally, complete after infrastructure work.
- Issue #8: AI/ML evaluation baseline — continue as a parallel workstream; it does not replace production security gates.
- Issue #11: MVP boundary — Business Manager and Team Leader confirm scope before adding later modules.
- Issue #10: brand integration — separate product-quality work; it must not block identity/security architecture.

Before starting each issue, refresh its current status, comments and acceptance criteria on GitHub.

## 8. Roles and handoffs

- **Team Leader / Project Coordinator:** coordinates stakeholder constraints, priorities, milestone approvals and pilot go/no-go.
- **Business & Project Manager:** validates user workflows, pilot assumptions, roles, institutional needs and data-handling expectations; does not authorize access on behalf of an institution.
- **AI/ML Engineer:** defines screening-stage job contracts, model/data dependencies, compute needs, evaluation hooks and AI-provider data requirements.
- **Full-Stack Developer:** implements authentication integration, authorization enforcement, database, migrations, jobs, storage, APIs and application tests.
- **Software Developer / AI Platform Developer:** owns architecture/ADRs, threat model, technical standards, cross-component contracts, security review and technical acceptance.

Handoffs must include a concrete artifact and acknowledgement by the receiving role.

## 9. Phase 1 exit criteria

Phase 1 is ready for a controlled pilot-readiness review only when all applicable criteria have evidence:

- Real authentication is enabled; demo header identity is removed from protected paths.
- Authorization is deny-by-default and passes endpoint, resource and organization-isolation tests.
- Workflow state is persisted in PostgreSQL and migrations are repeatable.
- Durable jobs survive restarts and handle retries/idempotency safely.
- Proposal documents are private, validated, access-controlled and governed by an approved lifecycle.
- Staging, secrets, logs, metrics, alerts, backups and restore procedures are verified.
- Critical security findings are mitigated or explicitly accepted by the authorized decision owner; no unmitigated critical/high issue is silently waived.
- Critical user journeys pass automated integration and staging smoke tests.
- AI findings retain evidence/provenance and human review; similarity is not labelled as proof of plagiarism.
- Data permissions, external provider use and any institutional integration are explicitly authorized.
- Product, business, technical and stakeholder owners record a go/no-go decision.

Passing these criteria does not itself establish regulatory compliance, security certification or institutional endorsement.

## 10. Explicit non-goals

Unless separately approved:
- Do not add grant lifecycle/M&E or publication reconciliation to the first release.
- Do not automate funding decisions or reviewer conclusions.
- Do not label similarity as plagiarism.
- Do not make autonomous scientific novelty judgments.
- Do not activate RIGMS or other institutional connectors without written authorization and technical documentation.
- Do not use real institutional proposals in public demos, synthetic benchmarks or developer environments without explicit authorization and controls.
- Do not undertake a broad rewrite of working domain logic as part of infrastructure hardening.

## 11. Open questions to resolve in Work Package 0

1. Which identity provider and sign-in experience are required by the intended pilot institution?
2. Which organizations/tenants are in scope for the first controlled environment?
3. Who provisions, approves, suspends and removes user accounts and reviewer assignments?
4. What roles and resource-sharing rules does the actual grant workflow require?
5. Which deployment environment and managed services are available/approved for PostgreSQL, queue and private object storage?
6. What proposal retention/deletion rules and data-processing restrictions apply?
7. Are external AI providers permitted to process proposal content, and under what terms?
8. What are the target pilot volume, file-size limits, concurrency and recovery expectations?

Until answered, record assumptions explicitly and do not encode them as institutional facts.

## 12. Related documents

- `docs/implementation/phase-0-baseline-audit.md`
- `company/architecture/README.md`
- `docs/implementation/security-quality-and-devops.md`
- `docs/implementation/platform-and-data.md`
- `docs/implementation/pilot-and-release-plan.md`
- `docs/implementation/role-workstreams.md`
- GitHub Issues #3–#11 in `Etytabs/AI-SCREENING-`
