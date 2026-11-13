# Retrieval benchmark execution

The benchmark runner connects labelled synthetic corpora to the same ranking interfaces used by the screening retrieval path.

## Benchmark #1 baseline

The lexical pipeline is executable without an ML model and provides the CI reference:

- Recall@5: 1.00
- Precision@5: 0.20
- MRR: 1.00
- nDCG@5: 1.00

These results are from four synthetic cases with one labelled relevant candidate per case. They are a regression baseline, not production performance.

The first model-backed run also measured embedding and hybrid retrieval on this dataset. All three strategies produced the same metrics, so Benchmark #1 does not demonstrate a retrieval advantage for embeddings.

## Benchmark #2 — adversarial retrieval

`data/evaluation/retrieval_benchmark_adversarial.json` is a separate synthetic corpus designed to expose retrieval failure modes that the first benchmark did not test.

It includes:

- low lexical-overlap paraphrases;
- semantically related proposals using different terminology;
- lexically tempting but incorrect candidates;
- near-topic distractors;
- researcher-name and abbreviation variation;
- publication reconciliation cases;
- duplicate-versus-related proposal distinctions;
- evidence retrieval for eligibility criteria;
- multiple relevant candidates.

The benchmark contains 10 cases with five candidates per case. Labels are benchmark annotations only and are not official NRIF decisions.

Benchmark #2 should be interpreted as a diagnostic evaluation. A semantic or hybrid method performing better is evidence for this synthetic corpus only; it does not establish production performance.

The lexical-only execution on 12 November 2026 measured Recall@5 **1.00**, Precision@5
**0.24**, MRR **0.562** and nDCG@5 **0.667** across the 10 synthetic cases. The high
recall but low precision/ranking scores show that relevant candidates are retrieved but
often mixed with distractors. At Precision@5 0.24, only about 1.2 of five returned
candidates per query were labeled relevant on average in this small set; the remaining
results need human filtering. These metrics describe retrieval labels, not plagiarism
probability or scientific validity. Embedding and reranker strategies were not run in
this execution; these results are not scientific or institutional validation.

## Phase 3 comparison and similarity diagnostic

The Phase 3 audit preserved both Phase 2 retrieval datasets and reran the deterministic
lexical method. No ranking change was accepted: a weighted lexical and BM25 experiment
reduced adversarial MRR and nDCG@5, so the existing ranking behavior remains the baseline.
The Phase 3 query cleanup and OpenAlex provenance fixes do not alter these synthetic
ranked candidate lists.

| Dataset | Queries | Recall@5 | Precision@5 | MRR | nDCG@5 |
|---|---:|---:|---:|---:|---:|
| Synthetic baseline (`v0.1`) | 4 | 1.00 | 0.20 | 1.00 | 1.00 |
| Synthetic adversarial (`v0.1`) | 10 | 1.00 | 0.24 | 0.562 | 0.667 |

`data/evaluation/similarity_benchmark.json` is a separate, ten-pair synthetic dataset
covering exact and partial overlap, paraphrase, common terminology, references, boilerplate,
institutional templates, same-topic independent work, asymmetric source/application
coverage and unrelated documents. Run it with:

`python -m scripts.evaluate_similarity`

The current diagnostic result is precision **0.429** (3 true positives, 4 false positives)
and recall **0.750** (3 true positives, 1 false negative), with 2 true negatives. False
positives are shared research terminology, references, standard methodology and a repeated
institutional template; the paraphrased case is a false negative. These hand-authored
labels are test fixtures for error analysis, not plagiarism judgements or production
performance estimates. Do not tune thresholds to this small corpus.

The text-overlap measure keeps application-side and source-side coverage distinct. Retrieval
precision/recall and reviewer decisions remain separate: a retrieved match is not a
plagiarism finding, and a reviewer decision is not a retrieval label. OpenAlex source
availability and unusable-result counts are recorded independently from matched-source
counts.

## Expanded fixed-pool graded ranking diagnostic — v1.0

`data/evaluation/retrieval_evaluation_v1.json` is a new, frozen synthetic benchmark.
It supplements rather than replaces the Phase 2 corpora above. It contains 27 catalog
records, which collapse by the same normalized DOI/record-ID key used by the literature
source to 25 unique works per query; 12 query variants (research questions and proposal
statements) span six domains. Each query has 25 unique candidates, including relevant,
weakly relevant, and irrelevant records. Graded labels use 0 (not relevant), 1 (weak),
2 (relevant), and 3 (highly relevant), with a rationale for every label: case-level
default rationales cover the cross-domain negatives, and explicit judgments cover
same-domain matches and difficult negatives.

The fixture intentionally includes paraphrases with limited shared vocabulary, highly
lexical but meaningfully different candidates, a same-DOI duplicate, a distinct-DOI
near-duplicate, title-only metadata, an absent abstract, and one record with no searchable
metadata. All records and judgments are synthetic and hand-authored; labels have not
been adjudicated by domain experts. The dataset is a diagnostic fixture, not evidence of
institutional or scientific validity.

Known sampling biases include a shared catalog for all query groups, only two phrasings
per domain, English-only terminology, and many easy cross-domain grade-0 examples
(264/300 judgments are grade 0). The few same-domain hard negatives and positive
paraphrases cannot represent the diversity or ambiguity of real scholarly queries.
Dataset labels reflect one synthetic construction, not inter-rater agreement.

Run the model-free baseline and write the deterministic result artifact with:

```sh
python -m scripts.evaluate_retrieval_dataset \
  --dataset data/evaluation/retrieval_evaluation_v1.json \
  --output data/evaluation/retrieval_evaluation_v1_results.json
```

