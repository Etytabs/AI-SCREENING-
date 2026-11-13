# Phase 2 workflow audit

**Audited base:** `main` at `926a1d279d4fa1025c01fec2a44e0a85c05a97bf` (merged PR #17).  
**Scope:** Repository implementation and local automated tests. No institutional data,
production environment, authenticated deployment or OpenAlex live search was used.

## Workflow status

| Workflow capability | Existing implementation | Verified status | Gap / limitation | Priority |
|---|---|---|---|---|
| Product identity and navigation | Approved logo, Fredoka/Nunito fonts, brand tokens, dashboard sidebar and workflow routes | Implemented and verified by source inspection, frontend lint/type-check/build, component tests and Playwright at 1440, 768 and 390 CSS-pixel widths | Responsive checks are manual; no browser suite is established in CI | P1 |
| Grant call creation and RFP upload | FastAPI call/RFP endpoints, call form, PDF/DOCX/TXT parsing | Implemented and verified by API integration test | Workflow entities are memory-only; identity headers are a demo mechanism | P0 for production, outside this sprint's approved architecture scope |
| Requirement extraction and confirmation | Deterministic sentence extraction with source locations; administrator verify/reject/edit; screening requires confirmation | Implemented and verified by API and workflow tests | Rule-based extraction can miss or misclassify unusual wording; no calibrated extraction confidence | P1 |
| Application upload and association | Multiple files and ZIP grouping, format checks, document extraction, pending-upload association, page/line text endpoint | Implemented and verified by API integration and upload edge-case tests | Scanned-PDF OCR is not implemented; documents are not durably stored with the workflow repository | P1 |
| Eligibility and completeness | Configured deterministic checks, evidence-backed outcomes, uncertain/missing information routed to review | Implemented and verified by workflow tests | Rules have synthetic-only evaluation; no representative institutional validation | P1 |
| Duplicate/overlap screening | Same-call, historical and optional local archive comparisons; paired passages and source metadata | Implemented and verified by workflow/duplication tests | Semantic retrieval depends on optional model extras; external historical systems are not connected | P1 |
| Published-literature similarity | OpenAlex query generation, deduplication by work ID, abstract comparison, partial/failure states and source metadata | Implemented and verified with mocked retrieval tests; asymmetric source coverage now has a regression test | No live retrieval was run; OpenAlex is unsearched unless enabled; coverage is limited to returned works with abstracts | P1 |
| Evidence inspection | Finding evidence API and UI drawer; citation validation against extracted document text; source and coverage information | Implemented and verified by evidence integrity and API tests | Numeric confidence values are heuristic and not statistically calibrated; they are not shown to reviewers | P1 |
| Human review | Reviewer note/decision API, actor and timestamp, history and audit record; AI findings retained separately | Implemented and verified by API test | Demo identity is not authentication; no escalation workflow beyond existing recorded actions | P0 for production identity, separate approved workstream |
| Reports | Report aggregates real call/application/findings/decisions and includes disclaimer and synthetic notice | Implemented; strengthened API test verifies decision propagation | Not a durable export/archive; reports reflect current in-memory state | P1 |
| Workflow persistence and job recovery | Repository interface, in-memory workflow repository and in-process job runner | Partially implemented; local synchronous integration path verified | API restart loses workflow records and thread-pool jobs; durable storage/queue are explicit architecture dependencies | P0 blocked for production, excluded by scope |
| Institutional source integrations | RIGMS and optional scholarly-source registry report access state | Explicitly unavailable/not configured; no false zero-result claim | Authorized RIGMS specification and scholarly connectors are absent | Blocked by external/architectural dependency |

## Prioritized sprint changes

1. Make the frontend test environment provide the same-origin storage API expected by
   workspace call recovery.
2. Recognize the exact generated synthetic application bundle so its uploaded
   applications and resulting report retain the synthetic-data label.
3. Assert that an actual reviewer decision survives into both report summary and the
   corresponding reported finding.
4. Document the complete synthetic run, observable expected results, reset boundary and
   operational limitations.

No screening thresholds, source rankings, authentication, persistence provider or
infrastructure were changed.

Reviewer-facing numeric confidence was removed because current values come from
hand-set heuristics rather than a validated calibration set. Finding states, explanations,
methods and traceable evidence remain visible and unchanged.

Published-source phrase coverage now reports the source-side overlap rather than reusing
the proposal-side overlap. An asymmetric synthetic regression case verifies the percentage
against the title and abstract used by the comparison pipeline.

## Validation record

At the start of this work, all 163 backend tests passed. Frontend lint, TypeScript
validation and production build passed. The frontend test suite initially had one
environment failure because Node 26 did not provide the jsdom `localStorage` object;
the test environment now provides deterministic in-memory storage and the suite passes.

Backend `ruff check .` currently reports three existing import-only findings in
`services/grant_workflow/screening/text_similarity.py` and
`services/plagiarism/attribution.py`. They are unrelated to the workflow changes and
are not included in this focused patch.

The full HTTP workflow test uses only generated synthetic files and an in-process API:
create call, upload/verify RFP requirements, batch-upload five applications, screen,
inspect source evidence, record a reviewer action and read the report. It does not
establish browser-level responsive behavior, live-source reliability, production
authorization, durable persistence or scientific validation.

Manual Playwright validation also opened the seeded synthetic call and all five results,
inspected an eligibility finding against the RFP and proposal passages, recorded a
reviewer decision through the frontend/API, and verified that the report displayed the
decision and synthetic-data notice. The dashboard and evidence workspace had no
horizontal overflow at 1440×900, 768×1024 or 390×844; light/dark theme toggling was
verified, and the theme hydration warning was corrected.

The synthetic retrieval diagnostics measured Recall@5 1.00, Precision@5 0.20, MRR 1.00
and nDCG@5 1.00 on the four-case baseline; the 10-case adversarial set measured Recall@5
1.00, Precision@5 0.24, MRR 0.562 and nDCG@5 0.667. These small labeled synthetic sets
are diagnostic only, not scientific validation. No live OpenAlex retrieval or embedding-
backed benchmark was run.

Spot contrast checks for body text, active/inactive sidebar links, synthetic badges and
the evidence-drawer close action exceeded 12:1 in both themes. This is not a full WCAG
audit; screen-reader testing and complete keyboard-flow coverage remain outstanding.
