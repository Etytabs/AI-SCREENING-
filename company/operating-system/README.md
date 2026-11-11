# ShakaHive Team Operating System

**Status:** Draft for team approval  
**Applies to:** Technical and non-technical contributors.

## 1. One shared workspace

Use the repository as the shared source of truth for project work. GitHub is the tracking system, not merely a place to store code.

| Need | System of record |
|---|---|
| Tasks, bugs, research actions | GitHub Issues |
| Roadmap, sprint and cross-team progress | GitHub Projects |
| Code and document review | Pull Requests |
| Company policies and plans | `company/` |
| Technical architecture and specifications | `docs/` |
| AI experiments and evaluation | `ml/`, `data/evaluation/`, and linked reports |
| Meeting notes and decisions | `resources/meetings/`, `resources/decisions/` |
| Brand source files | `assets/brand/` |
| Release history | GitHub Releases and release notes |

## 2. Roles from the team agreement

- Team Leader / Project Coordinator: coordinates delivery, stakeholder requirements, programme reporting, milestones and team decisions.
- Business & Project Manager: customer discovery, market validation, partnerships, business model and commercial pathway.
- AI/ML Engineer: model research, data preparation, model implementation, evaluation and responsible AI documentation.
- Full-Stack Developer: frontend, backend, database implementation, APIs, application security, tests and deployment.
- Software Developer / AI Platform Developer: overall platform architecture, requirements alignment, integration, engineering standards, technical coordination, quality and technical documentation.

The agreement's responsibility matrix remains authoritative for role-level accountability. Contributors should collaborate across boundaries and record handoffs.

## 3. Work lifecycle

1. Create an Issue before starting substantive work.
2. Describe the problem, expected outcome, owner, priority, due date or milestone, dependencies and acceptance criteria.
3. Add the Issue to the relevant GitHub Project.
4. Link relevant design, specification, research or decision documents.
5. Update status as work progresses.
6. Submit implementation or document changes through a Pull Request when review is appropriate.
7. Obtain review from the accountable role or designated approver.
8. Close the Issue only when acceptance criteria are met and evidence of completion is linked.

Suggested statuses: Backlog → Ready → In Progress → In Review → Blocked → Done. Use Blocked with a reason and next action.

## 4. Contribution types

Non-technical contributors can create and update Issues, upload meeting notes, write market research, document stakeholder interviews, maintain business assumptions, add reports and update project milestones. They do not need to submit code.

Technical contributors can add code, tests, architecture decisions, API specifications, model cards, experiment reports, deployment notes and security findings.

All contributions should be linked to a relevant Issue or milestone where practical.

## 5. Weekly cadence

- Weekly full-team meeting: progress, decisions, blockers and upcoming commitments.
- Technical coordination at least twice weekly when integration work requires it.
- Weekly product demonstration/review.
- Biweekly customer and stakeholder validation update.
- Monthly company review: roadmap, KPIs, risks, budget and strategic assumptions.
- Milestone release review: acceptance, documentation, known limitations and handover.

Record decisions and actions, not verbatim meeting transcripts.

## 6. Definition of Ready

A task is ready when its problem, intended outcome, owner, acceptance criteria, dependencies and priority are understood. Research tasks should state the question and expected evidence.

## 7. Definition of Done

A task is done when:
- Acceptance criteria are met.
- Relevant tests or validation are complete.
- Documentation and evidence are updated.
- Known limitations are recorded.
- Changes are reviewed where required.
- The Issue and Project status are updated.

For AI/ML work, include dataset provenance, evaluation method, metrics, limitations and model/version details. For business work, include sources, date, assumptions and next action.

## 8. Decision records

Use Architecture Decision Records for material technical choices and decision notes for business/product choices. Each record should include context, options considered, decision, rationale, consequences, owner, date and status.

## 9. Security and confidentiality

Never commit API keys, passwords, production credentials, confidential proposals, personal data or unauthorised institutional records. Use synthetic or approved de-identified examples. Restrict access to sensitive working materials using an approved private location and access policy.

## 10. Monthly scorecard

Track:
- Milestones completed versus planned.
- Work items completed and ageing blocked items.
- Product workflow completion and pilot feedback.
- Document extraction and screening reliability.
- Evidence coverage and reviewer outcomes.
- Retrieval quality on appropriately labelled evaluation data.
- Defects, incidents and deployment reliability.
- Customer discovery, validated needs and partnership progress.

Metrics must be defined consistently; do not report synthetic benchmark performance as production performance.
