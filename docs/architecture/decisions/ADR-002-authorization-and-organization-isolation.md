# ADR-002: Authorization and Organization Isolation

- **Status:** Proposed revision — founder-confirmed reviewer assignment scope and review actions; remaining role and administration details require team review
- **Date:** 11 November 2026
- **Decision owners:** Software Developer / AI Platform Developer (technical recommendation); Team Leader (coordination and approval)
- **Implementation owner:** Full-Stack Developer
- **Related:** ADR-001; Phase 0 audit; Phase 1 Architecture & Implementation Plan; GitHub Issue #5

## 1. Context and current repository evidence

The current workflow has role-based action checks in parts of the service layer, but the documented API states that read endpoints do not check a role. The frontend sends caller-selected role and user headers, which are not authenticated. The repository does not establish a complete user-membership model or prove consistent access enforcement for API reads, documents, jobs, exports and audit records.

Authentication in ADR-001 establishes a verified ShakaHive-managed user. This ADR defines how the ShakaHive team grants that user access to the MVP and its resources.

## 2. Founder-confirmed pilot direction

The founder has confirmed:

1. **Initial deployment scope:** one institution, as a test MVP platform.
2. **Access administration:** the ShakaHive team manages user invitations and reviewer assignments.
3. **Reviewer access:** reviewers access the MVP when invited/assigned. GitHub repository access is a separate invitation and is not automatic.
4. **GitHub:** the ShakaHive team decides separately whether a reviewer should be invited to the repository.

The initial scope is therefore a **single-institution controlled test environment**, not a multi-institution SaaS rollout. This does not mean the MVP may assume that every authenticated user can see every record. User-level permissions and reviewer assignment still apply.

The founder's answer does not yet define programme-manager permissions. This ADR deliberately leaves that role disabled/unassigned until the team specifies its required access.

## 3. Decision drivers

- Deny-by-default authorization for every protected API operation.
- A simple, manageable permission model for one institution and a controlled test MVP.
- ShakaHive-controlled invitations, role assignment and reviewer assignment.
- Least privilege and separation of duties.
- Resource-level authorization, not role-only checks.
- Consistent enforcement for reads, writes, downloads, exports and background processing.
- Clear distinction between MVP permissions and GitHub repository permissions.
- Avoid premature multi-tenant complexity while preserving a safe path to future expansion.

## 4. Proposed MVP authorization model

Adopt a centralized, server-side permission policy based on:

- A verified user principal from ADR-001.
- An active MVP account/invitation record.
- A server-side application role assigned by an authorized ShakaHive team administrator.
- The target resource and its workflow state.
- An explicit reviewer assignment when the actor is a reviewer.
- The requested action (read, create, update, upload, screen, decide, export, download or administer).

A role alone is not enough. Every resource access must be checked against the user's account state, assigned role and resource scope.

Do not accept role, reviewer assignment, ownership or permission claims from browser headers, query parameters or request bodies as proof of access.

### Initial organization scope

- Model the first test deployment as one institution/workspace.
- All MVP business data belongs to that configured workspace.
- Do not expose organization switching or cross-organization sharing in the first MVP.
- Do not build a multi-institution administration interface or complex cross-tenant workflows as part of this phase.
- Keep organization/workspace ownership explicit in the data model where this supports integrity and a future migration, but do not claim multi-tenant isolation is implemented merely because an `organization_id` column exists.
- Before any second institution is onboarded, conduct a separate tenant-isolation design and security review covering database, files, jobs, search indexes, exports, audit and backups.

## 5. Proposed MVP roles and permissions

These are proposed application permissions for the controlled test MVP, not institutional job titles. ShakaHive team members assign them individually.

