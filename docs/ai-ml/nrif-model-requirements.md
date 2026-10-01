# NRIF Model Requirements

## Model boundaries
shakaHive separates four classes of intelligence:

- deterministic completeness/eligibility rules;
- semantic retrieval and embedding similarity;
- duplicate/entity-resolution models;
- text-overlap analysis and optional language-model reasoning.

An LLM may assist extraction or explanation, but it is not the sole decision-maker.

## Required model outputs
Production models must return the prediction, score, model/version identifier, input provenance, supporting evidence IDs, and known limitations.

## Consequential decisions
The system only produces screening assistance. Human reviewers remain responsible for eligibility interpretation, plagiarism conclusions, and funding decisions.

## Evaluation dataset
Before production claims, create a labelled evaluation set from approved historical applications. Keep training, validation, and test sets separated. Include positive, negative, borderline, and missing-data cases.

## Metrics
- Eligibility: precision, recall, accuracy by criterion.
- Duplicate retrieval: precision, recall, F1 and Recall@K.
- Semantic retrieval: Recall@K and ranking quality.
- Extraction: field-level precision/recall.
- Confidence: calibration error after calibration is actually validated.
- Operations: latency and screening-time change against a measured baseline.
