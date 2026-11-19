# Current-State Technical and Product Gap Audit

**Audited commit:** `b063c6adc60ace80a9a38cdd24bbd0b9659b9b26`

This audit verifies implementation surfaces and does not certify runtime deployment or institutional readiness.

## 1. Repository and architecture baseline

- Branch: `main`; worktree was clean before this audit.
- Backend: FastAPI/Python; API modules under `apps/api/routes`; workflow logic in `services/grant_workflow`.
- Frontend: Next.js/React/TypeScript in `apps/web`; static demo and live API modes.
- AI/ML: `ml/semantic_matching`, `ml/novelty`, `ml/eligibility`, `ml/plagiarism`, ingestion and evidence modules.
- Documents: PDF/DOCX/TXT extraction in `services/ingestion/` and `services/grant_workflow/documents.py`.
- Current workflow persistence: `InMemoryWorkflowRepository` in `services/grant_workflow/repository.py`.
- Comparison-library persistence: separate SQLite class `DuplicationArchive`; not the workflow data store.
- Current screening jobs: `ThreadPoolJobRunner` in `services/grant_workflow/jobs.py`.
- Demo auth: process-local `DemoAuthentication` in `services/auth/demo_auth.py`; sessions are opaque 15-minute bearer values.
- Docker declares PostgreSQL/pgvector in `docker-compose.yml`, but the workflow API sets no PostgreSQL repository adapter and `pyproject.toml` has no SQLAlchemy/driver/migration dependency.

## 2. API and workflow boundaries

Core routes are in `apps/api/routes/workflow.py` under `/api/v1`:

- `/grants`, `/grants/{call_id}/rfp`, `/grants/{call_id}/requirements`
- `/grants/{call_id}/applications`, `/grants/{call_id}/applications/batch`
- `/applications/{application_id}`, `/documents/{document_id}/content`
- `/grants/{call_id}/screen`, `/applications/{application_id}/screen`
- `/screening-runs/{run_id}`, `/screening-batches/{batch_id}`
- `/findings/{finding_id}`, `/findings/{finding_id}/evidence`, `/findings/{finding_id}/decision`
- `/grants/{call_id}/dashboard`, `/audit`, `/report`

Existing auth routes are `/api/v1/auth/login`, `/me`, `/logout`. All API-v1 business routes except the public API info/login are middleware-gated only for the enabled demo workspace; applicant is blocked from grant workflow routes.

Publications routes include `/api/v1/publications/reconcile`, `/reconcile-pair`, `/sources`, `/search`, `/compare`, `/plagiarism`; duplication routes include `/api/v1/duplication/projects`.

These route paths exist, but route existence is not proof of production authorization or persistence.

## 3. Models and persistence

`services/grant_workflow/models.py` contains call/RFP/criterion, applicant/institution/application/document, run/batch, finding/evidence/similarity match, reviewer decision/note and audit types.

`InMemoryWorkflowRepository` deep-copies Pydantic entities and extracted document content only in process memory. It has no database constraints, migration, backup or organization/assignment scoping. Restart loss is explicitly documented in `docs/grant-workflow.md`.

The only workflow-like persistent implementation found is the SQLite `DuplicationArchive`. It is not a PostgreSQL workflow repository and cannot establish that Docker PostgreSQL is connected.

## 4. Authentication and authorization

Implemented:
- Synthetic workspace sessions and bearer resolution in `services/auth/demo_auth.py`.
- Middleware in `apps/api/main.py` that rejects invalid tokens and applicant access to grant routes.
- Rejection of forged `X-User-Role` and `X-User-Id` by tests.

Not implemented:
- Real invitation, password/magic-link/SSO, account lifecycle or MFA.
- Durable or revocable-at-restart account sessions.
- Canonical user/role/organization/membership entities.
- Call/application/document/export assignment checks on every route.
- Conflict-of-interest declarations or recusal.
- Resource-level review and file download authorization.

The demo credentials are fixed public synthetic credentials; they must not be enabled for production.

## 5. Documents and ingestion

Implemented:
- PDF/DOCX/TXT extraction and page/line data.
- Upload grouping and pending-upload association.
- Document hashes and version numbers.
- Citation locator validation against extracted text.
- Limited OCR/unreadable detection; no OCR implementation.

Missing or unverified:
- Private durable object storage.
- Signature/MIME verification and comprehensive archive/malware controls.
- Document snapshot/immutable submission association.
- Secure short-lived download URLs.
- Retention/deletion/backup lifecycle.

## 6. Background jobs

`ThreadPoolJobRunner` is the default service implementation. Tests use `InlineJobRunner`. The runner has no durable job table, retry policy, replay, dead-letter queue, worker crash recovery or cross-process ownership. API acceptance is not a durable enqueue. This remains `UNVALIDATED/BLOCKED` for pilot operations.

