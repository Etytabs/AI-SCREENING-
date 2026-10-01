# shakaHive — Research Intelligence Platform

AI/ML-centered research intelligence platform for grant proposal screening, grant lifecycle intelligence, and research publication reconciliation. The system is designed as an evidence workspace: AI/ML models surface findings, retrieve supporting evidence, reconcile records, and expose provenance while authorized staff retain the final decision.

## NCST / NRIF alignment reinforcement

The FY 2025-2026 NCST Annual Report strengthens the case for a platform that sits alongside—not replaces—the national research management infrastructure. The report describes the upgraded RIGMS as supporting grant management from applications through project closing, with improved workflow automation, security, monitoring, reporting and data management. It also describes the Rwanda Research and Innovation Repository as a national knowledge hub for research outputs and identifies fragmented resources, weak interoperability, limited local AI/ML datasets and limited visibility of research as ecosystem gaps.

shakaHive therefore now models an NCST-aligned research intelligence layer across the grant lifecycle:

Application → Administrative screening → Technical review → Award → Implementation → M&E → Closeout → Research-to-impact

### Source hierarchy

The platform distinguishes between:

1. Official strategic/procedural sources — NCST reports and the active NRIF procedures.
2. Call-specific authoritative sources — the active RFP/RFA/call package.
3. Institutional systems — RIGMS and the Rwanda Research and Innovation Repository.
4. Configured AI rules — machine-readable rules approved by authorized staff.
5. Demo rules — synthetic rules that can never silently become production rules.

Direct RIGMS/repository integration is deliberately marked as authorization-dependent. No public API or credentials are assumed.

### New NCST-alignment APIs

- GET /api/v1/ncst/requirements — source registry and requirement domains.
- GET /api/v1/ncst/lifecycle — application-to-impact lifecycle model.
- GET /api/v1/ncst/monitoring-indicators — structured M&E evidence indicators.

Operational call-specific rules require the authorized source document, version/provenance and human approval before activation.

## Grant-call screening workflow

The dashboard (`/dashboard`) runs a complete grant-call workflow: create a call → upload the call document → deterministic requirement extraction → administrator verification → confirm → upload applications (single, multiple or ZIP) → asynchronous batch screening (extraction, requirement mapping, eligibility, completeness, duplication, text similarity, novelty, evidence validation) → dashboard and results table → review workspace with evidence drawer → reviewer decisions with rationale → audit trail → report.

See [docs/grant-workflow.md](docs/grant-workflow.md) for the steps, REST API, roles, configuration, synthetic demo data and limitations. The API seeds one clearly labelled synthetic climate call with five synthetic applications; storage is in memory and identity is a demo header, not authentication.

## MVP focus

### 1. AI Grant Screening

The current MVP demonstrates an end-to-end screening workflow for grant proposals:

- document ingestion and text extraction;
- completeness assessment;
- machine-readable eligibility rules;
- lexical, embedding and hybrid semantic retrieval;
- duplicate / near-duplicate candidate detection;
- cross-encoder reranking;
- text-overlap evidence;
- evidence chunks with page/chunk provenance;
- confidence scoring and model contracts;
- human review and decision history;
- append-only audit events;
- source/run coverage states.

Human-in-the-loop principle: AI produces findings and evidence. It does not independently reject a proposal, declare plagiarism, or make a funding decision.

### 2. Grant lifecycle and M&E intelligence

The reinforced architecture extends beyond pre-award screening to the monitoring responsibilities described by NCST:

- quarterly technical-progress evidence;
- expected outputs and achievements;
- financial management and compliance evidence;
- datasets, experiments and field/laboratory evidence;
- implementation risks and support needs;
- change detection across submitted reports;
- closeout evidence reconciliation;
- research-to-impact, technology-transfer and commercialization evidence.

This is an AI evidence layer for M&E—not an automated funding or compliance decision engine.

### 3. AI Publication Reconciliation

The platform also provides the foundation for:

- publication ingestion;
- researcher/entity resolution;
- duplicate detection;
- metadata reconciliation;
- missing-record detection;
- human verification;
- synchronization with an authorized national repository.

International research databases are optional connectors, not prerequisites for the local-first MVP.

## NCST Annual Report → product requirements

The report identifies several ecosystem needs that map directly to the architecture:

