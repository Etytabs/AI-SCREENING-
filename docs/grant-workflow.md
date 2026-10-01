# Grant-call screening workflow

This document describes the grant-call workflow that is implemented in this repository: what each step does, the REST API behind it, the roles, the synthetic demo data and the current limitations. It only describes behaviour that exists in the code today.

## Workflow

| Step | Who | What happens | Where |
| --- | --- | --- | --- |
| 1. Create grant call | Grant Administrator | Name, organization, reference, window, funding range, currency, domains. Status `DRAFT`. | Dashboard → Grant Calls |
| 2. Upload call document (RFP) | Grant Administrator | PDF, DOCX or TXT. Re-uploading creates a new version and supersedes unconfirmed requirements. Status `REQUIREMENTS_PENDING`. | Grant Calls → call |
| 3. Requirement extraction | System | Deterministic, rule-based extraction (`services/grant_workflow/rfp_extraction.py`). Every requirement quotes the sentence it came from with page/section. No LLM, no invented requirements. | automatic |
| 4. Verify requirements | Grant Administrator | Verify, edit (recorded as administrator edit), reject (reason required), add manually (recorded as administrator-authored), deactivate/reactivate. | Grant Calls → call |
| 5. Confirm | Grant Administrator | Only possible when no active requirement is still unverified. Status `READY_FOR_SUBMISSIONS`. | Grant Calls → call |
| 6. Upload applications | Grant Administrator | One application, several files, or a ZIP. Files are grouped by folder (`REF/file.pdf`) or prefix (`REF__file.pdf`); anything else is held for manual association. | Applications |
| 7. Batch screening | Grant Administrator | Runs asynchronously in a thread pool. Eight stages per application (below). Status `SCREENING`, then `REVIEW` when every run has finished. | Screening |
| 8. Dashboard | all roles | Requirements, submissions, screening signal counts, review progress, source coverage. | Overview |
| 9. Results table | all roles | Filter by search text, eligibility, completeness, novelty signal, review progress, similarity flag; sort. | Applications |
| 10. Review workspace | all roles | Documents with highlighted evidence on the left, findings on the right, evidence drawer per finding. | Applications → application |
| 11. Reviewer decision | Reviewer, Grant Administrator | Confirm, dismiss, request further review or escalate. A rationale note is required. Notes can also be added without a decision. | evidence drawer |
| 12. Audit trail | Grant Administrator, System Administrator | Every workflow action with actor, time and details. | Review |
| 13. Report | all roles | Printable report: verified requirements, per-application findings, evidence counts, reviewer decisions, disclaimer. | Overview → Open report |

### Screening stages

| Stage | Behaviour |
| --- | --- |
| Document extraction | Uses the text extracted at upload. If no document is readable the run is `BLOCKED` and the remaining stages are skipped. |
| Requirement mapping | Maps each verified requirement to the most relevant passages. |
| Eligibility | Checks verified eligibility requirements (country, amount ceiling, duration, required phrases, keyword coverage). A value that cannot be found gives `REVIEW_REQUIRED`, never `FAIL`. |
| Completeness | Checks required documents. `FAIL` only when every file was readable and the document is absent; unreadable files, conditional requirements and section-only matches give `REVIEW_REQUIRED`. |
| Duplication | Exact normalized text, substantial content reuse and optional semantic similarity against same-call proposals, earlier submissions across calls, and the persistent library of submitted/funded projects. Results include match classification and paired passages for human review. |
| Text similarity | Shared verbatim passages (8-word shingles) between narrative documents, excluding text quoted from the call document. Signal only; not a plagiarism finding. |
| Novelty | Per-dimension comparison producing `HIGH` / `MEDIUM` / `LOW` / `REVIEW_REQUIRED` signals. Never `FAIL` and never a scientific novelty judgement. |
| Evidence | Validates every citation against extracted text. A `FAIL` without application or inventory evidence is downgraded to `REVIEW_REQUIRED`. |

A stage that raises an error produces a `NOT_ASSESSABLE` finding for that check and the run finishes `PARTIAL`. Sources that cannot be searched (for example RIGMS) are recorded in the run coverage as not searched; they are never treated as "no matches".

## Roles and identity

| Role | Can |
| --- | --- |
| `NCST_GRANT_PERSONNEL` | create/edit calls, upload RFPs, verify requirements, upload applications, launch screening, record decisions, read audit |
| `GRANT_INSTITUTION` | create/edit calls, upload RFPs, verify requirements, upload applications, launch screening, record decisions, read audit |
| `GRANT_ADMINISTRATOR` | legacy equivalent of the operational grant-administrator permissions |
| `REVIEWER` | read calls, applications, findings and evidence; record decisions and notes |
| `SYSTEM_ADMINISTRATOR` | administrative call actions, sources, audit |