## 7. Evidence and audit

Evidence passages and page/section provenance exist for extracted documents and many screening findings. `FindingEvidence`, `CitationLocator` validation and run coverage are meaningful primitives.

Audit is `AuditLogEntry` storage in `InMemoryWorkflowRepository` and `WorkflowAudit` helpers. It is not append-only/durable, tamper-resistant, protected by resource authorization or independent of the workflow process.

## 8. Interfaces

Genuinely available:
- Grant-call/RFP/requirement, application, screening, findings/evidence and report dashboard.
- Applicant login plus a placeholder applicant dashboard.
- Reviewer decisions/notes and existing audit/report screens.

Missing:
- Applicant drafts/submission/receipt/status/withdrawal/clarification.
- Rubric authoring/approval/criterion assessment/ranking.
- Reviewer assignment/COI/recusal.
- Award/contracts/disbursement/milestones/closeout.
- IP/commercialization/funding-overlap workflows.

## 9. Purpose-overlap audit

The current duplication implementation can detect exact normalized text, substantial/possible overlap and high-level semantic passage similarity. It also has novelty dimensions and shared-concept evidence.

It does **not** create a structured project profile or compare the individual dimensions approved as a purpose-overlap requirement. Candidate rankings describe text or a novelty signal, not a project-purpose equivalence, replication, follow-on or differentiated result.

The test `tests/test_duplication_detection.py::test_same_broad_topic_different_projects_are_not_duplicates` shows topic-only negatives; it does not prove purpose/beneficiary/intervention/output/outcome matching quality.

Recommendation: extend `ml/semantic_matching` retrieval and `services/grant_workflow/screening/similarity.py` primitives, but introduce a separate purpose-overlap module and structured profiles. Do not relabel current duplication scores as purpose classification.

## 10. Plagiarism audit

Components:
- Public discovery: Gemini Google Search grounding in `services/plagiarism/search.py`.
- Public page fetch and lexical window comparison in `services/plagiarism/service.py`.
- Published literature: OpenAlex adapter and abstract comparison.
- Source attribution metadata: `services/plagiarism/attribution.py`.

These are optional, provider-dependent and unvalidated:
- Gemini is operational only with `GEMINI_API_KEY`; no live test proves discovery or fetch quality.
- OpenAlex live retrieval is not enabled or validated; tests replace network calls.
- HTML extraction is simplistic and does not preserve rendered/PDF/source version identity.
- No institutional submission/thesis/report/authorized publication corpus is wired.
- Generic boilerplate and quote/citation handling are not comprehensive.
- Reviewer disposition and exportable plagiarism evidence are not separate domain features.

## 11. Funding-overlap audit

No dedicated funding-overlap implementation exists. The repository has application `requested_amount`, grant call funding fields and historical project outcome metadata, but no award identifiers, funding periods, budget lines, separate award commitments or deliverable overlap. Do not combine this with plagiarism or textual duplication.

## 12. Assessment-engine audit

FPDR-001 and TAIS-001 are approved planning decisions, but no implementation was found. Missing runtime surfaces include rubric draft/approval, criterion assessment, eligibility assessment result, deterministic weighted score, recommendation, ranking snapshot and assessment reports.

Existing eligibility and screening findings can be reused as evidence patterns. `RfpCriterion` is not a rubric criterion: it has no 100% scored-weight guarantee or criterion applicability/0–4 rating semantics.

## 13. Applicant/reviewer workflow audit

Applicant models and an applicant demo workspace exist, but submission/draft/receipt/snapshot/withdrawal/clarification routes do not. Reviewer finding decisions and notes exist, but assignment, conflict declarations, recusal and resource-scoped access do not.

Canonical FPDR-002 could not be found. A repository-wide search found no `FPDR-002` file or canonical document. `docs/implementation/controlled-demo-tracking.md` identifies FPDR-002 v0.3 as a canonical record and references it as the source of demo credentials and status-transition rules, but it does not contain or link to the recoverable approved source.

The available local and remote branch search found only `main` and `origin/main`; both contain references but not the decision file. The local checkout is shallow at commit `b063c6a` and has no other reachable historical commit. A full history recovery action is therefore unresolved by this audit. Governance must recover the approved FPDR-002 v0.3 source from the founder/governance record, or explicitly approve a replacement canonical applicant-intake decision. This audit does not infer, reconstruct or supersede its contents.

## 14. External integrations

RIGMS is a stub in `services/grant_workflow/providers.py` and always unavailable. OpenAlex is optional. Crossref, PMC, arXiv, DOAJ and CORE are registered or partial adapters, not evidence of authorized or complete coverage. Institutional integration requires written authorization and API/data terms.
