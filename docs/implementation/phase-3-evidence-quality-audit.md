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

## Expanded retrieval evaluation report — 2026-11-13

### Baseline assessment

The merged PR #19 implementation added query cleanup, OpenAlex source-state accounting,
DOI/record-ID deduplication, and synthetic evaluation scripts. The production literature
path generates up to six proposal-derived queries, requests up to 30 OpenAlex works per
query, removes duplicate and unusable-abstract records, and retains provider result
ordering. It does not use `ml.semantic_matching.hybrid.rank_candidates` to reorder
published literature before text comparison. That generic ranker is a deterministic
token-set Jaccard implementation with stable sorting; equal scores inherit input order.
The historical Phase 2 retrieval fixtures contain 4 and 10 queries with five candidates
each, so K=5 evaluates the entire candidate pool and does not measure candidate filtering.
Their binary labels also cannot distinguish weak from strong relevance. Those historical
fixtures and reference outputs remain unchanged.

### Dataset and method

The new versioned fixture is `data/evaluation/retrieval_evaluation_v1.json`
(`synthetic-research-retrieval-v1.0`); its deterministic output is
`data/evaluation/retrieval_evaluation_v1_results.json`. It has 27 synthetic publication
records, 25 unique works after DOI/record-ID deduplication, 6 domain groups, 12 query
variants, and 25 unique candidates per query. It covers agriculture, maternal health,
water quality, renewable energy, education, and biodiversity. The 300 query-work labels
are 264 grade 0, 12 grade 1, 12 grade 2, and 12 grade 3. Every grade has a rationale:
case-level rationales explicitly label the default cross-domain negatives, with
candidate-specific rationales for matches and difficult negatives.

The fixture uses synthetic texts and identifiers only. It deliberately includes
paraphrases, lexical distractors, near-topic negatives, one same-DOI duplicate pair,
incomplete metadata and missing abstracts. The evaluator deduplicates with the same
normalization helper as the literature source and uses the existing ranker on the
concatenated title and abstract. No ranking formula, query-generation rule, threshold, or
external-model dependency changed.

The evaluator supplies all 25 unique works directly to the ranker; it does not execute
an independent candidate-generation or external literature-retrieval stage.
`ranked_pool_recall_metrics` reports Recall@5/10/20: relevant candidates appearing in
the top K of that supplied pool. Independent candidate generation and live-source
retrieval recall have not been evaluated. The `ranked_pool_fraction_at_20` result
(20/25 = 0.8000) is only the selected fraction of the fixed input pool, not a
retrieval-quality metric. Relevant-candidate retrieval rate@20 is omitted because it is
mathematically identical to Recall@20 in this experiment.

Ranking metrics are Precision@5 and MRR over grades 1–3, plus graded nDCG@5/10 with
gain `2^grade - 1`. These metrics are separately reported but share the same ranked
output; they describe ranking quality within the supplied synthetic pool. They do not
measure recall of live OpenAlex queries or establish production ranking quality.

### Baseline results and error analysis

| Fixed-pool top-K recall | Result | Ranking | Result |
|---|---:|---|---:|
| Recall@5 | 0.8333 | Precision@5 | 0.5000 |
| Recall@10 | 0.9167 | MRR | 1.0000 |
| Recall@20 | 0.9444 | Graded nDCG@5 | 0.8314 |
| Ranked-pool fraction@20 (selection depth only) | 0.8000 | Graded nDCG@10 | 0.8650 |

Across 12 queries, there were 30 grade-0 top-five results (2.5 per query on average)
and two positive judgments below depth 20: `PUB-ENE-02` (grade 2, `ENE-Q2`) and
`PUB-BIO-03` (grade 1, `BIO-Q1`). The first positive was ranked first on all queries,
which explains MRR=1.0; it does not mean all positive candidates were ranked near the
top. Difficult negatives remained competitive when sharing terms but differing in
meaning, including crop nutrient stress vs. crop infection, irrigation vs. water
contamination, and electricity demand vs. solar generation. Some cross-domain records
also ranked highly due to common-token overlap.

Repeated evaluation with unchanged candidate order produced identical rankings. Reversing
candidate input order changed the order of tied candidates in all 12 queries; there were
49 tied score groups and mean pairwise ordering agreement was 0.8867. Thus ranking is
repeatable for fixed input, but tie order is input-dependent.

No alternative ranker was tested or adopted. The observed lexical and tie weaknesses
justify a future controlled comparison, but do not justify a production scoring change
from this small, hand-authored dataset. No retrieval improvement is claimed.

### Regression results, limitations, and next activity

- Backend: **187 passed**, including Phase 2 workflow, OpenAlex state/deduplication,
  evidence provenance, API error redaction, and the new dataset/metric tests.
- Literature-source regression tests: **19 passed**, including DOI URL/bare DOI
  normalization, cross-ID DOI deduplication, and case-folded record-ID fallback.
- Frontend: **72 passed** across six files; ESLint, TypeScript checking, and production
  build passed.
- Changed Python files: Ruff passed. Repository-wide Ruff reports the pre-existing
  import-order finding in `services/plagiarism/attribution.py`.
- The baseline output is byte-for-byte repeatable and records the dataset SHA-256.

Limitations remain substantial: judgments are hand-authored rather than independently
adjudicated; there are only six domains and twelve English query variants; all queries
share the same small catalog; and 264/300 judgments are easy cross-domain negatives.
The pool is supplied rather than discovered by a live source, and synthetic performance
does not validate scientific relevance, institutional screening, plagiarism, or
funding decisions. Missing-abstract behavior is represented in the fixture, but the
offline ranker uses available title text and does not reproduce all OpenAlex response,
pagination, or network failure modes. Live OpenAlex validation remains blocked as
documented above. The dataset, metric, test, and result artifacts preserve existing
Phase 2 reference metrics rather than overwriting them. `npm ci` also reported
18 existing lockfile dependency advisories (9 moderate, 6 high, 3 critical); this task
did not change dependencies or investigate/remediate those advisories.

**Recommendation:** before proposing a ranking change, obtain authorization for a
privacy-reviewed, representative publication/query set; have domain reviewers label
candidate relevance with rationales; and compare the baseline and any alternative on
identical query/candidate pools while separately validating live-source retrieval,
coverage, provenance, and source-state behavior. Until then, retain the current behavior
and keep all consequential screening decisions under human authority. Phase 3 is not
complete.
