# ADR-002: Authorization and Organization Isolation

- **Status:** Proposed — requires team and pilot-stakeholder review
- **Date:** 11 November 2026
- **Decision owners:** Software Developer / AI Platform Developer (technical recommendation); Team Leader (coordination and approval)
- **Implementation owner:** Full-Stack Developer
- **Related:** ADR-001; Phase 0 audit; Phase 1 Architecture & Implementation Plan; GitHub Issue #5

## Context

The current workflow has role-based action checks in parts of the service layer, but the documented API states that read endpoints do not check a role. The frontend sends caller-selected role and user headers, which are not authenticated. The current workflow documentation lists these operational roles:

- `NCST_GRANT_PERSONNEL`
- `GRANT_INSTITUTION`
- `GRANT_ADMINISTRATOR` (legacy equivalent)
- `REVIEWER`
- `SYSTEM_ADMINISTRATOR`

The current role names and service checks describe demo workflow behaviour; they are not yet an approved institutional permission policy. The inspected repository does not establish a complete organization/tenant membership model or prove organization isolation at API, database, file-storage or job-worker boundaries.

Authentication in ADR-001 provides a verified subject. This ADR defines how that subject is granted access to actions and resources.

## Decision drivers

1. Deny-by-default access control on every protected API operation.
2. Least privilege and separation of duties.
3. Organization/tenant isolation across API, database, documents, jobs, exports and audit records.
4. Resource-level authorization, not role-only checks.
5. Explicit reviewer assignment and scope.
6. Consistent enforcement for reads, writes, downloads, exports and background processing.
7. Auditable privileged actions and policy changes.
8. Testable policies that can evolve without scattering role comparisons throughout route handlers.

## Proposed authorization model

Adopt a policy-based authorization layer using **role-based permissions scoped to an organization and resource relationship**. A role alone is insufficient to grant access.

A request's authorization context should be derived from:
- The verified principal from ADR-001.
- Active organization membership(s) loaded from trusted server-side records.
- The user's role/permission grants within the selected organization.
- The target resource's organization, ownership and workflow relationships.
- Explicit assignments, such as reviewer-to-application or reviewer-to-call assignment, where the approved workflow requires them.
- The requested action (for example, read, create, update, upload, screen, decide, export, download, administer).

Do not accept organization IDs, role names, ownership, reviewer assignment or permission claims from the browser as proof of access. Client values may identify the requested organization/resource, but the server must validate membership and relationship before proceeding.

### Enforcement layers

1. **API boundary:** every protected route declares its authentication and permission requirement. Public routes are explicitly allowlisted.
2. **Application/service layer:** domain operations authorize the actor against the target resource and workflow state; route-level checks alone are not enough for reused service methods.
3. **Repository/data layer:** queries are scoped to the authorized organization/resource. Consider database row-level security as defence in depth after evaluating connection pooling and transaction-scoped tenant context.
4. **Object storage:** file keys are private; downloads require a server authorization decision and short-lived access mechanism where signed URLs are used.
5. **Background jobs:** jobs carry immutable actor, organization and resource identifiers from the authorized enqueue operation. Workers validate the job's scope and current resource state before processing; a queue message is not itself an authorization grant.
6. **Audit:** privileged access, membership/role changes, exports, document access and reviewer decisions generate appropriately protected audit events.

## Proposed role and permission design

Treat these as candidate application roles to validate with the intended institution, not finalized institutional job titles.

| Candidate role | Proposed scope | Candidate permissions | Important restrictions |
|---|---|---|---|
| Grant administrator | One or more explicitly assigned organizations | Manage grant calls/RFPs, verify requirements, manage submissions, initiate screening, view authorized results, manage reviewer assignments, view relevant audit/report data | Cannot access another organization without membership; privileged actions audited |
| Reviewer | Explicitly assigned call/application set within an organization | Read assigned call/application/evidence; add notes; submit review decisions within assigned scope | No call configuration, bulk export or access to unassigned applications unless separately granted |
| Programme manager | Explicitly assigned organization/calls | Read programme-level status and approved reports; monitor progress | No document-content access or decision authority unless explicitly granted |
| Platform operator | Operational platform scope, not automatic business-data scope | Health/operations, service administration and controlled support actions | No default access to proposal content; time-bound, approved break-glass access with audit if support access is required |
| Organization administrator | Organization membership administration, if required | Invite/deactivate members and assign approved organization roles | Cannot grant platform-wide privileges or access other organizations |
| System administrator | Cross-platform operational role only if required | Manage platform configuration and support controls | Must not automatically imply unrestricted proposal-content access; separate operational and data-access permissions |

The current `SYSTEM_ADMINISTRATOR` and `GRANT_ADMINISTRATOR` labels must be mapped deliberately. Do not carry forward broad legacy privileges by name alone. Confirm whether `NCST_GRANT_PERSONNEL` and `GRANT_INSTITUTION` are distinct institutional roles or deployment-specific labels.

