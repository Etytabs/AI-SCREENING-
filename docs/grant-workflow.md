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
| Duplication | Whole-proposal similarity against other applications in the call and authorized historical records (lexical, or hybrid when embeddings are enabled; optional cross-encoder reranking). Produces a *signal* (`POSSIBLE_DUPLICATION` / `NO_SIGNIFICANT_SIMILARITY` / `NOT_ASSESSABLE`), never a duplication verdict. |
| Text similarity | Shared verbatim passages (8-word shingles) between narrative documents, excluding text quoted from the call document. Signal only; not a plagiarism finding. |
| Novelty | Per-dimension comparison producing `HIGH` / `MEDIUM` / `LOW` / `REVIEW_REQUIRED` signals. Never `FAIL` and never a scientific novelty judgement. |
| Evidence | Validates every citation against extracted text. A `FAIL` without application or inventory evidence is downgraded to `REVIEW_REQUIRED`. |

A stage that raises an error produces a `NOT_ASSESSABLE` finding for that check and the run finishes `PARTIAL`. Sources that cannot be searched (for example RIGMS) are recorded in the run coverage as not searched; they are never treated as "no matches".

## Roles and identity

| Role | Can |
| --- | --- |
| `GRANT_ADMINISTRATOR` | create/edit calls, upload RFPs, verify requirements, upload applications, launch screening, record decisions, read audit |
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

## Limitations

- **Storage is in memory.** Calls, applications, findings and audit events are lost when the API restarts. The repository interface (`services/grant_workflow/repository.py`) is the seam for a PostgreSQL implementation.
- **Identity is not authenticated** (see above).
- **RIGMS is a stub.** `RIGMSGrantDataProvider` always reports itself as unavailable; runs record RIGMS as not searched.
- **External scholarly sources** (Crossref, PubMed Central, arXiv, DOAJ, CORE, institutional repositories) are registered as optional and `NOT_CONFIGURED`; no connector is implemented.
- **Similarity is lexical by default.** Semantic similarity and reranking only run when the ML extras are installed and enabled.
- **Requirement extraction is rule-based.** Requirements phrased unusually may be missed or mis-categorised; that is why administrator verification is mandatory before screening.
- **Scanned PDFs without a text layer** are reported as unreadable; OCR is not implemented.
- Thresholds and rules have only been exercised on synthetic data. Validation on authorized, representative data is required before operational use.

The system does not decide eligibility, duplication, plagiarism, novelty or funding. It produces signals with evidence; every consequential judgement is recorded by a human reviewer.
