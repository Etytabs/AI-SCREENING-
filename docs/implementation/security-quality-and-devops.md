# Security, Quality Engineering and DevOps Standard

## Security posture and threat model

Treat proposals, extracted text, prompts, model outputs, logs, exports and backups as potentially confidential. A demo deployment is not suitable for real submissions by default.

Threat model: cross-organization access; account/session compromise; privilege escalation; malicious/oversized uploads; archive traversal/decompression/parser exhaustion; injection through documents/prompts/rendering; SSRF where URL ingestion exists; leakage through logs/analytics/exports/backups/AI providers; secrets exposure; job replay/duplication; insider misuse/audit tampering; dependency/container/CI supply-chain risks.

For each threat record likelihood, impact, controls, residual risk, owner and verification evidence.

## Identity and authorization

Use real identity in staging/pilot; remove demo headers. Enforce authorization on every API operation/resource lookup. Define least-privilege roles for administrators, reviewers, programme managers and operators. Enforce organization isolation in queries/storage. Test horizontal and vertical privilege escalation. Audit role changes, exports, sensitive access and reviewer decisions.

## Secure development lifecycle

CI checks: formatting, linting, type checks, unit/integration tests, dependency scan, secret scan, static analysis, container scan where relevant, build/migration checks and staging smoke tests. Protect main with required checks/review. Require review for security, authorization, schema, AI threshold and infrastructure changes. Pin/update dependencies through reviewed changes.

## Testing pyramid

- Unit: rules, parsers, validators, state transitions, permission policy and AI preprocessing.
- Integration: DB/migrations, storage, queue workers, API authorization, AI adapters and audit writes.
- End-to-end: call-to-report; upload failure/manual association; tenant isolation; partial coverage; retries/idempotency.
- Non-functional: load/performance, resilience, recovery, security, accessibility and browser compatibility.
- AI/ML: versioned evaluation sets, leakage checks, baselines, threshold regression and error analysis.

## Required security tests

Organization A cannot access organization B; reviewer cannot perform admin-only actions; absent/expired identity is denied; spoofed/malformed/excessive uploads are rejected; stored files remain private; secrets/proposal text do not appear in logs/errors; SSRF protections block private/internal targets where URL retrieval exists; rate/resource limits work; privileged actions generate audit events.

## Release and environments

Separate development, test/CI, staging and pilot/production. Keep secrets out of repository and CI logs. Use least-privilege service accounts. Review migrations and backup before risky schema changes. Run smoke tests after deployment. Maintain release notes, deployment identifier and rollback/forward-fix plan. Never copy real proposals to public demos or local developer environments.

## Reliability

Set service objectives after measuring baseline. Monitor API availability/latency, queue wait/processing duration, success/failure by file type, provider latency/errors, DB/storage capacity, backup and restore results, frontend errors. Define incident severity, escalation, communication and post-incident review.

## Release candidate gate

Critical journeys pass; no unmitigated critical/high security issue; authorization/tenant isolation pass; migrations and restore are tested; monitoring/alerts active; limitations/support documented; product and technical owners sign off.
