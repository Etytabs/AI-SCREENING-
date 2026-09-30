# Retrieval evaluation

## Purpose

The retrieval layer ranks historical records or evidence candidates for a screening query. This evaluation measures ranking quality before a second-stage reranker is introduced.

The benchmark is intentionally synthetic until authorized historical proposal data and validated relevance labels are available.

## Metrics

- Recall@K: fraction of labelled relevant candidates appearing in the top K.
- Precision@K: fraction of the top K results that are labelled relevant.
- MRR: reciprocal rank of the first relevant result.
- nDCG@K: position-sensitive ranking quality relative to the ideal ordering.

These are retrieval metrics. They are not confidence scores, probabilities of duplication, plagiarism findings, eligibility decisions, or funding recommendations.

## Benchmark

The synthetic benchmark contains four grant-screening queries and labelled historical candidates.

Each case defines a screening query, candidate historical records, and one or more labelled relevant candidates. The labels are demonstration labels only and must not be represented as official NRIF relevance judgements.

## Evaluation protocol

Compare retrieval strategies using the same candidate pool and relevance labels:

1. lexical baseline;
2. embedding-only retrieval;
3. hybrid lexical + embedding retrieval;
4. later, a true second-stage cross-encoder reranker.

Report Recall@K, Precision@K, MRR and nDCG@K for the same K values.

Record the dataset version, model name/revision, retrieval weights and evaluation date with every experiment.

## Limitations

The synthetic benchmark cannot establish production performance. Before deployment, evaluation should use an authorized, de-identified and representative dataset with reviewer-validated relevance labels, held-out evaluation data, and documented error analysis.