**Identity is a demo mechanism.** The frontend sends `X-User-Role` and `X-User-Id` headers chosen in the sidebar. They are not authenticated. On actions that need a role, a missing role header returns `401`, an unknown role `400` and a disallowed action `403`. A real deployment must replace this with the institution's identity provider.

## REST API

Base path `/api/v1`. Every write action and the audit trail need `X-User-Role`; read endpoints do not check a role in this demo build. Errors return `{"detail": "..."}` with 400, 401, 403, 404, 409 or 422.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/session` | Demo identity info |
| POST, GET | `/grants` | Create / list grant calls |
| GET, PATCH | `/grants/{call_id}` | Read / update a call (status may only be set to `CLOSED` or `ARCHIVED`) |
| POST, GET | `/grants/{call_id}/rfp` | Upload the call document (multipart `file`) / list versions |
| GET, POST | `/grants/{call_id}/requirements` | List / add a requirement |
| POST | `/grants/{call_id}/requirements/confirm` | Confirm requirements, open submissions |
| PATCH | `/requirements/{id}` | Edit a requirement |
| POST | `/requirements/{id}/verify` | `{"decision": "VERIFY" \| "REJECT", "note"}` |
| POST | `/requirements/{id}/active` | `{"active": bool}` |
| POST | `/grants/{call_id}/applications` | One application: multipart `files`, optional `reference` |
| POST | `/grants/{call_id}/applications/batch` | Several applications or ZIP: multipart `files` |
| GET | `/grants/{call_id}/applications` | Results rows; query `q`, `flagged`, `screening_status`, `eligibility`, `completeness`, `novelty`, `review_progress`, `processing_status` |
| GET | `/grants/{call_id}/pending-uploads` | Files awaiting manual association |
| POST | `/pending-uploads/{id}/associate` | `{"application_id"}` or `{"new_reference"}` |
| GET | `/applications/{id}` | Application detail, documents, latest run |
| POST | `/applications/{id}/documents` | Add documents to an application |
| GET | `/documents/{id}/content` | Extracted text by page and line |
| POST | `/grants/{call_id}/screen` | Start a batch (`202`); optional `{"application_ids": [...]}` |
| POST | `/applications/{id}/screen` | Screen one application |
| GET | `/screening-runs/{id}` | Run with per-stage status and coverage |
| GET | `/screening-batches/{id}` | Batch progress per stage and per run |
| GET | `/applications/{id}/findings` | Findings of the latest run |
| GET | `/findings/{id}` | Finding with decisions and notes |
| GET | `/findings/{id}/evidence` | Evidence items |
| POST | `/findings/{id}/decision` | `{"action": "CONFIRM" \| "DISMISS" \| "REQUEST_REVIEW" \| "ESCALATE", "note"}` |
| POST | `/findings/{id}/notes` | `{"note"}` |
| GET | `/grants/{call_id}/dashboard` | Dashboard summary |
| GET | `/grants/{call_id}/audit` | Audit trail (Grant/System Administrator) |
| GET | `/grants/{call_id}/report` | Screening report |
| GET | `/sources` | Source registry and access status |
| GET, POST | `/duplication/projects` | List comparison-library metadata / import a prior or funded project (multipart `file`, `title`, `source_type`, optional `reference`, `year`, `organization`) |
| GET | `/demo/rfp`, `/demo/applications.zip` | Synthetic demo files for trying the upload steps |

Interactive OpenAPI documentation is served at `/docs` when the API runs.

## Synthetic demo data

On start-up the API seeds one synthetic call, **"Climate Resilience Research Grant 2026 (synthetic demo)"**, modelled loosely on an NCST/NRIF-style call, with five synthetic applications (`APP-001` … `APP-005`) and synthetic historical records. Everything seeded is marked `data_origin = SYNTHETIC` and shown with a **SYNTHETIC** badge in the UI; reports include a synthetic-data notice.

The seed verifies the extracted requirements automatically, with the note *"Verified automatically by the synthetic demo seed; not a human verification."*, so the demo can be screened immediately. Calls you create yourself go through manual verification.

Uploaded files are marked `UPLOADED`. No real applicant, NCST, NRIF or RIGMS data is included in this repository. Disable the seed with `AI_SCREENING_DEMO_SEED=false`.

## Configuration

| Variable | Default | Effect |
| --- | --- | --- |
| `AI_SCREENING_DEMO_SEED` | `true` | Seed the synthetic demo call at API start-up |
| `AI_SCREENING_CORS_ORIGINS` | `http://localhost:3000,http://localhost:3001` | Allowed browser origins (comma separated) |
| `AI_SCREENING_SCREENING_WORKERS` | `2` | Background screening threads |
| `AI_SCREENING_DUPLICATION_DB` | `data/private/duplication.sqlite3` | SQLite comparison library; put this on persistent storage when hosting the API |
| `AI_SCREENING_RIGMS_URL` | unset | Marks RIGMS as configured (`AUTH_REQUIRED`); no RIGMS calls are made without an agreed API specification |
| `AI_SCREENING_EMBEDDINGS_ENABLED` | `false` | Hybrid (lexical + embedding) similarity; requires `pip install ".[ml]"` |
| `AI_SCREENING_RERANKER_ENABLED` | `false` | Cross-encoder reranking of similarity candidates |
| `NEXT_PUBLIC_API_BASE_URL` (web) | `http://localhost:8000` | API base URL used by the browser |

