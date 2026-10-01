# NRIF Grant Screening — Problem Framing and Product Requirements

## Primary user
NCST / National Research and Innovation Fund (NRIF) technical staff responsible for administrative screening of grant applications in RIGMS.

## Current workflow
Applicants submit through RIGMS → staff check completeness and eligibility → plagiarism/similarity screening → eligible proposals proceed to peer review.

## Product objective
shakaHive should reduce repetitive screening effort while improving consistency and traceability. It complements RIGMS and existing plagiarism tooling; it does not replace either system or make final funding decisions.

## MVP AI capabilities
1. Document extraction from PDF/DOCX.
2. Completeness detection against a configurable checklist.
3. Eligibility evaluation using machine-readable criteria plus evidence extraction.
4. Semantic candidate retrieval against historical applications when approved data is available.
5. Duplicate / near-duplicate candidate detection.
6. Text-overlap analysis as evidence, never as an automatic plagiarism verdict.
7. Explainable confidence and source/page evidence.
8. Human review and auditable decisions.

## Evidence contract
Every flag should be traceable to: source document → extracted text/chunk → model or rule → score → evidence → reviewer decision.

## Data policy
Real RIGMS/historical applications are required only after NCST/NRIF authorization. Until then, synthetic fixtures are explicitly labelled demo data. Missing data remains missing; the system must not infer completeness from absence.

## Validation questions
- What is the current plagiarism tool and coverage?
- Which eligibility criteria are deterministic and machine-readable?
- What are proposal volumes and median screening times per call?
- How are historical duplicates currently found?
- Which RIGMS integration/API is available?
- Which fields/documents are confidential and what retention rules apply?

## Success measurement
The pilot should establish a baseline first, then measure screening time, eligibility precision/recall on labelled cases, duplicate retrieval quality, evidence traceability, and reviewer acceptance of AI flags. No final funding decision is automated.
