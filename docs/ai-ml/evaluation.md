# AI/ML Evaluation

The platform must evaluate models against labeled datasets before using them for consequential decisions.

## Initial metrics
- Eligibility: accuracy, precision, recall where labels permit.
- Duplicate detection: precision, recall, F1.
- Entity resolution: precision, recall, F1.
- Similarity/retrieval: recall@k and ranking quality.
- Confidence: calibration error and reliability curves.
- Extraction: field-level precision/recall.

## Evaluation rules
- Keep train, validation, and test data separated.
- Record dataset version and provenance.
- Compare new models against a documented baseline.
- Do not treat similarity score as proof of duplication or plagiarism.
- Human reviewers validate consequential decisions.
