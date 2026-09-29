# AI-SCREENING — Research Intelligence Platform

AI/ML-centered platform for intelligent grant proposal screening and research publication reconciliation.

## Pilot modules

1. **AI Grant Screening** — eligibility, semantic similarity, duplicate detection, plagiarism/text overlap, explainable confidence, human review, audit trail.
2. **AI Publication Reconciliation** — ingestion, researcher/entity resolution, duplicate detection, metadata reconciliation, missing-record detection, human verification, synchronization.

## Architecture

The platform separates deterministic rules, machine-learning models, semantic retrieval, and LLM reasoning. The LLM is an assistive component, not the sole decision-maker.

Pipeline: Ingestion → Extraction → Validation → AI/ML Analysis → Confidence → Evidence → Human Review → Audit → Synchronization

## Stack

- Frontend: Next.js + TypeScript
- API: Python + FastAPI
- AI/ML: Python, scikit-learn, sentence-transformers/Transformers
- Database: PostgreSQL + pgvector
- Documents: PyMuPDF / python-docx
- Testing: pytest + frontend tests
- Deployment: Docker + GitHub Actions

The repository is intentionally structured for a local-first pilot. International research databases can later be added as connectors without making them a prerequisite for the core platform.
