# Phase 3 evidence quality and retrieval reliability audit

- **Audited base:** `main` at `4d6c0851a658434404d10153f82d2f901209697e`
- **Working branch:** `phase-3-evidence-quality`
- **Scope:** Repository source, synthetic datasets, mocked OpenAlex responses and local automated tests. No institutional or confidential data was used.

## Initial technical assessment

### Existing capabilities

- `ScreeningOrchestrator` builds comparison records from readable applications, configured providers, the local duplication archive and OpenAlex, then runs eligibility, completeness, duplication, text similarity and novelty as separate stages.
- `literature.py` creates up to six queries from an application title, extracted document title, keywords, frequent content terms and substantial numbered sections. OpenAlex requests are limited to 30 works per query.
- The OpenAlex connector maps work IDs, DOI, title, abstract, authors, publication date, journal and available links. Its request has a 20-second timeout; the connector relies on provider-side search order and does not paginate.
- Literature records are deduplicated across queries by record ID and only records with an identifier and at least 25 abstract words are compared. Before this phase, discarded records were not counted in the coverage state.
- Text similarity uses 8-word shingles and content-phrase overlap. It reports proposal-side and source-side coverage separately. Existing review thresholds are `MIN_PASSAGE_WORDS=12`, `MIN_COVERAGE=0.05`, `MIN_PHRASE_COVERAGE=0.20`, and published-source coverage `MIN_SOURCE_COVERAGE=0.15`; none were changed. Similarity bands are text-overlap descriptions, not probability estimates.
- Findings retain application/finding IDs, method, source records and matched passages; evidence items retain a source identifier and document locator where available. Reviewer decisions are separately stored and included in reports.
- Retrieval ranking is deterministic token-set Jaccard when no model is configured. Optional hybrid retrieval combines lexical and embedding scores (0.35/0.65 by default); an optional cross-encoder reranks a shortlist. Model-backed ranking is disabled by default.
- Source `RunState` values distinguish complete, partial, blocked and failed operations. The reviewer workspace already warns that similarity is not proof of plagiarism and that unavailable sources are not evidence of originality.

### Verified weaknesses and error patterns

- The page-furniture expression contained a literal backspace where a regex word boundary was intended. `Page 1` could therefore survive cleanup and enter a title/query.
- OpenAlex records without usable abstracts were discarded, and the source could still be marked complete with zero compared works. In addition, the finding UI inferred that literature was searched from the presence of returned works, conflating a completed empty/incomplete search with “not searched.”
- Cross-query deduplication used only the OpenAlex record ID; duplicate records with different IDs but the same DOI could be compared twice.
- The reviewer UI showed a per-source overlap score without defining that it is the greater of verbatim application coverage and proposal-side shared phrase coverage. The per-match content-phrase coverage was not represented separately in the API model.
- The existing lexical and adversarial retrieval corpora contain four and ten queries respectively, five candidates per query, and synthetic labels only. They evaluate ranking metrics but not duplicate-detection precision/recall, source-result filtering, or recurring false-positive/false-negative patterns.
- The new 10-pair similarity diagnostic identifies false positives from generic research terminology, shared bibliographic references, standard methodology boilerplate and repeated institutional templates. One paraphrased case is missed. These are synthetic diagnostic examples, not estimates of real-world error rates.

Potential ranking changes were tested against the existing datasets before being rejected: weighted lexical overlap and BM25 lowered adversarial MRR from 0.562 to 0.543 and nDCG@5 from 0.667 to 0.651, while leaving Recall@5 and Precision@5 unchanged. No ranking formula or match threshold was changed on the basis of these small datasets.

## Changes in this phase

- Corrected page-number furniture cleanup and added title/query regression coverage.
- Counted OpenAlex records returned, compared and unusable; surfaced retrieval timestamp and explicit source state. An unusable-record result is now partial rather than a clean zero-comparison result.
- Deduplicated text-comparable OpenAlex records by normalized DOI where available, falling back to record ID.
- Sanitized OpenAlex error reporting so failures retain HTTP status/type without echoing proposal query text or request URLs that could contain credentials.
- Added the per-match proposal phrase-coverage measure to the finding model and reviewer breakdown. The UI distinguishes completed, partial, failed and blocked source states and explains the score as textual overlap, not plagiarism probability.
- Added `data/evaluation/similarity_benchmark.json` and `python -m scripts.evaluate_similarity` to report synthetic duplicate-signal precision/recall, confusion counts, error case IDs and both sides of phrase coverage.
- Preserved all Phase 2 retrieval datasets and reference results. No threshold, ranking formula, API route or RIGMS behavior changed.
- Added safe API validation and generic-error responses that omit submitted values and exception messages. Publication-source failures, extraction errors, ZIP errors and failed screening coverage now use bounded messages; exception logging records operation, exception type and safe identifiers rather than traceback messages or document content.

