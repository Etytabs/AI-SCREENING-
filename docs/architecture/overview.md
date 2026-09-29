# Architecture Overview

AI-SCREENING is an AI/ML-centered research intelligence platform, not an LLM wrapper.

## Core decision chain
SOURCE → INGESTION → NORMALIZATION → VALIDATION → MODEL → CONFIDENCE → EVIDENCE → HUMAN REVIEW → AUDIT → RESULT

## Grant screening
Proposal → extraction → eligibility rules → semantic similarity/duplicate analysis → text-overlap analysis → evidence and confidence → human review → audit.

## Publication reconciliation
Local repository or optional connector → normalization → author/entity resolution → duplicate detection → metadata reconciliation → confidence → human verification → synchronization.

International databases are optional connectors. The pilot remains useful with local repository data.

## Integrity principles
- Rules, ML models, retrieval, and LLM reasoning are separate components.
- LLMs assist defined tasks; they do not become the sole decision-maker.
- Missing data is preserved as missing.
- Synthetic fixtures are explicitly labeled.
- Provenance, uncertainty, evidence, and human decisions are retained.