## Resource ownership and access rules to validate

At minimum, define and test authorization for:
- Organization membership and user administration.
- Grant calls and RFP versions.
- Requirements and requirement verification state.
- Applicants, applications and uploaded documents.
- Pending uploads and manual associations.
- Screening batches/runs and stage-level status.
- Findings, evidence, reviewer notes and decisions.
- Reports, dashboards, audit records and exports.
- Duplication archive records and imported documents.
- Source configuration and integration credentials.

A user may access a child resource only when the server can establish an authorized path to its parent resource and organization. Never authorize a document or finding solely because its opaque ID is known.

## Policy evaluation contract

Centralize authorization behind a small, testable policy interface. Conceptually:

`authorize(principal, action, resource, context) -> allow | deny`

The policy layer must:
- Fail closed when principal, membership, resource owner or policy context is missing.
- Return a consistent forbidden/not-found response strategy that does not disclose cross-organization resource existence.
- Avoid trusting role/tenant fields supplied by request headers or request bodies.
- Keep policy evaluation separate from UI navigation and button visibility.
- Support explicit, logged break-glass procedures without silently bypassing policy.

The exact Python module/API and whether a policy library is needed should be determined during implementation design; avoid introducing a framework without a demonstrated need.

## Database and tenant isolation

The preferred direction is organization-scoped data access enforced in application/repository queries, with PostgreSQL row-level security considered as additional defence in depth.

Before adopting RLS, validate:
- Tenant context is set transaction-locally and cannot leak through pooled connections.
- Background workers establish the correct tenant context for every job.
- Migration, administrative and support paths have explicit, restricted policies.
- Tests prove cross-tenant reads and writes fail even when identifiers are guessed.
- The application does not rely on a privileged database connection that silently bypasses intended row policies.

The final tenant model and RLS decision must be recorded with the PostgreSQL persistence ADR before implementation.

## Consequences

- Every route must be inventoried as public or protected, with action/resource requirements.
- Existing service-level role checks need to be reconciled with a central policy contract.
- Read routes, file downloads, exports and background tasks require the same scrutiny as writes.
- The database schema needs organization membership and ownership relationships before tenant-aware persistence is considered complete.
- The frontend should consume server-provided capabilities for presentation only; it cannot grant permissions.
- Tests must cover both allowed and denied cases and verify that errors do not leak cross-tenant data.
- Existing synthetic demo roles and seed data must be adapted to explicit test organizations and memberships without enabling demo authorization in staging/pilot.

## Security and acceptance criteria

- All API routes are inventoried; unclassified routes are treated as protected.
- Every protected read/write/download/export checks a verified principal and required permission.
- Missing identity, missing membership and unknown policy context fail closed.
- Cross-organization access is denied for calls, applications, documents, findings, reports and audit records.
- Reviewers cannot read or decide on unassigned resources.
- Organization administrators cannot elevate themselves to platform-wide roles.
- Platform operators do not receive automatic access to confidential proposal content.
- Authorization is enforced in service/repository paths, not only in frontend or route UI.
- Background jobs cannot be forged to process another organization's resources.
- Tests cover horizontal/vertical privilege escalation, guessed IDs, bulk endpoints, exports, signed downloads, stale membership and role revocation.
- Audit events capture role/membership changes and defined privileged operations without copying confidential document contents into logs.

## Open questions before final decision

1. Which organizations/tenants are in the first controlled environment: one institution, multiple institutions, or ShakaHive-managed demo tenants only?
2. Who is authorized to invite users and approve organization membership?
3. Which roles are recognized by the institution, and are `NCST_GRANT_PERSONNEL` and `GRANT_INSTITUTION` distinct permissions?
4. Can a reviewer be assigned to individual applications, whole calls, or both?
5. Should programme managers see metadata/status only, or also proposal content and findings?
6. What operational tasks require platform-wide administration, and who can approve break-glass access?
7. Are any cross-organization collaborations or shared calls required in the first release?
8. What audit retention and review requirements apply?

## Implementation boundary

This ADR proposes the policy model but does not finalize institutional roles, tenant topology, PostgreSQL RLS, or a policy framework. Resolve the open questions with stakeholders, record the accepted permission matrix and tenant enforcement strategy, then implement Issue #5 in coordination with ADR-001 and the PostgreSQL persistence work.

## References

- `apps/api/dependencies.py`
- `apps/api/routes/*`
- `services/grant_workflow/service.py`
- `services/grant_workflow/models.py`
- `docs/grant-workflow.md`
- `docs/implementation/phase-0-baseline-audit.md`
- `docs/implementation/phase-1-architecture-and-implementation-plan.md`
- ADR-001
