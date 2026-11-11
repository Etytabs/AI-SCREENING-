# Role-Based Workstreams and Responsibility Matrix

**Authority:** The agreed team agreement takes precedence if any conflict exists.

## 1. Team Leader / Project Coordinator

**Accountability:** delivery coordination, stakeholder alignment, programme milestones and team decisions.

**Owns:** integrated roadmap and milestones; stakeholder coordination and requirements capture; decision ownership and escalation; weekly reviews, demos and milestone reviews; ensuring workstreams have owners, dependencies and acceptance criteria; coordinating pilot authorization and stakeholder sign-off (not self-authorizing data access).

**Deliverables:** roadmap/milestone plan; stakeholder map and communication log; decision and escalation register; weekly progress report; milestone acceptance records; pilot go/no-go record.

**Done when:** every milestone has an owner, dependencies and exit criteria; risks/blocked work have owners and next actions; stakeholder decisions are recorded.

## 2. Business & Project Manager

**Accountability:** customer discovery, workflow validation, market/business evidence, partnerships and commercial pathway.

**Owns:** interviews with grant administrators/reviewers/programme managers; current-state workflow and pain-point mapping; MVP problem validation; personas, journeys, user stories and prioritization evidence; alternatives/competitor and procurement research; pilot onboarding/training/feedback with the Team Leader; partnership pipeline with evidence and stage clarity.

**Deliverables:** interview plan and anonymized findings; current/future workflow maps; prioritized product requirements; market/alternatives assessment; business model assumptions; pilot user/training/feedback plan; partnership tracker.

**Done when:** priority requirements link to user evidence or labelled assumptions; each workflow has user, trigger, outcome and acceptance criteria; commercial claims are dated and do not imply unconfirmed partnerships.

## 3. AI/ML Engineer

**Accountability:** AI/ML research, data preparation, method implementation, evaluation and responsible-AI evidence.

**Owns:** data provenance, labeling and splits; document intelligence methods assigned to AI/ML; lexical/semantic retrieval, embeddings, similarity and reranking; duplicate-candidate signals; baselines, evaluation sets, error analysis and threshold calibration; model/tokenizer/embedding/prompt/dependency versions; model cards and limitations; AI service contracts with Platform and Full-Stack.

**Deliverables:** dataset cards and pipelines; reproducible experiments; retrieval/similarity interfaces; evaluation reports; threshold recommendations; model/method cards; error taxonomy and monitoring guidance.

**Done when:** permission, provenance, split and leakage controls are documented; metrics include sample size, class balance, methodology and error analysis; evaluation is reproducible; outputs expose method/version and evidence; unavailable/insufficient evidence is explicit. Similarity is not proof of plagiarism.

## 4. Full-Stack Developer

**Accountability:** web application, backend/API, database, persistence, integrations and deployment implementation.

**Owns:** responsive frontend; backend endpoints and workflow orchestration; database schema/migrations; authentication and server-side authorization implementation with Platform oversight; secure upload/storage; AI/ML service integration; review, audit and reporting workflows; automated tests and deployment pipelines.

**Deliverables:** frontend/API code; schema/migrations/fixtures; auth/RBAC implementation and tests; ingestion and job integration; API documentation; CI/CD and runbooks.

**Done when:** critical workflow state is persistent; protected APIs enforce authorization; uploads have validation and resource limits; migrations are repeatable; critical journeys have automated tests; deployment is reproducible without committed secrets.

## 5. Software Developer / AI Platform Developer

**Accountability:** overall platform architecture, requirements alignment, engineering standards, integration oversight, technical quality and technical documentation.

**Owns:** system context and architecture boundaries; translation of product requirements into technical requirements/contracts; coding/branch/review/testing/versioning/documentation standards; architectural, security and non-functional reviews; technical dependency coordination; ADRs and technical risk reviews; observability/reliability/maintainability requirements; documentation accuracy; technical acceptance before release.

**Deliverables:** system architecture and diagrams; ADRs; API/event/data contracts; engineering standards and review checklist; threat model and technical risk register; integration test strategy; release sign-off and documentation index.

**Done when:** material decisions have ADRs; interfaces define schemas/errors/versioning; critical cross-component paths have integration tests; security/reliability risks have owners; documentation matches implementation.

## Responsibility matrix

R = executes; A = accountable; C = consulted; I = informed.

| Activity | Team Leader | Business Manager | AI/ML Engineer | Full-Stack Developer | Platform Developer |
|---|---|---|---|---|---|
| Stakeholders and milestones | A/R | C | I | I | C |
| User discovery and market validation | C | A/R | C | C | C |
| Product requirements/prioritization | A | R | C | C | C |
| Architecture and technical standards | I | C | C | R | A |
| AI methods and evaluation | I | C | A/R | C | C |
| Frontend/backend/database | I | C | C | A/R | C |
| API contracts/integration oversight | I | C | R | R | A |
| Security architecture/quality gates | I | C | C | R | A |
| Pilot readiness | A | R | C | R | R |
| Business model/partnership evidence | C | A/R | I | I | I |

## Required handoffs

- Business Manager → Product/Engineering: validated workflow, stories, evidence, priorities and acceptance examples.
- Team Leader → all workstreams: approved milestones, stakeholder constraints and decisions.
- Platform → technical team: architecture, contracts, standards, dependencies and acceptance criteria.
- AI/ML → Full-Stack: stable service contract, schemas, latency expectations, errors and evaluation evidence.
- Full-Stack → AI/ML: integration telemetry, failure cases and reviewer feedback.
- Technical team → leadership/business: demo, limitations, risks, pilot needs and release evidence.

A handoff is complete only when the receiving owner acknowledges the deliverable and criteria.
