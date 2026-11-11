# AI/ML Implementation and Evaluation Standard

## Purpose and boundaries

AI/ML finds relevant information and candidate similarities. It does not make funding decisions, issue plagiarism verdicts or replace scientific peer review. Deterministic configured rules handle explicit conditions; ML/NLP supports semantic retrieval, ranking and validated discovery; humans decide consequential outcomes.

## Data governance

For every dataset record owner/source/date; permission and allowed purpose; sensitivity classification; anonymization method; label definitions and adjudication; inclusion/exclusion criteria and bias; train/validation/test splits and leakage prevention; retention/deletion. Use synthetic or explicitly authorized data. Never use confidential submissions in public benchmarks, external AI APIs or developer machines without written approval and security review.

## Baselines before complexity

1. Exact/checksum match for identical files.
2. Normalized text and lexical retrieval (e.g. BM25/TF-IDF).
3. Embedding retrieval for semantic candidates.
4. Cross-encoder reranking only if measured gains justify latency and cost.

Keep providers/models replaceable behind a stable interface.

## Evaluation

Maintain a versioned labelled evaluation set with representative formats and edge cases. Separate tuning from held-out evaluation; prevent related proposals/near-duplicates crossing splits.

Measure as applicable:
- Retrieval: Recall@k, Precision@k, MRR, nDCG.
- Duplicate candidates: precision, recall, F1 and false-positive rate.
- Eligibility: per-rule correctness, precision/recall and confusion matrix against verified labels.
- Extraction: field-level precision/recall and page/source localization.
- Evidence: validity, coverage, attribution correctness and reviewer usefulness.
- Operations: latency, throughput, failure rate and cost per application.

Report sample size, class distribution, methodology, uncertainty where practical, thresholds, model/dataset versions, baseline comparison and error analysis. No uncontextualized single accuracy score.

## Threshold and decision policy

Calibrate thresholds on labelled examples and document false-positive/false-negative trade-offs. Use Needs Review when uncertain. Never convert model scores directly into funding eligibility or rejection. Similarity is not proof of plagiarism; novelty is not scientific judgement. Low coverage reduces certainty and must be visible. Unavailable sources are Not Searched/Unavailable, not “no matches”. Threshold changes require evaluation evidence, rationale and AI/ML owner approval with Platform review.

## Evidence and provenance

Retain run/input versions; model/embedding/tokenizer/prompt/config versions; method and parameters; candidate/source coverage; supporting passages with page/chunk offsets; score meaning; limitations; reviewer disposition/rationale. Do not present generated explanations as source evidence. Do not call raw scores calibrated probabilities unless validated.

## Reproducibility and monitoring

Version code, models, preprocessing, prompts, config, dataset and evaluation scripts. Record runtime/provider details where material. Review false positives/negatives, language variation, formatting, terminology, document length and malformed files. Track reviewer overrides/disagreements and drift where lawful and statistically meaningful.

## AI/ML release gate

Permission and provenance documented; baseline/evaluation set exist; metrics/error analysis reviewed; evidence references validated; failure/unavailable states implemented; thresholds/limitations shown in UI; disable/rollback switch exists; human review remains in control.