No API keys or credentials are used or stored by the frontend.

## Running locally

```bash
# API (from the repository root)
pip install ".[dev]"
uvicorn apps.api.main:app --port 8001

# Web (from apps/web)
npm install
# point the UI at the API
echo NEXT_PUBLIC_API_BASE_URL=http://localhost:8001 > .env.local
npm run dev
```

Open `http://localhost:3000/dashboard`.

Checks: `pytest`, `ruff check .`, and in `apps/web`: `npm run lint`, `npx tsc --noEmit`, `npm test`, `npm run build`.

## Duplication workflow

1. Open **Duplication** in the dashboard. Import readable PDF, DOCX or UTF-8 TXT proposals as previously submitted applications or funded projects. Add the project title and optional reference, year and organization. Imports are limited to 20 MB and require a Grant Administrator or System Administrator role.
2. Upload submissions through the existing Applications workflow. Real uploaded narratives are automatically saved to the local comparison library; synthetic demo applications are not persisted there.
3. Run screening. Duplication compares each proposal to other applications in the same call, earlier submissions across calls, available historical providers and imported projects. It excludes the application itself and avoids counting its live record and saved snapshot twice. For revised files, it uses the latest version; CVs, declarations and budgets are not substitutes for proposal content.
4. Open the duplication finding. Review exact-text, substantial-similarity or possible-similarity matches, both passages, source identity and year, and available page citations. Scores measure similarity, not the probability of misconduct. Confirm or dismiss through the existing human decision controls.

After importing additional projects, rerun screening to include them. Existing findings remain records of their original run. Match totals count all assessed candidates; the evidence view shows up to five strongest matches. Missing sources and unreadable narratives are reported explicitly, and a no-match result applies only to the records actually searched.

The comparison library survives API restarts. Back up its SQLite file (including an active WAL, or use SQLite backup) and configure a persistent volume for hosted deployments. The static website calls the API for imports and screening; deploying the frontend alone does not run these features. RIGMS and external funding databases still require authorized connectors; use library imports for records you have available.

The existing eligibility rules and requirement inputs are unchanged. Duplication source expansion happens only inside the duplication stage.

## Limitations

- **Workflow storage is in memory.** Calls, applications, findings and audit events are lost when the API restarts. The duplication comparison library persists separately in SQLite. The repository interface (`services/grant_workflow/repository.py`) is the seam for a PostgreSQL implementation.
- **Identity is not authenticated** (see above).
- **RIGMS is a stub.** `RIGMSGrantDataProvider` always reports itself as unavailable; runs record RIGMS as not searched.
- **External scholarly sources** (Crossref, PubMed Central, arXiv, DOAJ, CORE, institutional repositories) are registered as optional and `NOT_CONFIGURED`; no connector is implemented.
- **Duplication uses text matching by default.** It detects identical text and substantial lexical reuse without downloading models. Semantic paraphrase detection and reranking only run when the ML extras are installed and enabled; text matching alone cannot reliably detect proposals rewritten with different vocabulary.
- **Requirement extraction is rule-based.** Requirements phrased unusually may be missed or mis-categorised; that is why administrator verification is mandatory before screening.
- **Scanned PDFs without a text layer** are reported as unreadable; OCR is not implemented.
- Thresholds and rules have only been exercised on synthetic data. Validation on authorized, representative data is required before operational use.

The system does not decide eligibility, duplication, plagiarism, novelty or funding. It produces signals with evidence; every consequential judgement is recorded by a human reviewer.
