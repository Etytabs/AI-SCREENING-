# Demo role and screen matrix

## Audit findings

The web and API role enums contain six values. The selector rendered all six labels, although the context only accepted the three stakeholder labels after refresh; legacy roles could still be selected until reload. The web client also translated `NCST_GRANT_PERSONNEL` into the `GRANT_ADMINISTRATOR` API role. That mapping silently treated NCST staff as grant administrators.

The sidebar showed shared grant-operations screens for every role. Page-level checks treated every non-reviewer role as an operator, including institution and applicant labels. The overview suggested applicant-owned submissions and publications, but no Publications route exists and the application list is workspace-wide rather than applicant-scoped. Reviewer assignment scoping and Team Admin account-management screens are also absent. The backend reads the role from caller-supplied headers; this is demo identity, not authentication or production authorization.

The active selector therefore exposes only the existing Grant Administrator workflow. The other roles are deliberately unavailable until their screen scope and capabilities are implemented and approved. Canonical ADRs are unchanged.

## Role-to-screen matrix

| Role | Status and experience | Navigation and routes | Actions and limitations |
|---|---|---|---|
| NCST Grant Personnel | Unsupported; no approved mapping to Grant Administrator | No navigation; dashboard routes redirect to the active demo landing page | Not selectable. The former client-side API alias was removed; no administrator powers are inferred. |
| Grant Institution | Unsupported; institution-specific data view is not implemented | No navigation; dashboard routes redirect | Not selectable. There is no institution-owned application list or institution access scope. |
| Researcher / Applicant | Unsupported; applicant workspace is not implemented | No navigation; dashboard routes redirect | Not selectable. No applicant-owned applications/publications view or applicant actions are fabricated. |
| Grant Administrator | Active demo workflow, backed by the existing legacy API role | Overview (`/dashboard`), Research Check (`/dashboard/check`), Grant Calls (`/dashboard/calls`), Applications and detail (`/dashboard/applications`, `/dashboard/applications/view`), Duplication, Screening, and Report | Existing call/RFP configuration, requirement verification, application upload/association, screening, comparison-library import, evidence review and decisions. These are demo interactions only; the role header is not authenticated. |
| Reviewer | Legacy, unavailable because reviewer assignments are not enforced | No navigation; dashboard routes redirect | Not selectable. A reviewer preview would expose unassigned applications and evidence. |
| System Administrator | Legacy, unavailable; no ShakaHive Team Admin workspace exists | No navigation; dashboard routes redirect | Not selectable. No account, invitation, suspension or role-management actions are exposed. Grant Admin remains distinct from Team Admin. |

## Route and navigation behavior

The active Grant Administrator navigation is derived from `DEMO_ROLE_CONFIG`; route availability and page action capabilities use the same configuration. `/dashboard/report` is explicitly available and has a sidebar entry. Application detail is available below `/dashboard/applications/view`; query-string call/application identifiers remain within their existing pages. Direct navigation to a route not available to the selected role replaces the page content with an unavailable message and redirects to that role's landing page. Persisted inactive role values normalize to the active demo role on refresh.

The public `/` landing page is outside the dashboard role workspace. Hiding navigation, restricting demo routes, and sending `X-User-Role` are not security controls. The API and application remain unauthenticated as described in ADR-001 and ADR-002.
