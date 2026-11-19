# Architecture and Decision Conflict Register

**Scope:** reconcile feedback proposals with FPDR-001, TAIS-001, ADR-001, ADR-002 and existing implementation.

| ID | Existing/approved context | Conflict or unresolved proposal | Evidence | Required disposition | Status |
|---|---|---|---|---|---|
| DC-01 | FPDR-001 approved | TAIS-001 and code have no rubric/assessment/ranking implementation | `company/product/FPDR-001...`, `docs/architecture/TAIS-001...`, no `AssessmentRun` runtime class | Preserve FPDR; implement only as staged approved engineering work | Approved decision, implementation missing |
| DC-02 | ADR-001 title/status proposes invited-account authentication | Current demo auth is process-local and documented in `services/auth/demo_auth.py` | Main middleware and test evidence | Approve selected provider/mechanism in revised ADR-001; do not describe demo as pilot auth | Proposed revision, not implementation |
| DC-03 | ADR-002 proposed server-side authorization | Current middleware only permits demo grant administrator/applicant workspaces | `apps/api/main.py`, `apps/api/dependencies.py` | Revise/approve permission matrix and implementation; preserve role separation | Proposed revision, implementation missing |
| DC-04 | ADR-002 allows one institution only for MVP | Feedback includes multi-institution readiness | ADR-002 §1/§4 | Keep P3; require separate tenant-isolation ADR/security review before second institution | No decision to implement |
| DC-05 | FPDR-001 separates eligibility from quality | Existing eligibility is a finding/signal stage; no 0–4 assessment | `services/grant_workflow/screening/eligibility.py` | Reuse evidence patterns but create separate eligibility/quality contracts | No conflict; new implementation needed |
| DC-06 | FPDR-001 prohibits missing evidence becoming zero | Some screening confidence heuristic and text overlap remain signals | `ml/scoring/confidence.py`, `screening/similarity.py`, models | Never map unavailable evidence to rating 0; preserve separate non-assessed states | Approved invariant |
| DC-07 | FPDR-001 requires exactly 100.00% applicable scored weights | Existing RFP criteria have no weight | `RfpCriterion` in `services/grant_workflow/models.py` | Create distinct rubric criterion and decimal validation | No universal weights approved |
| DC-08 | FPDR-001 ranking same call/rubric, eligible and complete | Retrieval ranks are candidate rankings | `ml/semantic_matching/hybrid.py`, `rank_candidates` | Never expose retrieval rank as grant rank; implement ranking snapshot separately | No ranking implementation |
| DC-09 | FPDR-001 preserves ties and snapshot | No tie policy/ranking snapshot exists | TAIS-001 unresolved tie policy | Do not invent tie-break; block final ranking until separately decided | Tie-break not approved |
| DC-10 | FPDR-001 four advisory recommendation categories | No recommendation implementation | TAIS-001 §4 contract is proposed | Implement category contract and approval of call bands only after decision | Thresholds not approved |
| DC-11 | FPDR-001 human authority and original AI preservation | Existing finding decisions retain finding, decision and note records | `ReviewerDecision`, `ReviewerNote`, `Human Review DecisionHistory` | Adapt for score adjustments while preserving original criterion assessment | No conflict |
| DC-12 | FPDR-001 external final decision needs separate approval | Existing workflow has confirm/dismiss finding actions, not funding decision | `ReviewerAction` and docs | Do not expose `/final-decisions` until authority/vocabulary/role is approved | Blocked |
| DC-13 | Existing architecture is modular in-process, not microservices | Feedback proposes wider lifecycle/platform services | `docs/architecture/overview.md`, TAIS-001 §1 | Keep internal services in FastAPI; no independent microservice without ADR | No conflict |
| DC-14 | PostgreSQL/pgvector documented but not connected | Docker Compose declares DB and README says stack includes it | `docker-compose.yml`, `services/grant_workflow/repository.py`, `pyproject.toml` | Select persistence ADR; implement adapter/migrations only after approval | Proposed technical choice |
| DC-15 | Phase 1 durable queue/storage plans | Thread pool and in-memory state remain defaults | `build_service()` in `apps/api/dependencies.py` | Complete P0 with a separately selected queue/storage | Technical choice unresolved |
| DC-16 | Pilot remains single institution/synthetic until authorized | Feedback includes public-source, funding, awards, IP and analytics | MVP/ADR/pilot docs | Keep P2/P3 behind institutional authorization; demo must remain synthetic | Institutional approval required |
| DC-17 | FPDR-002 applicant intake | Document absent, although `controlled-demo-tracking.md` identifies FPDR-002 v0.3 as canonical | Repository-wide exact search found no FPDR-002 source file; only `main` and `origin/main` were available, and the checkout is shallow | Recover the approved source from governance records or approve a replacement; do not infer contents | Missing source/recovery action |
| DC-18 | Feedback proposes unified integrity reporting | Text, purpose, plagiarism and funding overlap are separate risk types | This audit and current modules | Do not merge into one misconduct/probability metric | Reporting policy needed |
| DC-19 | Current public/publication features use optional external services | Feedback asks source attribution and comprehensive discovery | Gemini/OpenAlex/adapters | Obtain terms/access, persist source snapshots and coverage | Blocked/external |
| DC-20 | Responsible-AI principles | Synthetic benchmarks only | `data/evaluation/*`, FPDR-001 | No operational accuracy claims or threshold tuning until authorized expert data | Data/label policy approval |

## Approved decisions

- FPDR-001: product behavior and governance.
- TAIS-001: approved staged implementation specification, subordinate to FPDR-001 and ADRs.
- ADR-001/002: existing canonical records, but currently marked proposed revisions and require further technical/owner decisions.
- Single-institution controlled test MVP in ADR-002.
- Separation of ShakaHive Team Administrator and Grant Administrator.
- Human authority and advisory AI.

## Proposed, not approved

- Authentication provider/mechanism.
- Authorization role/permission implementation details.
- Persistence adapter, migration tool, queue, object storage.
- Retention periods.
- External model/provider processing of application content.
- Recommendation thresholds and call bands.
- Tie-breaking.
- Final-decision vocabulary/authority.
- Institution and applicant intake policy.

## Minimum decision records before implementation

1. `ADR-001` revision selecting provider/session and account lifecycle.
2. `ADR-002` revision approving the MVP permission matrix and assignment/conflict/recusal policy.
3. Applicant intake FPDR-002 or documented replacement if FPDR-002 is not the canonical name.
4. ADR-003 PostgreSQL/persistence and migrations.
5. ADR-004 durable jobs.
6. ADR-005 private document storage and retention/deletion.
7. ADR-006 operations, observability and recovery.
8. Product decision for purpose-overlap dimension taxonomy and disposition vocabulary.
9. Product decision for funding-overlap/evidence and award authority.
10. AI/ML evaluation and data-authorization gate.
