# ADR-001: Authentication and Session Model

- **Status:** Proposed revision — aligned with founder's Phase 1 pilot direction; technical details require team review
- **Date:** 11 November 2026
- **Decision owners:** Software Developer / AI Platform Developer (technical recommendation); Team Leader (coordination and approval)
- **Implementation owner:** Full-Stack Developer
- **Related:** Phase 0 audit; Phase 1 Architecture & Implementation Plan; GitHub Issue #3; ADR-002

## 1. Context and current repository evidence

The current API does not authenticate users. `apps/api/dependencies.py` constructs an `Actor` from caller-supplied `X-User-Role` and `X-User-Id` headers. The source explicitly labels this as a demo boundary. `apps/web/lib/api.ts` creates those headers from a UI-selected identity. A caller can therefore claim another user ID or role.

The API's identity dependency must be replaced before the MVP is used with non-public application data. Authentication must establish a trusted subject; authorization is addressed separately in ADR-002.

## 2. Founder-confirmed pilot direction

The founder has confirmed the following operating assumptions:

1. **Account model:** ShakaHive-managed accounts for the first test MVP. Users may be invited using Gmail addresses or other approved email addresses. The first pilot is not dependent on institutional SSO or institution-managed accounts.
2. **Account administration:** ShakaHive team members manage invitations and account access.
3. **Deployment context:** the MVP is initially for one institution as a test platform, not a multi-institution production service.
4. **GitHub access:** repository access is separate from application access. A reviewer may also be invited to the GitHub repository when the ShakaHive team decides that repository access is appropriate.

These are founder-provided product/operating assumptions. They do not identify a specific authentication vendor, prove institutional authorization to process real proposals, or imply that every reviewer should have GitHub access.

## 3. Decision drivers

- Simple onboarding for a controlled MVP using email invitations.
- Individually identifiable accounts; no shared team login.
- Server-side verification of identity and session validity.
- ShakaHive-controlled invitation, suspension and removal workflow.
- Secure browser sessions, logout and credential revocation.
- Clear separation of local demo/test identity from staging/MVP.
- Provider flexibility so the team can adopt institutional SSO later if required.

## 4. Options considered

### Option A — ShakaHive-managed invited accounts (preferred MVP direction)

ShakaHive team members invite individual users by email. Each person authenticates with their own account. Gmail addresses may be used, but the email domain itself is not proof of authorization or institutional affiliation.

The exact authentication mechanism (for example, managed email/password, email magic link, or Google sign-in) remains a technical selection to be made after comparing security, account recovery, cost, integration effort and deployment constraints.

**Advantages:** matches the founder-confirmed MVP account model; ShakaHive controls who is invited and can revoke access.

**Trade-offs:** ShakaHive must manage invitations, account recovery, deactivation, MFA policy and support. Email verification and abuse protections are required.

### Option B — Institutional identity provider / SSO

Integrate with the institution's identity provider if the institution later requires or approves this model.

**Advantages:** can align with institutional account lifecycle and central MFA/revocation.

**Trade-offs:** requires institutional technical coordination and is not a prerequisite for the currently described test MVP.

### Option C — Self-managed identity service

Operate an identity service under ShakaHive's control.

**Advantages:** control over identity configuration.

**Trade-offs:** ShakaHive assumes significant security and operational responsibilities. Do not choose this without a clear need and capacity.

## 5. Proposed MVP direction

Adopt **ShakaHive-managed, individually invited accounts** for the first controlled MVP. Do not require institutional SSO for this initial test environment unless the institution later makes it a condition.

Implementation requirements:

- ShakaHive team members with an authorized team-administration permission can invite a user by email, resend/expire an invitation, suspend access and revoke active sessions.
- Each person uses an individual account. Shared Gmail credentials or a shared generic "team" login are prohibited.
- Invitation is allowlist-based: only a valid, unexpired invitation can activate an account. The invitee must verify control of the invited email address.
- A Gmail address is an acceptable email address, not an automatic grant of application permissions. Access comes from the server-side invitation and membership record.
- Do not infer a role from an email domain, display name, browser state or client-supplied claim.
- The backend validates the authentication credential/session and creates a canonical principal from verified identity data.
- Roles and application permissions are loaded from trusted server-side records as defined in ADR-002.
- The frontend must stop sending `X-User-Role` and `X-User-Id` as authority. These headers must not establish identity or privilege.
- Select the authentication provider/mechanism through a short technical evaluation. Prefer a managed identity solution over building password storage, reset and MFA flows from scratch unless there is a compelling reason.
- For browser sessions, evaluate secure HttpOnly SameSite cookies and CSRF protection against the actual frontend/API domain topology. Do not store long-lived bearer tokens in localStorage.
- Define invitation expiry, session lifetime, logout, revocation, recovery, rate limiting and account suspension.
- Keep test/demo authentication isolated and impossible to enable accidentally in the MVP deployment.
- Keep the integration provider-independent at the application boundary so institutional SSO can be considered later.

## 6. GitHub repository access is separate

Access to the ShakaHive MVP does not automatically grant access to the GitHub repository, and GitHub access does not automatically grant access to the MVP.

- The ShakaHive team separately invites approved collaborators to the GitHub repository.
- Give the minimum repository permission needed for the person's actual contribution.
- A reviewer who only reviews grant applications does not need GitHub access by default.
- If a reviewer is also contributing to software/product review and is explicitly invited to GitHub, record that as a separate access decision.
- GitHub permissions must not be used as a substitute for application roles, and application roles must not be mapped automatically to GitHub permissions.

## 7. Consequences

- ShakaHive owns the initial user-invitation and account lifecycle process.
- A server-side user and membership record is required.
- The MVP can be tested without waiting for institutional SSO configuration.
- The team must select an authentication mechanism/provider and configure it securely before implementing Issue #3.
- Existing synthetic demo workflows need a safe test identity path that cannot bypass MVP authentication.
- Future institutional SSO may require account linking/migration; stable internal user IDs should not depend solely on mutable email addresses.
- Authentication establishes who the user is. It does not by itself grant access to a grant call, application or document.

## 8. Security and acceptance criteria

- Only invited and verified email accounts can activate MVP access.
- Invitations are single-use, expire, and cannot be used after revocation.
- Every user has an individual identity; shared credentials are not supported.
- Missing, malformed, expired, invalid or revoked credentials are rejected.
- Client-supplied `X-User-Role` and `X-User-Id` cannot establish identity or elevate privileges.
- A user cannot choose their own role or organization membership.
- ShakaHive team account administrators can suspend a user and revoke their sessions.
- Session cookies, if used, have appropriate Secure, HttpOnly and SameSite attributes and CSRF protections for state-changing requests.
- Secrets and signing keys are not committed; rotation is documented and testable.
- Authentication errors do not leak tokens, secrets or sensitive identity data.
- Tests cover invitation acceptance, email verification, authentication success/failure, expiry, revocation, logout and test-mode isolation.
- MVP deployment fails closed if required authentication configuration is missing.
- GitHub repository permissions are configured and reviewed separately from MVP roles.

## 9. Remaining technical questions

1. Which managed identity provider or authentication mechanism best supports email invitations, verification, revocation and secure browser sessions within the team's budget and deployment?
2. Should invitees authenticate by Google sign-in, email/password, magic link, or a combination?
3. Is MFA required for ShakaHive team administrators and other privileged MVP users?
4. Which named team members are allowed to invite, suspend and remove users?
5. What are the frontend/API domains, and what cookie, CORS and CSRF design do they require?
6. What account recovery and support process will ShakaHive operate?

## 10. Implementation boundary

This ADR records the founder-confirmed account direction but does not select a provider or implement authentication. Resolve the remaining technical questions, update this ADR with the selected mechanism and rationale, then implement Issue #3.

## References

- `apps/api/dependencies.py`
- `apps/web/lib/api.ts`
- `docs/grant-workflow.md`
- `docs/implementation/phase-0-baseline-audit.md`
- `docs/implementation/phase-1-architecture-and-implementation-plan.md`
- ADR-002
