# ADR-001: Authentication and Session Model

- **Status:** Proposed — requires team and pilot-stakeholder review
- **Date:** 11 November 2026
- **Decision owners:** Software Developer / AI Platform Developer (technical recommendation); Team Leader (coordination and approval)
- **Implementation owner:** Full-Stack Developer
- **Related:** Phase 0 audit; Phase 1 Architecture & Implementation Plan; GitHub Issue #3; ADR-002

## Context

The current API does not authenticate users. `apps/api/dependencies.py` constructs an `Actor` from caller-supplied `X-User-Role` and `X-User-Id` headers. The source explicitly labels this as a demo boundary. `apps/web/lib/api.ts` creates those headers from a UI-selected identity. A caller can therefore claim another user ID or role.

The API's identity dependency must be replaced before the platform is used with confidential grant applications or institutional accounts. Authentication must establish a trusted subject; authorization is addressed separately in ADR-002.

The repository and current documentation do not establish which identity provider the intended pilot institution requires. It would be premature to select a vendor or protocol without stakeholder confirmation.

## Decision drivers

1. Compatibility with the intended institution's identity and account-provisioning requirements.
2. Server-side verification of identity and token/session validity.
3. Secure browser session handling, revocation and logout.
4. Least-privilege service configuration and key/secret rotation.
5. Clear separation of local demo/test identity from staging and pilot.
6. Testability, auditability, operational support and maintainable integration.
7. Avoidance of unnecessary identity-provider lock-in.

## Options to evaluate

### Option A — Institutional identity provider / SSO

Integrate with the identity provider designated by the pilot institution, subject to its supported protocol and configuration.

**Advantages:** aligns with institutional account lifecycle, central MFA and access revocation where available.

**Trade-offs:** depends on institutional readiness, technical documentation, tenant configuration, test accounts and stakeholder coordination.

### Option B — Managed external identity provider

Use a managed identity service if the institution does not require or provide an SSO integration for the controlled pilot.

**Advantages:** can reduce custom authentication operations and provide mature session/account features.

**Trade-offs:** introduces provider cost, data-processing/vendor review, configuration and account lifecycle responsibilities. Institutional acceptance must be confirmed.

### Option C — Self-managed identity service

Operate an identity service under ShakaHive's control.

**Advantages:** greater control over deployment and identity configuration.

**Trade-offs:** ShakaHive assumes responsibility for patching, availability, account recovery, MFA, abuse protection, key management and security operations. This option should not be selected merely to avoid institutional coordination.

## Proposed architectural direction

**Do not select the provider in this ADR yet.** First obtain answers to the open questions below. Regardless of provider, implement a provider-independent backend identity boundary:

- The backend validates the credential/session using trusted issuer configuration, signature/key validation, issuer and audience checks, expiry and other required claims.
- The backend constructs a canonical authenticated principal from verified claims. Client-supplied role or user headers are never authoritative.
- The canonical principal contains a stable subject identifier and only the verified identity attributes needed by the application. Organization membership and application permissions are resolved through the authorization model in ADR-002; do not trust arbitrary role claims supplied by the browser.
- Protected API routes reject missing, invalid, expired or revoked credentials according to the selected session model.
- Browser credential storage and transport are selected based on the chosen protocol and threat model. Prefer secure, HttpOnly, SameSite cookie-backed sessions for a same-site browser architecture where feasible; document any cross-site constraints and CSRF protections. Do not put long-lived bearer tokens in localStorage.
- Logout and account disablement/revocation behaviour must be explicit. Session lifetime, refresh, rotation and key rotation must be documented.
- Development/test authentication is isolated behind explicit test configuration and cannot be enabled in staging or pilot by accident.
- The frontend may display identity and available actions, but the backend remains the authority for identity and permissions.

## Consequences

- Existing demo identity headers must be removed from protected production paths and from the production frontend API client.
- API dependencies and tests will consume a canonical verified principal rather than constructing an actor from request headers.
- A provider adapter/configuration boundary should isolate provider-specific validation from grant workflow services.
- User provisioning, deactivation and organization membership need a defined operational owner.
- Local development must retain a convenient but clearly isolated test identity mechanism.
- Existing synthetic demo workflows may need a separate demo profile or seeded test identity; this must not weaken staging/pilot authentication.
- Authentication establishes who the user is. It does not by itself grant access to a grant call, application or document.

## Security and acceptance criteria

- Missing, malformed, expired, invalid-signature, wrong-issuer and wrong-audience credentials are rejected.
- Client-supplied `X-User-Role` and `X-User-Id` cannot establish identity or elevate privileges.
- A client cannot choose its own trusted organization membership or application role.
- Disabled/revoked accounts and sessions are rejected within the documented revocation model.
- Session cookies, if used, have appropriate Secure, HttpOnly and SameSite attributes and CSRF protections for state-changing requests.
- Secrets and signing keys are not committed; rotation is documented and testable.
- Authentication errors do not leak tokens, secrets or sensitive identity data.
- Tests cover authentication success, failure, expiry, revocation, logout and demo/test-mode isolation.
- Staging/pilot configuration fails closed if required identity configuration is missing.

## Open questions before final decision

1. Which identity provider does the intended pilot institution require or already operate?
2. Is institutional SSO mandatory for the first controlled environment?
3. Are pilot users institution-managed accounts, ShakaHive-managed accounts, or a mixture?
4. Who provisions, approves, suspends and removes accounts, and who handles account recovery?
5. Is MFA required by institutional policy?
6. What browser/domain topology will be used (same-site frontend/API or cross-site), and what does that imply for cookies, CORS and CSRF?
7. Are external identity-provider processing terms and hosting regions acceptable to the institution?

## Implementation boundary

This ADR does not authorize a specific identity provider, create accounts, configure SSO, or implement authentication. After the open questions are answered, record the selected provider/session design and rationale here before implementation of Issue #3.

## References

- `apps/api/dependencies.py`
- `apps/web/lib/api.ts`
- `docs/grant-workflow.md`
- `docs/implementation/phase-0-baseline-audit.md`
- `docs/implementation/phase-1-architecture-and-implementation-plan.md`