| NCST-reported need | shakaHive response |
| --- | --- |
| Fragmented research outputs/resources | Evidence registry + repository reconciliation |
| Poor interoperability | Normalized source adapters + provenance-preserving records |
| Limited visibility of research | Semantic retrieval + missing/duplicate publication detection |
| Limited local AI/ML datasets | Local-first architecture and authorized-data evaluation gates |
| Data sovereignty concerns | Controlled deployment, provenance and authorization boundaries |
| Limited AI/Data Science skills | Explainable workflows and reusable evidence tooling |
| Research duplication | Semantic similarity, entity resolution and duplicate detection |
| Stronger governance/accountability | Audit trail, source versions, reviewer actions |
| Quarterly M&E of funded projects | Structured monitoring indicators and evidence comparison |
| Research-to-impact gap | Impact/commercialization lifecycle stage and evidence model |

The report's proposed priorities also emphasize resource visibility, governance, emerging skills, academia-industry collaboration, sustainable financing, open data and interoperability. These are treated as architectural alignment targets rather than claims that shakaHive already solves the national problems.

## Current ML retrieval architecture

The validated retrieval stack is:

Query → lexical retrieval + sentence embeddings → hybrid ranking → top-N candidates → cross-encoder reranking → evidence → human review

The system deliberately separates first-stage retrieval from second-stage reranking:

- Lexical: token-based baseline.
- Embedding: sentence-transformer semantic similarity.
- Hybrid: 35% lexical + 65% semantic fusion.
- Cross-encoder: jointly scores the query and candidate pair for second-stage reranking.

Default models:

- Embedding: sentence-transformers/all-MiniLM-L6-v2
- Cross-encoder: cross-encoder/ms-marco-MiniLM-L-6-v2

Both ML runtimes are configurable and disabled by default in normal CI.

## Retrieval validation

Three synthetic benchmarks have been implemented:

1. Benchmark #1 — baseline: 4 simple synthetic cases.
2. Benchmark #2 — adversarial: 10 harder synthetic cases designed to expose lexical failure modes.
3. Benchmark #3 — reranker: the same adversarial corpus with cross-encoder reranking.

Benchmark #3 results on the synthetic adversarial corpus:

| Strategy | Recall@5 | Precision@5 | MRR | nDCG@5 |
| --- | ---: | ---: | ---: | ---: |
| Lexical | 1.00 | 0.24 | 0.562 | 0.667 |
| Embedding | 1.00 | 0.24 | 0.720 | 0.794 |
| Hybrid | 1.00 | 0.24 | 0.745 | 0.814 |
| Hybrid + Cross-Encoder | 1.00 | 0.24 | 0.875 | 0.897 |

These are synthetic diagnostic results, not production performance claims. Validation on authorized, representative NRIF/RIGMS data is still required before operational use.

## Evidence and explainability

The MVP follows:

Prediction → Confidence → Evidence → Explanation → Human decision → Audit trail

For grant lifecycle intelligence, the evidence chain can additionally retain:

- project/report version;
- reporting period and lifecycle stage;
- milestone/output identifier;
- financial evidence locator;
- dataset/experiment evidence;
- impact/commercialization evidence;
- source system and synchronization timestamp;
- reviewer action and rationale.

Source failures are represented explicitly and are not treated as zero evidence.

## Stakeholder MVP

The presentation MVP is designed around a real screening workspace:

- proposal/document viewer;
- AI screening readout;
- completeness;
- eligibility;
- semantic similarity;
- text-overlap evidence;
- provenance/model contract;
- reviewer actions;
- screening queue;
- NCST/NRIF requirement source map.

The public prototype uses synthetic/demo data and clearly identifies that limitation. Commercial terms are outside the scope of this repository and are agreed separately with stakeholders.

## Data, governance and deployment

The repository `main` branch is the single source of truth for the application code. The deployment topology is intentionally simple:

- **Frontend:** Cloudflare Pages, deployed from GitHub `main`.
- **API:** Render, serving the FastAPI application.
- **Repository:** GitHub `main` contains the authoritative Next.js frontend, FastAPI backend and AI/ML services.
- **Preview URLs:** Cloudflare-generated preview URLs are deployment artifacts, not separate source branches.

