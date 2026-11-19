# Team Workstream and Responsibility Matrix

The matrix uses role assignments only; named individuals are not inferred.

| Workstream | Accountable | Responsible | Consulted | Required output |
|---|---|---|---|---|
| Governance and decisions | Team Leader / Project Coordinator | Platform Developer | Business Manager, Full-Stack, AI/ML | FPDR-002 decision, ADR revisions/new ADRs, decision log |
| Product intake and applicant UX | Business & Project Manager | Full-Stack Developer | Platform, AI/ML | Applicant journey, submission acceptance, user feedback |
| Authentication and account lifecycle | Full-Stack Developer | Full-Stack Developer | Platform Developer, Team Leader | Auth implementation and acceptance tests |
| Authorization and assignment | Full-Stack Developer | Full-Stack Developer | Platform Developer | Permission matrix, policy, negative tests |
| Persistence and migrations | Full-Stack Developer | Full-Stack Developer | Platform Developer | Adapter, migration plan, restart/restore tests |
| Storage and data lifecycle | Full-Stack Developer | Full-Stack Developer | Platform Developer, Business Manager | Private storage, retention/deletion, upload tests |
| Durable jobs and operations | Full-Stack Developer | Full-Stack Developer | Platform Developer | Queue/worker, retry, progress and recovery |
| Architecture and standards | Software Developer / AI Platform Developer | Platform Developer | Full-Stack, AI/ML | ADRs, contracts, threat model, technical acceptance |
| AI/ML methods and datasets | AI/ML Engineer | AI/ML Engineer | Platform, Full-Stack | Data cards, evaluation protocol, baselines and error analysis |
| Purpose overlap | AI/ML Engineer | AI/ML + Full-Stack | Business Manager, Platform | Profile schema, candidate service, expert-labelled evaluation |
| Plagiarism/source provenance | AI/ML Engineer | AI/ML + Full-Stack | Platform, institutional data owner | Source adapters, snapshot/evidence model, coverage and precision |
| Application assessment | Platform Developer | Full-Stack + AI/ML | Business Manager, Team Leader | Rubric/eligibility/score/recommendation/ranking/report |
| Funding-to-impact operations | Full-Stack Developer | Full-Stack Developer | Business Manager, Platform, institutional finance | Award/ledger/milestone/closeout workflows |
| STI/repository expansion | AI/ML Engineer | AI/ML + Full-Stack | Business Manager, institutional data owner | Authorized source/repository integration and analytics |
| Security/privacy review | Platform Developer | Platform + Full-Stack | AI/ML, Team Leader | Threat model, privacy/data review, release gate |
| Pilot and controlled demo | Team Leader / Project Coordinator | Business Manager | All roles | Synthetic acceptance, institutional authorization and go/no-go |

## Required handoffs

- Governance → Engineering: approved scope, authority, data terms and blocked decisions.
- Business → Product/Engineering: applicant/reviewer discovery, workflow, acceptance examples.
- AI/ML → Full-Stack: versioned method contract, latency/errors/coverage/evaluation evidence.
- Full-Stack → AI/ML: integration telemetry and failure/reviewer feedback.
- Platform → all: architecture, security, contracts and release criteria.
- Institutional data owner → AI/ML/Platform: authorized source, provenance and permitted use.
