# Retrieval benchmark execution

The benchmark runner connects the labelled synthetic corpus to the same ranking interfaces used by the screening retrieval path.

## Current baseline

The lexical pipeline is executable without an ML model and provides the CI reference:

- Recall@5: 1.00
- Precision@5: 0.20
- MRR: 1.00
- nDCG@5: 1.00

These results are from four synthetic cases with one labelled relevant candidate per case. They are a regression baseline, not production performance.

## Embedding and hybrid evaluation

The production embedding path uses the configured SentenceTransformer model. CI intentionally keeps that runtime disabled so tests do not download or execute a model.

When embeddings are enabled, the benchmark runner can evaluate lexical, embedding, and hybrid strategies using the same candidate pools, labels and K.

- lexical — existing lexical ranking;
- embedding — cosine similarity over the configured embedding model;
- hybrid — the existing 35% lexical / 65% semantic fusion.

## Why the cross-encoder comes later

A cross-encoder changes the retrieval architecture by scoring a query-candidate pair jointly. It should therefore be introduced only after the first-stage lexical, embedding and hybrid baselines have been measured on the same benchmark.

The next implementation should record model name/revision, K, dataset version, and all four metrics for every run, then compare the cross-encoder against the established first-stage baseline.

## CI reference

The retrieval reference results file records the current synthetic lexical baseline and explicitly marks production embedding/hybrid evaluation as not run in CI.