## Reproducible evaluation

Commands:

```sh
python -m scripts.evaluate_retrieval --dataset data/evaluation/retrieval_benchmark.json --methods lexical --output /tmp/phase3-retrieval.json
python -m scripts.evaluate_retrieval --dataset data/evaluation/retrieval_benchmark_adversarial.json --methods lexical --output /tmp/phase3-adversarial.json
python -m scripts.evaluate_similarity --output /tmp/phase3-similarity.json
```

The original retrieval reference remains unchanged. Since ranking was not changed, the measured after-results equal the recorded Phase 2 baseline:

| Dataset | Queries | Recall@5 | Precision@5 | MRR | nDCG@5 |
|---|---:|---:|---:|---:|---:|
| Synthetic baseline (`v0.1`) | 4 | 1.00 | 0.20 | 1.00 | 1.00 |
| Synthetic adversarial (`v0.1`) | 10 | 1.00 | 0.24 | 0.562 | 0.667 |

Similarity diagnostic: 10 pairs (one case in each category), 3 true positives, 4 false positives, 1 false negative and 2 true negatives; precision 0.429 and recall 0.750. False-positive IDs are `S004`–`S007`; the false-negative ID is `S003`. Mean application-side phrase coverage is 0.493 and mean source-side phrase coverage is 0.520. These labels mean “surface for human comparison,” not plagiarism, eligibility or scientific judgements. The dataset is intentionally small and hand-authored; it must not be used to select production thresholds or claim general performance.

No evidence-backed improvement to candidate ranking was established. The confirmed query-cleanup and source-state fixes improve query hygiene and result traceability, but this phase does not claim better retrieval ranking performance than Phase 2.

## OpenAlex validation report

- **Live connectivity:** Not validated. A controlled request to `api.openalex.org` failed because the environment could not resolve the host. No live literature-search success is claimed.
- **Mocked integration:** The test suite checks request parameters and configured credentials, abstract reconstruction, metadata/identifier/link mapping, absent abstracts, duplicate records, source-side coverage, query errors, and blocked/failed/partial states.
- **Recent error-redaction regression:** A synthetic HTTP 429 error containing a private query and API key is verified absent from both source status and captured logs. API validation, unhandled API errors, publication-source errors and document extraction failures are also tested with synthetic secret markers.
- **Request limits:** `per-page` is clamped to 1–50; the screening provider requests 30 results for each of at most six generated queries. The connector uses one page and does not follow OpenAlex cursors. It does not retry rate-limit responses; timeout and HTTP errors propagate to the provider, which records failed or partial coverage.
- **Result handling:** Query results are deduplicated by DOI or record ID at the screening source. Records without an identifier or at least 25 abstract words are counted as unusable and make coverage partial. Source IDs, DOI and source links are retained when returned by the API.
- **RIGMS:** Still unavailable pending an authorized institutional specification and integration agreement; no successful connection is simulated.

## Phase 3 completion follow-up diagnosis

This follow-up starts from the same `main`/`origin/main` commit listed above; no newer
main commit is present in the checkout.

### Why the retrieval metrics did not improve

- The deterministic no-embedding ranker is a token-set Jaccard score. It ignores term
  frequency and word order; paraphrases with different vocabulary consequently score
  below lexical distractors. Equal-score candidates retain input order, so benchmark
  order affects MRR and nDCG.
- On the adversarial corpus, relevant candidate ranks across A001–A010 are 3, 1, 4, 4,
  (1 and 3), 4, 5, 3, 1 and 1. These are ordering failures, not candidate omissions:
  every labeled relevant item is in the candidate pool.
- Each labeled retrieval case has exactly five candidates and the benchmark evaluates
  `k=5`. It returns the entire pool; Recall@5 is necessarily 1.00 and Precision@5 is
  determined solely by label composition, independent of ranking. Those metrics do not
  demonstrate that the ranker filtered irrelevant candidates.
