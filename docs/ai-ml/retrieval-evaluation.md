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
