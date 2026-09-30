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

## Strategies

When embeddings are enabled, the benchmark runner evaluates:

- lexical — existing lexical ranking;
- embedding — cosine similarity over the configured embedding model;
- hybrid — the existing 35% lexical / 65% semantic fusion.

The same candidate pools, labels and K are used for each strategy.

## Why the cross-encoder comes later

A cross-encoder changes the retrieval architecture by scoring a query-candidate pair jointly. It should therefore be introduced only after first-stage lexical, embedding and hybrid methods have been measured on a sufficiently difficult benchmark.

The next decision should be based on Benchmark #2 results, not on an assumed advantage. If first-stage retrieval still produces materially wrong rankings, the next step can be a true cross-encoder reranker evaluated against the same cases.

## Reproducible commands

Benchmark #1:

`python -m scripts.evaluate_retrieval --dataset data/evaluation/retrieval_benchmark.json`

Benchmark #2:

`python -m scripts.evaluate_retrieval --dataset data/evaluation/retrieval_benchmark_adversarial.json --output data/evaluation/retrieval_benchmark_2_results.json`

For a model-backed run, enable the configured SentenceTransformer runtime with `AI_SCREENING_EMBEDDINGS_ENABLED=true`, optionally set `AI_SCREENING_EMBEDDING_MODEL` and `AI_SCREENING_EMBEDDING_REVISION`, then run the command.

The output records the dataset, timestamp, K, model, revision and metrics.

## GitHub Actions

The original manual `Retrieval Benchmark` workflow remains the Benchmark #1 path.

A separate manual `Retrieval Benchmark #2` workflow runs the adversarial corpus with `sentence-transformers/all-MiniLM-L6-v2` and uploads `retrieval_benchmark_2_results.json` as an artifact.

The model-backed workflows are intentionally separate from required CI because model downloads add latency and external runtime dependencies to every commit. Normal CI remains deterministic and model-free.