- Weighted lexical overlap and BM25 were prototyped on the unchanged cases. Both reduced
  adversarial MRR/nDCG@5 versus token Jaccard; neither improved Precision@5 or Recall@5.
  Model-backed embedding strategies were not available in the dependency-free benchmark
  run. Changing production scoring based on this evidence would be unjustified.
- The Phase 2 corpus is a synthetic project-candidate ranking benchmark, not a labeled
  OpenAlex relevance set. It cannot establish candidate recall, OpenAlex query quality,
  literature retrieval ranking, plagiarism detection quality or reviewer judgement.
  In the actual literature path, OpenAlex returns provider-ranked results per query;
  the workflow deduplicates results and compares abstracts. It does not use the generic
  benchmark's ranker to reorder those works before text comparison.
- Proposal-section query generation uses title/keywords/frequent terms and numbered
  sections of at least 60 words. It can miss unnumbered sections, terminology variants
  and passages outside the three longest sections. OpenAlex supplies at most one page
  of up to 30 works per query; there is no cursor pagination or query-specific relevance
  reranking. These are possible candidate-quality limitations, but no authorized
  labeled live corpus is available to measure their contribution.

**Diagnosis:** The observed benchmark weakness is primarily a metric/candidate-pool
design limitation plus lexical ranking's paraphrase and tie behavior. It does not prove
that OpenAlex retrieval is poor. Do not select or tune a ranker until an authorized
benchmark has more than five candidates per query, graded query-to-source relevance
labels, representative proposal sections, and an evaluation that separates candidate
recall from ranking quality. The existing baseline and adversarial datasets remain
unchanged.

### OpenAlex network blocker

A controlled request on this runner failed before establishing a connection:
`socket.getaddrinfo("api.openalex.org", 443)` returned `gaierror: [Errno -5] No address
associated with hostname`, and curl returned HTTP status `000` with a DNS resolution
failure. `github.com` did resolve in the same process, so this is a hostname-specific
network/DNS restriction in the current environment, not evidence of an OpenAlex API,
authentication, rate-limit, timeout or response-parsing failure. No live request or
response was obtained; integration evidence remains mocked only.

## Validation and limitations

Before changes, the full backend suite passed (166 tests), the frontend suite passed (70 tests), frontend lint and TypeScript validation passed, and the production frontend build completed. The baseline build emitted optional-`sharp`, Autoprefixer and webpack-cache warnings.

After the Phase 3 evidence/provenance work and the completion follow-up:

- Backend: **177 passed**, with one existing Starlette/httpx deprecation warning.
- Frontend: **72 passed** across six test files.
- Frontend ESLint and `tsc --noEmit`: **passed**.
- Production frontend build: **passed**.
- Phase 2 API workflow, source-state, provenance, reviewer/report and redaction regression tests: **passed** as part of the backend suite.
- Retrieval and similarity benchmark runners: **completed** with the results above.
- Full backend Ruff check: **one pre-existing import-order finding** remains in `services/plagiarism/attribution.py`; all changed backend files pass Ruff. No unrelated attribution cleanup was included.
- Synthetic-secret checks cover API validation, unhandled server errors and their logs, unknown roles, publication-source errors and logs, invalid ZIP filenames, document extraction metadata and responses, and background-job logs. Operational logs retain the exception type, operation and safe route/run identifiers, without exception text or stack traces.
- Live OpenAlex validation was retried on 2026-11-13: DNS lookup failed with `gaierror: [Errno -5] No address associated with hostname`; curl reported `Could not resolve host` and HTTP `000` with zero DNS/connect time. In the same check `github.com` resolved. This is the runner's DNS/network restriction; no live request reached OpenAlex.

The full after-results continue to show no ranking-score gain over Phase 2, and the synthetic similarity benchmark exposes material false-positive and false-negative patterns. Therefore the strict definition of done—demonstrated improvement in ranking relevance—is **not met**. This audit records the verified fixes and limitations rather than claiming Phase 3 is complete.

Remaining limitations: no authorized representative corpus; no live OpenAlex validation; OpenAlex pagination and retry/backoff remain absent; ranking has no measured gain over Phase 2; duplicate-signal errors remain visible in the synthetic diagnostic and thresholds were intentionally left unchanged; OCR, institutional integrations and production-readiness validation remain out of scope.

AI findings are screening signals only. Similarity does not establish plagiarism, shared subject matter does not establish duplication, and a missing or unavailable source is not proof of absence. Consequential findings require human review against the cited source text.