The evaluator deduplicates by DOI/record ID, concatenates available title and abstract
text, and supplies all 25 unique records directly to the existing `rank_candidates`
token-Jaccard ranker without changing its scoring formula. The artifact field
`ranked_pool_recall_metrics` reports fixed-pool Recall@K: the fraction of all judged
relevant candidates that appear in the top K of the supplied pool. These values do not
measure independent candidate generation or the retrieval of records outside the
supplied pool. Independent candidate generation and live-source retrieval recall have
not been evaluated.

The artifact's `ranked_pool_fraction_at_20` is a selection-depth statistic (20 of the
25 supplied records, or 0.8), not a retrieval-quality measure. Relevant-candidate
retrieval rate@20 is omitted because it is mathematically identical to Recall@20 in
this fixed-pool experiment. Ranking metrics describe ordering within the same ranked
pool: Precision@5 and MRR treat grades 1–3 as relevant; nDCG uses graded gain
`2^grade - 1`. These offline ranking metrics do not measure live OpenAlex query recall:
in the current literature workflow OpenAlex supplies result order, records are
deduplicated and abstract-filtered, and the generic ranker does not reorder those works
before text comparison.

The 13 November 2026 lexical-only baseline is:

| Evaluation view | Metric | Result |
|---|---|---:|
| Fixed-pool top-K recall | Recall@5 | 0.8333 |
| Fixed-pool top-K recall | Recall@10 | 0.9167 |
| Fixed-pool top-K recall | Recall@20 | 0.9444 |
| Selection depth (not retrieval quality) | Ranked-pool fraction@20 | 0.8000 |
| Ranking | Precision@5 | 0.5000 |
| Ranking | MRR | 1.0000 |
| Ranking | Graded nDCG@5 | 0.8314 |
| Ranking | Graded nDCG@10 | 0.8650 |

The 12 query variants have 300 deduplicated query-work judgments: 264 grade 0, 12
grade 1, 12 grade 2, and 12 grade 3. There were 30 grade-0 results in top-five lists
(2.5 per query on average) and two positive judgments below depth 20: a grade-2,
lexically weaker photovoltaic paraphrase for `ENE-Q2`, and a grade-1 conservation
context candidate for `BIO-Q1`. The first positive candidate was ranked first for every
query, so MRR=1.0 does not imply that all relevant candidates were ranked well; the
graded nDCG exposes weaker ordering among the remaining positives.

Repeated runs with identical input were identical. Reversing candidate input order
changed tied ordering for all 12 queries; there were 49 non-singleton tie groups and
mean pairwise ordering agreement was 0.8867. The stable sort is deterministic for a
fixed input but inherits input order for equal Jaccard scores. Frequent top-five errors
include high-overlap distractors (for example crop nutrient stress vs. crop infection,
irrigation vs. water contamination, and weather-driven electricity demand vs. solar
generation) and unrelated records that share common words.

This run does not compare an alternative ranker. It confirms limitations in lexical
matching and tie behavior, but the labels are hand-authored, the corpus is small, and
the candidate pool is supplied rather than discovered from OpenAlex. No ranker change is
accepted from this diagnostic. The output JSON includes per-query results, rationales
for false positives/negatives, a dataset SHA-256, and tie-consistency diagnostics so a
future experiment can use the identical candidate pool and labels.

## Cross-encoder reranking

The retrieval stack now supports a true second-stage cross-encoder:

1. First-stage hybrid retrieval ranks the candidate pool using lexical overlap plus sentence embeddings.
2. The top `rerank_k` candidates are passed as query-candidate pairs to a cross-encoder.
3. The cross-encoder scores each pair jointly.
4. The reranked top `k` candidates are returned with first-stage and cross-encoder scores.

The default reranker is `cross-encoder/ms-marco-MiniLM-L-6-v2`. It is disabled by default and loaded lazily only when `AI_SCREENING_RERANKER_ENABLED=true`.

This is intentionally distinct from the embedding model. The embedding model represents query and candidate independently; the cross-encoder evaluates the pair jointly.

## Benchmark #3

Benchmark #3 evaluates:

- lexical;
- embedding;
- hybrid;
- hybrid + cross-encoder reranking.

It uses the same 10-case adversarial corpus and reports Recall@5, Precision@5, MRR and nDCG@5. This allows the reranker to be evaluated against the established first-stage methods without changing the labelled candidate pool.

The benchmark must be treated as synthetic diagnostic evidence. A reranker improvement does not establish production performance until it is validated on an authorized, representative dataset.

## Reproducible commands

Benchmark #1:

`python -m scripts.evaluate_retrieval --dataset data/evaluation/retrieval_benchmark.json`

Benchmark #2:

`python -m scripts.evaluate_retrieval --dataset data/evaluation/retrieval_benchmark_adversarial.json --output data/evaluation/retrieval_benchmark_2_results.json`

Benchmark #3:

`AI_SCREENING_EMBEDDINGS_ENABLED=true AI_SCREENING_RERANKER_ENABLED=true python -m scripts.evaluate_retrieval --dataset data/evaluation/retrieval_benchmark_adversarial.json --k 5 --rerank-k 5 --output data/evaluation/retrieval_benchmark_3_results.json`

The output records dataset, timestamp, K, rerank pool size, embedding model/revision, reranker model/revision and metrics.

## GitHub Actions

The original manual `Retrieval Benchmark` workflow remains the Benchmark #1 path.

`Retrieval Benchmark #2` runs the adversarial first-stage comparison with `sentence-transformers/all-MiniLM-L6-v2`.

`Retrieval Benchmark #3 - Reranker` enables both the embedding model and `cross-encoder/ms-marco-MiniLM-L-6-v2`, then uploads `retrieval_benchmark_3_results.json`.

The model-backed workflows are intentionally separate from required CI because model downloads add latency and external runtime dependencies to every commit. Normal CI remains deterministic and model-free.