| MVP role | Initial access | Restrictions / notes |
|---|---|---|
| ShakaHive Team Administrator | Manage ShakaHive-controlled MVP accounts: invite/suspend users, assign/revoke application roles and reviewer assignments, and administer workspace access | A distinct platform-administration role. Only specifically authorized ShakaHive team members hold it; privileged actions are audited; individual accounts only; no shared administrator login |
| Grant Administrator / Test Operator | Operate the grant-screening workflow: manage grant calls and RFPs, verify requirements, upload/associate applications, initiate screening and view authorized results | A distinct product/workflow role. It does not automatically grant authority to invite users, administer accounts or change platform-wide roles; reviewer assignment is permitted only if separately delegated |
| Reviewer | Access only the call/application/document/evidence items assigned by the ShakaHive team; add notes and submit review decisions within assigned scope | No user administration, call configuration, reviewer assignment, bulk export or unassigned application access |
| Programme Manager | **Not enabled until permissions are specified and approved** | The founder's response did not define whether this role may see metadata, proposal content, findings, reports or decisions. Do not grant a broad default role. |
| Platform Operator | Operational health and service administration only where needed | No default proposal-content access; any support access must be explicitly approved, time-bound and audited |

The existing code's role labels (`NCST_GRANT_PERSONNEL`, `GRANT_INSTITUTION`, `GRANT_ADMINISTRATOR`, `REVIEWER`, `SYSTEM_ADMINISTRATOR`) are legacy/demo labels. Do not carry them into the new permission model unchanged without mapping each to an approved MVP role and permission set.

### ShakaHive team authority

ShakaHive's company-level operating responsibilities must remain distinct from the grant-screening product's institutional workflow:
- **ShakaHive Team Administrator** manages platform accounts, invitations, application-role assignment/revocation and reviewer assignments.
- **Grant Administrator / Test Operator** operates grant calls, RFPs, applications and screening within the configured test workspace.
- Reviewer assignment may be delegated to a Grant Administrator, but only through an explicit permission; it is not inherent in that role.
- GitHub repository access is decided and administered separately from MVP access.

This separation is intentional even though the current team is delivering the MVP as part of a competition. ShakaHive should be represented as the product/company operating model, not merely as a temporary competition team. Keeping platform administration separate from institutional grant operations creates a clearer responsibility boundary and a more credible path to scaling the product to additional institutions later. The first deployment nevertheless remains a single-institution controlled test MVP; this role separation does not claim that multi-institution capabilities already exist.

The implementation must represent these powers as explicit server-side permissions. Do not make every ShakaHive team member a super-administrator by default; identify which named team members are authorized to administer accounts and role assignments.

## 6. Reviewer assignment and access rules

- A reviewer must have an active, verified MVP account and an explicit assignment before seeing proposal content.
- Support both **call-level** and **application-level** reviewer assignments.
- A call-level assignment grants access to applications within that call, subject to the reviewer's other permissions and the call's active state.
- An application-level assignment grants access only to the specifically assigned application and its permitted documents, findings and evidence.
- The ShakaHive team may use either assignment scope. The effective scope must be explicit, auditable and enforced on every relevant API operation; a reviewer cannot create or broaden their own assignment.
- A reviewer may perform these four actions within their assigned scope:
  1. Add review notes.
  2. Submit a review, including confirming or dismissing a finding.
  3. Request further review or clarification.
  4. Escalate an application for additional assessment.
- Each review action must be validated against workflow state, recorded with the actor, resource, action and timestamp, and remain subject to any required administrator workflow controls.
- A reviewer cannot invite users, change grant requirements, assign reviewers, expand their own scope or access unassigned submissions.
- Removing an assignment or suspending the account must revoke access on subsequent requests and invalidate relevant sessions/capabilities.
- Bulk endpoints, reports, document-content routes, exports and background jobs must apply the same assignment checks.

**Founder-confirmed direction:** support both call-level and application-level assignments, and permit the four review actions listed above. These permissions apply only within the reviewer's assigned scope.

## 7. GitHub access is a separate authorization domain

