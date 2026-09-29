# Model Contracts

Each production model must declare:

- task and intended decision support
- input schema
- output schema
- training/evaluation dataset and version
- model/version identifier
- threshold or ranking policy
- known limitations
- confidence interpretation
- provenance requirements
- human-review policy

A similarity score is evidence for review, not proof of duplication or plagiarism. A confidence score describes model/evidence agreement under the documented calibration method; it is not a probability of truth unless explicitly calibrated and validated as such.
