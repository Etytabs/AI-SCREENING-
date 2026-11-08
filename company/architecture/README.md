# ShakaHive Platform Architecture

**Status:** Proposed target architecture; distinguish from currently implemented prototype behaviour.  
**Category:** Research Intelligence  
**First product:** AI-Assisted Grant Screening.

## 1. Architecture principles

- Modular boundaries around workflow, ingestion, rules, ML, evidence, review and audit.
- Evidence and provenance are first-class data.
- Human authority for consequential decisions.
- Tenant and institution isolation for multi-institution deployment.
- Secure-by-default handling of confidential proposal data.
- Replaceable AI providers and external connectors.
- Observable asynchronous processing and recoverable workflows.
- Explicit source coverage and unavailable-source states.

## 2. Logical architecture

```text
Users: Grant Administrators | Reviewers | Programme Managers
                         |
              Web Application
           Next.js + TypeScript
                         |
                Application API
          FastAPI | Auth | RBAC | Workflow
                         |
  +-----------+----------+----------+-----------+
  |           |          |          |           |
Rules       AI/ML      Ingestion   Evidence    Review
Engine      Engine     & Parsing   Service     & Audit
  |           |          |          |           |
  +-----------+----------+----------+-----------+
                         |
          Data and Infrastructure Layer
 PostgreSQL + pgvector | Object Storage | Job Queue
             Monitoring | Backups | Logs
                         |
      Authorized institutional integrations
        RIGMS / repositories / public sources
```

## 3. Current repository stack

The README describes Next.js + TypeScript, Python + FastAPI, scikit-learn and sentence-transformers/Transformers, PostgreSQL + pgvector as the database technology, PyMuPDF/python-docx, Docker and GitHub Actions. Deployment documentation describes Cloudflare Pages for the frontend and Render for the API.

Do not infer that every target component is already deployed or production-ready.

## 4. Main domain components

- Organisation and user access.
- Grant calls and versioned call documents.
- Requirements and approval state.
- Applications and document versions.
- Screening runs and per-stage status.
- Findings, evidence and source coverage.
- Reviewer decisions and rationale.
- Audit events and reports.
- Model/provider registry and evaluation results.
- Integration adapters and synchronization history.

## 5. Screening sequence

1. Validate upload and associate files.
2. Extract text and preserve page/chunk provenance.
3. Map text to verified call requirements.
4. Apply deterministic eligibility and completeness rules.
5. Retrieve lexical and semantic similarity candidates.
6. Rerank candidate passages where configured.
7. Validate evidence references.
8. Present findings and coverage to authorised reviewers.
9. Record human action and rationale.
10. Preserve run/model/source versions and audit history.

## 6. Security architecture requirements

Before real institutional use, define and implement authentication, role-based access, organisation isolation, secure upload validation, malware/resource controls, encryption in transit and at rest, secrets management, retention/deletion, audit protection, backups, incident response and security testing.

## 7. Integration policy

RIGMS and national repository integrations are authorization-dependent. Require written authorization, data-sharing agreement, API documentation, security assessment, data mapping, test environment and integration acceptance before activation.

## 8. Reliability and operations

Use persistent workflow storage, durable background jobs, idempotent processing, retries with limits, dead-letter handling, health checks, structured logs, metrics, alerts, backups and restore tests. Record model and prompt versions for AI-assisted outputs.

## 9. Architecture decision records

Store material decisions under `docs/architecture/decisions/` using `ADR-NNN-title.md`. Include status, context, options, decision, consequences, owner and date.

## 10. Production gate

The current workflow guide says workflow records are in memory, identity is a demo header, RIGMS is a stub, external scholarly connectors are not configured and scanned-PDF OCR is not implemented. These are explicit gaps to address or scope out before production claims.