- MVP access and GitHub repository access are independent.
- The ShakaHive team invites a reviewer to GitHub only when repository collaboration is required.
- Grant the least GitHub permission appropriate to the contribution (for example, read-only access for review where supported).
- Do not grant GitHub access merely because someone is an MVP reviewer.
- Do not grant MVP access merely because someone is a repository collaborator.
- GitHub repository permissions do not control proposal/document access in the MVP.
- Record and periodically review GitHub collaborators separately from MVP users.

## 8. Enforcement layers

1. **API boundary:** every protected route declares its authentication and permission requirement. Public routes are explicitly allowlisted.
2. **Application/service layer:** domain operations authorize the actor against the target resource and workflow state.
3. **Repository/data layer:** queries are scoped to the single configured workspace and relevant resource assignment. Do not rely only on frontend filtering.
4. **Document access:** documents remain private; each read/download verifies the user's application permission and reviewer assignment.
5. **Background jobs:** jobs carry trusted workspace, actor and resource identifiers from the authorized enqueue operation. Workers validate resource scope and current state.
6. **Audit:** invitations, account suspension, role changes, reviewer assignments, exports, document access and reviewer decisions generate protected audit events.

Centralize policy behind a testable contract such as:

`authorize(principal, action, resource, context) -> allow | deny`

Fail closed when identity, account status, role, assignment, resource ownership or policy context is missing. Do not introduce a policy framework/library unless implementation demonstrates a need.

## 9. Consequences

- The first MVP can use a simpler single-workspace model rather than implementing a full multi-institution tenant administration product.
- Every protected read/write/download/export still needs backend authorization.
- A server-side user, role and reviewer-assignment model is required.
- ShakaHive Team Administrator and Grant Administrator are separate roles with distinct permission boundaries; an individual may hold both only if explicitly assigned both roles.
- The ShakaHive team needs a defined administrator roster and account-management procedure.
- Programme Manager access remains unimplemented until explicitly defined.
- GitHub collaborator management remains outside the MVP authorization system.
- A second institution requires a new architecture/security decision before onboarding.
- Existing synthetic demo roles and seed data must be mapped to the new test-workspace permissions without enabling demo authorization in the MVP deployment.

## 10. Security and acceptance criteria

- All API routes are inventoried; unclassified routes are treated as protected.
- Every protected read/write/download/export checks a verified principal and required permission.
- Only invited, active users can access the MVP.
- Role assignment and reviewer assignment are performed only by authorized ShakaHive team administrators.
- Reviewers cannot read or decide on unassigned resources.
- Cross-resource access is denied even when an identifier is guessed.
- Account suspension and assignment removal take effect on subsequent requests.
- The single-workspace boundary is enforced server-side, not just by UI filters.
- Documents, findings, reports, audit records and background jobs follow the same permission rules.
- GitHub access is not inferred from MVP roles, and MVP access is not inferred from GitHub membership.
- Tests cover horizontal/vertical privilege escalation, guessed IDs, bulk endpoints, exports, document downloads, stale assignments and revoked accounts.
- Privileged account and permission changes are audited without copying proposal content into logs.

## 11. Remaining questions for team confirmation

1. Which named ShakaHive team members will have permission to invite users and administer roles?
2. What should the Programme Manager role be allowed to see and do? Until decided, it remains disabled.
3. What minimum GitHub permission is needed when a reviewer is separately invited to the repository?

## 12. Implementation boundary

This ADR incorporates the founder's initial pilot scope and operating model, including the separation of ShakaHive platform administration from grant-workflow administration. It does not yet authorize multi-institution onboarding, define Programme Manager permissions, select an authentication provider, or implement application authorization. Resolve the remaining questions, approve the MVP permission matrix and then implement Issue #5 in coordination with ADR-001.

## References

- `apps/api/dependencies.py`
- `apps/api/routes/*`
- `services/grant_workflow/service.py`
- `services/grant_workflow/models.py`
- `docs/grant-workflow.md`
- `docs/implementation/phase-0-baseline-audit.md`
- `docs/implementation/phase-1-architecture-and-implementation-plan.md`
- ADR-001
