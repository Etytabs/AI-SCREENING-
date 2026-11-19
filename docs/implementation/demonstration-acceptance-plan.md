# Controlled Synthetic Demonstration Acceptance Plan

**Data boundary:** synthetic, de-identified or locally generated records only. No real proposals or public-source claims.

## Scenario acceptance matrix

| # | Scenario | Expected behavior | Evidence | Reviewer action | Failure condition |
|---|---|---|---|---|---|
| 1 | Same purpose, substantially different wording | Purpose-overlap candidate surfaced as unresolved or possible purpose match; no duplication/plagiarism misconduct conclusion | Both structured profiles, dimension evidence, passage evidence, method/version and coverage | Compare problem/purpose/objectives/beneficiaries/intervention; confirm or dismiss disposition | Only lexical similarity used; category defaults to duplicate; source coverage missing |
| 2 | Similar topic, different objectives/interventions | Topic similarity may exist, purpose overlap low and no duplicate conclusion | Dimension-by-dimension profile, candidate evidence and negative/explanation | Mark differentiated/same topic or request clarification | System classifies as duplicate or no overlap |
| 3 | Legitimate replication | Classification can be replication, with explicit similarity and no misconduct claim | Original/replication scope, shared and different objectives, provenance | Choose replication disposition and rationale | Misclassified as exact duplicate or funded/fraud conclusion |
| 4 | Differentiated follow-on | Follow-on/differentiated classification, preserving predecessor and changes | Prior project, changed population/intervention/location/method/output | Confirm differentiated, or escalate if purpose/substance unclear | No change/evolution evidence shown |
| 5 | Copied passage with traceable source | Text match shown with applicant/source passage and snapshot identity; status review-required | Page/offset or current locator, source URL/title/version/hash where available, method | Review and confirm/dismiss/clarify; no automatic verdict | Match lacks source or applicant passage; unavailable source shown as no-match |
| 6 | Correct quote and citation | Quoted/cited passage disposition, not uncited similarity misconduct | Citation text, quoted span, source identity and policy rule | Accept citation context or escalate ambiguous citation | Equal to uncited copied text; missing quote/citation metadata |
| 7 | Generic methodology/ethics boilerplate | Negative/boilerplate disposition, no plagiarism finding or low priority | Shared passage and boilerplate classification | Dismiss or request context only if proposal-specific evidence is also present | Boilerplate triggers misconduct or ranking penalty |
| 8 | Funding overlap with different wording | Separate funding-overlap candidate using structured award/funding evidence | Award ID/committer, period, budget line, deliverable/objective and match rationale | Review overlap and confidence; no award decision | Text similarity label used instead of funding evidence; no structured fields |
| 9 | Unavailable comparison source | Explicit blocked/unavailable/not-searched state; not no-match | Source ID/state/message/timestamp/attempted scope | Record limitation and seek authorized source or clarification | No-match, zero, or complete coverage implied |
| 10 | Applicant submission through human decision | Synthetic applicant submits immutable snapshot and reviewer records adjustment/decision | Identity, ownership, submission receipt, document versions, rubric/run, reviewer action, audit | Accept/challenge/adjust/request clarification/escalate; final action remains human | Snapshot mutable; role can access unassigned resource; AI overwrites human/original |

## Execution procedure

1. Reset synthetic seed and isolate the SQLite comparison library.
2. Record environment, API commit, model/provider status and feature flags.
3. Run the approved synthetic call/RFP/application fixtures.
4. Capture route results, evidence, source coverage and human actions.
5. Export report and verify data-origin/synthetic notice.
6. Repeat after API restart to distinguish persistent versus in-memory behavior only for the future P0 acceptance environment.

## Failure and stop conditions

Stop the demo and mark the run failed if:
- Real data or credentials are used accidentally.
- A score becomes a funding/award conclusion.
- Missing evidence becomes zero or pass.
- A source failure becomes no-match.
- An unassigned or forged actor accesses data.
- An AI result overwrites a human adjustment.
- Source or model versions cannot be reproduced.
- A private source snapshot or applicant text is leaked into logs/errors.

## Required evidence per run

- Commit SHA and API/frontend build ID.
- Synthetic-data declaration.
- Auth/role/assignment configuration.
- RFP/rubric or call requirements version.
- Application/document hashes and versions.
- Model/provider/calculator/pipeline versions.
- Source coverage and unavailable states.
- Human action, rationale, actor and timestamp.
- Report/export contents and limitations.