For the Cloudflare Pages project, configure the Git integration to this repository and the `main` production branch, with the web app rooted at `apps/web`. Set `NEXT_PUBLIC_API_BASE_URL` to the deployed Render API URL. Do not use GitHub Pages for production deployment.

Important constraints:

- confidential proposal and applicant data;
- role-based access control;
- secure storage and transmission;
- authorized integration with RIGMS;
- authorized repository synchronization;
- human oversight;
- explainable evidence;
- synthetic data until authorized real data is available;
- model/version provenance;
- auditability;
- explicit data-sovereignty boundaries;
- approval gates before activating call-specific rules.

## Stack

- Frontend: Next.js + TypeScript
- API: Python + FastAPI
- AI/ML: Python, scikit-learn, sentence-transformers / Transformers
- Database: PostgreSQL + pgvector
- Documents: PyMuPDF / python-docx
- Testing: pytest + frontend tests
- Deployment: Docker + GitHub Actions

## Repository structure

apps/
  api/                 FastAPI application
  web/                 Next.js frontend
ml/
  eligibility/         deterministic eligibility rules
  semantic_matching/   lexical, embedding, hybrid and reranking models
  evaluation/          retrieval metrics and benchmarks
services/
  evidence/            provenance and evidence chain
  human_review/        reviewer decisions
  ingestion/           document extraction and chunking
  audit/               audit events
  ncst_requirements/   NCST/NRIF sources, requirements and lifecycle alignment
data/
  evaluation/          synthetic benchmark datasets/results
docs/
  ai-ml/               model and evaluation documentation
tests/                 automated tests

## Local development

Install backend development dependencies:

pip install ".[dev]"

Run tests:

pytest

Run linting:

ruff check .

For model-backed retrieval:

pip install ".[ml]"

Enable embeddings:

AI_SCREENING_EMBEDDINGS_ENABLED=true

Enable cross-encoder reranking:

AI_SCREENING_RERANKER_ENABLED=true

The GitHub Actions model-backed benchmark workflows are manual so normal CI remains fast and deterministic.

## MVP status

Implemented:

- evidence integrity;
- document extraction and provenance;
- deterministic eligibility evaluation;
- hybrid retrieval;
- embedding runtime;
- retrieval evaluation;
- adversarial benchmark;
- cross-encoder reranking;
- human review primitives;
- audit primitives;
- NCST/NRIF source and requirement alignment layer;
- grant lifecycle and M&E indicator model;
- presentation-oriented Grant Screening workspace.

Next validation gate: obtain authorized representative NRIF/RIGMS/repository data and integration access, validate call-specific rules against the active source documents, establish operational retrieval and screening baselines, validate M&E evidence workflows, and agree governance with NCST stakeholders.

## Prototype disclaimer

This public prototype uses synthetic proposals, historical records and configured alignment metadata. It is not an official NCST/NRIF screening system and must not be used for funding, eligibility, plagiarism, compliance, or other consequential decisions.

## Free MVP publishing

The Next.js presentation frontend is configured for a static export and can be published at no hosting cost using GitHub Pages.

Deployment flow:

push to main → Next.js static build → GitHub Pages deployment

GitHub Pages hosts the static presentation only. The FastAPI screening endpoint is not hosted by GitHub Pages; live document upload and screening require a separately deployed API. The synthetic presentation remains usable without the API.

The presentation MVP includes the screening workspace, evidence-oriented findings, human-review workflow, screening queue, NCST/NRIF requirement source map and the grant-call screening workflow.
Cloudflare Pages deployment verified.


## Public-source similarity evidence

AI-SCREENING can search public web sources through Gemini Google Search grounding and attach the discovered source URL to a similarity finding. The comparison service then fetches the public page, computes an explicit similarity signal, and attempts to resolve author, publisher and publication metadata from the page. Results are always marked REVIEW_REQUIRED; the platform does not make an automatic plagiarism verdict.

Configure the backend with GEMINI_API_KEY and optionally AI_SCREENING_GEMINI_MODEL. The key must remain server-side. The endpoint is GET /api/v1/publications/plagiarism?text=...&limit=5.

Google's grounding response provides structured URL citations that can be surfaced in an application. Google documents this as a citation/grounding capability, while pricing and model availability can change; treat the Google provider as replaceable rather than a hard dependency.
