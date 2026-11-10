# Platform, Backend and Data Implementation Plan

## Architecture approach

Start with a modular application and explicit internal boundaries. Do not split into independently deployed microservices until scale, team ownership or isolation requirements justify the operational cost.

Modules: identity/organizations/authorization; calls/requirements; application/document ingestion; extraction/normalization; rules; AI/ML adapter; evidence/findings; review/audit; reporting/export; jobs/integrations.

Platform Developer owns architecture/standards. Full-Stack owns API/database/application implementation. AI/ML owns model methods and behaviour.

## Persistence and tenancy

- PostgreSQL is the transactional source of truth; pgvector is optional where semantic retrieval justifies it.
- Model organization ownership into every tenant-scoped entity.
- Enforce isolation in server-side services and, where appropriate, PostgreSQL Row-Level Security.
- Resolve tenant/user from authenticated identity; never trust browser-supplied tenant IDs.
- Use migrations, constraints, foreign keys and indexes.
- Define retention, deletion, archival and legal-hold behaviour before confidential data.
- Keep source files in private object storage; store metadata and opaque references in the database.

## Domain integrity

Use stable non-guessable IDs; unique application references in the correct call/organization scope; immutable source versions/checksums; screening runs that record exact input/configuration/model/rule versions; findings/evidence linked to exact runs and source versions; append-only review history; audit actor/action/resource/time/correlation ID. Store timestamps consistently in UTC and render in user locale.

## Background processing

Parsing and screening must not depend on a long browser/API request. Implement durable queue/workers, explicit job state/progress/retry count, idempotency, bounded exponential backoff, dead-letter handling/replay procedure, resource limits, safe cancellation and correlation IDs. A job is complete only after output and state are durably committed.

## File ingestion

Allowlist formats and verify file signatures/MIME. Limit file count, compressed/uncompressed size, pages and processing time. Defend against archive traversal, decompression bombs, malformed PDFs and parser exhaustion. Scan for malware where required and available. Keep originals private with authorized short-lived downloads. Record checksum, uploader, tenant, timestamp, parser version and status. Never log document content or credentials. Treat parser output as untrusted.

## API and integrations

Publish OpenAPI contracts. Version breaking changes and document deprecation. Use consistent errors, validation and pagination. Protect process/write endpoints with authorization, rate limits and idempotency. Wrap providers in adapters with timeouts, quotas, retries and circuit breakers. Store credentials in secret management/environment configuration, never source control.

RIGMS and scholarly connectors stay disabled until written authorization, data mapping, API specification, security review and acceptance tests exist.

## Security controls

Real authentication; server-side RBAC and tenant isolation; maintained session/token lifecycle; CSRF protection where cookie sessions apply; TLS; encryption at rest for database/storage/backups; secret rotation; least privilege; input validation/output encoding; parser sandbox/resource limits; audit of sensitive access and privileged operations; dependency/container/secret scanning; incident response and tested backups.

## Observability

Use privacy-aware structured logs, metrics and traces. Track correlation IDs, queue age, processing duration, parser failures, provider latency, retries, API errors and resource saturation. Do not log proposal text, access tokens, secrets or unnecessary personal data. Define health/readiness checks, dashboards, alerts, escalation and restore tests.

## Environments and deployment

Separate local, test/CI, staging and pilot/production. Use environment-specific credentials/data. Never copy real proposal data to local environments without approved anonymization. Make deployments repeatable, versioned and reversible: documented config, migration strategy, build/dependency versions, post-deploy smoke tests, release notes, known limitations and rollback owner.

## Architecture review

For significant changes ask: approved requirement? tenant isolation/least privilege? data-flow/retention/audit impact? API compatibility? failure/retry/recovery path? resource limits tested? observability/runbooks updated? ADR required?
