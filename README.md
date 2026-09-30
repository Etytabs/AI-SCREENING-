# AI-SCREENING — Research Intelligence Platform

AI/ML-centered research intelligence platform for **grant proposal screening** and **research publication reconciliation**. The MVP is designed as an evidence workspace: AI/ML models surface findings, retrieve supporting evidence, rank similar records, and expose provenance while authorized staff retain the final decision.

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

**Human-in-the-loop principle:** AI produces findings and evidence. It does not independently reject a proposal, declare plagiarism, or make a funding decision.

### 2. AI Publication Reconciliation

The platform also provides the foundation for:

- publication ingestion;
- researcher/entity resolution;
- duplicate detection;
- metadata reconciliation;
- missing-record detection;
- human verification;
- synchronization with an authorized national repository.

International research databases are **optional connectors**, not prerequisites for the local-first MVP.

## Current ML retrieval architecture

The validated retrieval stack is:

`Query → lexical retrieval + sentence embeddings → hybrid ranking → top-N candidates → cross-encoder reranking → evidence → human review`

The system deliberately separates first-stage retrieval from second-stage reranking:

- **Lexical:** token-based baseline.
- **Embedding:** sentence-transformer semantic similarity.
- **Hybrid:** 35% lexical + 65% semantic fusion.
- **Cross-encoder:** jointly scores the query and candidate pair for second-stage reranking.

Default models:

- Embedding: `sentence-transformers/all-MiniLM-L6-v2`
- Cross-encoder: `cross-encoder/ms-marco-MiniLM-L-6-v2`

Both ML runtimes are configurable and disabled by default in normal CI.

## Retrieval validation

Three synthetic benchmarks have been implemented:

1. **Benchmark #1 — baseline:** 4 simple synthetic cases.
2. **Benchmark #2 — adversarial:** 10 harder synthetic cases designed to expose lexical failure modes.
3. **Benchmark #3 — reranker:** the same adversarial corpus with cross-encoder reranking.

Benchmark #3 results on the synthetic adversarial corpus:

| Strategy | Recall@5 | Precision@5 | MRR | nDCG@5 |
| --- | ---: | ---: | ---: | ---: |
| Lexical | 1.00 | 0.24 | 0.562 | 0.667 |
| Embedding | 1.00 | 0.24 | 0.720 | 0.794 |
| Hybrid | 1.00 | 0.24 | 0.745 | 0.814 |
| Hybrid + Cross-Encoder | 1.00 | 0.24 | **0.875** | **0.897** |

These are **synthetic diagnostic results**, not production performance claims. Validation on authorized, representative NRIF/RIGMS data is still required before operational use.

## Evidence and explainability

The MVP follows:

**Prediction → Confidence → Evidence → Explanation → Human decision → Audit trail**

Evidence records can retain:

- source/document ID;
- document version;
- page number;
- chunk ID;
- evidence span;
- citation locator;
- retrieval method;
- model version;
- review status.

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
- screening queue.

The public prototype uses synthetic/demo data and clearly identifies that limitation. Commercial terms are outside the scope of this repository and are agreed separately with stakeholders.

## Data, governance and deployment

The architecture is local-first and designed for controlled institutional deployment.

Important constraints:

- confidential proposal and applicant data;
- role-based access control;
- secure storage and transmission;
- authorized integration with RIGMS;
- human oversight;
- explainable evidence;
- synthetic data until authorized real data is available;
- model/version provenance;
- auditability.

## Stack

- Frontend: Next.js + TypeScript
- API: Python + FastAPI
- AI/ML: Python, scikit-learn, sentence-transformers / Transformers
- Database: PostgreSQL + pgvector
- Documents: PyMuPDF / python-docx
- Testing: pytest + frontend tests
- Deployment: Docker + GitHub Actions

## Repository structure

```text
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
data/
  evaluation/          synthetic benchmark datasets/results
docs/
  ai-ml/               model and evaluation documentation
tests/                 automated tests
```

## Local development

Install backend development dependencies:

`pip install ".[dev]"`

Run tests:

`pytest`

Run linting:

`ruff check .`

For model-backed retrieval:

`pip install ".[ml]"`

Enable embeddings:

`AI_SCREENING_EMBEDDINGS_ENABLED=true`

Enable cross-encoder reranking:

`AI_SCREENING_RERANKER_ENABLED=true`

The GitHub Actions model-backed benchmark workflows are manual so normal CI remains fast and deterministic.

## MVP status

**Implemented and CI-validated:**

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
- presentation-oriented Grant Screening workspace.

**Next validation gate:** test the screening workflow with an authorized and representative dataset, establish operational baselines, validate retrieval/reranking quality, and agree governance/commercial assumptions with stakeholders.

## Prototype disclaimer

This public prototype uses synthetic proposals, historical records and demo eligibility rules. It is **not an official NCST/NRIF screening system** and must not be used for funding, eligibility, plagiarism, or other consequential decisions.
