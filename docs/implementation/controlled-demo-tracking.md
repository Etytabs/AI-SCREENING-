# Controlled demonstration implementation tracking

**Document type:** Non-canonical implementation tracking
**Scope:** Controlled synthetic demonstration only
**Canonical records:** FPDR-001, FPDR-002 v0.3 and TAIS-001 remain authoritative at their recorded approval states. ADR-001 and ADR-002 remain proposed revisions and are not changed by this tracking document.

## Phase status

| Phase | Status | Notes |
|---|---|---|
| 1 — Demo authentication and workspace foundation | Implemented — zero Critical and High findings; six Moderate development-tooling audit entries remain | Short-lived bearer sessions for the fixed demo identities; session token held in frontend memory. |
| 2 — Applicant dashboard and draft management | Not started | Must define ownership-bound draft access; no Applicant business API is enabled in Phase 1. |
| 3 — Document submission, validation and receipts | Not started | Requires persistent application records, controlled document storage and immutable submission snapshots. |
| 4 — Grant Administrator intake and screening integration | Not started | Preserve and regression-test the existing administrator-upload path. |
| 5 — Clarification, status projection and human review | Not started | Use only the seven FPDR-002 statuses and approved transitions. |
| 6 — End-to-end testing and demonstration readiness | Not started | Synthetic data only; no production readiness claim. |

## Phase 1 implementation scope

- One login interface validates the selected workspace and exact FPDR-002 demo credentials through the API.
- The API issues random, opaque bearer sessions with a 15-minute lifetime, stores only token digests in process memory, and revokes sessions on logout.
- The API derives its principal and Grant Administrator actor from the server-side session. Caller-supplied `X-User-Role` and `X-User-Id` do not establish identity.
- Existing `/api/v1` business endpoints require authentication and are restricted to the Grant Administrator demo workspace. Applicant identities may authenticate and reach an Applicant placeholder but cannot call the existing screening API.
- The web client holds the bearer token in React memory only; refresh loses the local session. Server expiry and any authenticated API `401` clear the in-memory identity and return the user to login. The Applicant route intentionally has no application-data calls in this phase.
- Demo authentication is disabled unless `AI_SCREENING_DEMO_AUTH_ENABLED=true`; enabling it with `AI_SCREENING_ENVIRONMENT=production` is rejected.
- Authentication responses, including rejected protected requests, are marked `Cache-Control: no-store`.

To run the controlled demo locally, start the API with:

```bash
AI_SCREENING_DEMO_AUTH_ENABLED=true AI_SCREENING_ENVIRONMENT=development uvicorn apps.api.main:app --reload
```

Set `NEXT_PUBLIC_API_BASE_URL` to the API origin for the web app. Fixed demo credential values are specified by FPDR-002; no production credentials or real data are configured here.

## Phase 1 verification

- Backend: all 195 full-suite tests passed, including authentication response-cache coverage; scoped Ruff passed.
- Frontend: all 91 tests across 8 suites passed, including active-session expiry, workspace cleanup and re-login coverage; ESLint, TypeScript checking and the static Next.js build passed.
- Repository-wide Ruff reports one pre-existing import-order issue in `services/plagiarism/attribution.py`, which is outside the Phase 1 change set.
- The static frontend build completed. Next.js and `eslint-config-next` were upgraded to 15.5.29, and Vitest was upgraded to 4.1.12 with its patched dependency tree. The Vitest config now uses Oxc JSX transformation. These upgrades clear the identified Next.js and test-tool Critical advisories without changing the React 18 line.
- Next.js 15.5.29 pins PostCSS 8.4.31, while the compatible fixed release is in the same PostCSS 8.x line. A narrowly scoped `next.postcss` override pins 8.5.32, also used by Vite; the Next build, frontend tests, lint and TypeScript checks pass with this dependency tree.
- The latest `npm audit` reports 0 Critical, 0 High and 6 Moderate audit impact entries associated with GHSA-g3hv-75wg-m249 in development tooling; `npm audit --omit=dev` reports 0 findings.
- Those six audit entries are `minimatch@10.2.6` and its affected `@typescript-eslint` parser, type-utils, typescript-estree, utils and eslint-plugin packages at 8.67.0, all through GHSA-g3hv-75wg-m249. The fixed minimatch release is 11.0.1+, but the current parser dependency range is `^10.2.2`; defer an override until compatibility is verified.
- `apps/web/package.json`, `apps/web/package-lock.json` and `apps/web/vitest.config.mts` include the dependency updates. The FPDR-002 document present before Phase 1 remains byte-for-byte unchanged.
- Existing administrator workflow and API regression coverage passed. Applicant authentication is implemented, but Applicant application data, drafts, submission receipts and lifecycle operations remain out of scope for Phase 1.

## Deferred production architecture decisions

These are tracking items only; this list does not approve or amend any canonical decision:

- Select and approve the production identity provider, account lifecycle, session transport and recovery policy under ADR-001.
- Reconcile the external Applicant principal and ownership-scoped permissions with ADR-002 before Applicant business endpoints are implemented.
- Approve the production authorization matrix, Grant Administrator call scope, reviewer assignment enforcement and Team Administrator boundaries under ADR-002.
- Select durable workflow persistence, migrations, private document storage, retention, backup/recovery and data-residency controls. PostgreSQL and private object storage are target directions in implementation documentation, not implemented services.
- Select durable background processing, idempotency, retry, cancellation and audit retention behavior.
- Approve status projection, clarification, resubmission, withdrawal and decision-communication policies wherever FPDR-002 or existing records leave implementation behavior unresolved.
- Obtain separate authorization for any real institutional, NCST or RIGMS data or integration.

The in-memory session registry is intentionally limited to the controlled demo. It is process-local, is lost on API restart, and is not production authentication infrastructure.
