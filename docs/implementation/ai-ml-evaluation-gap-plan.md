# AI/ML Evaluation and Benchmark Gap Plan

**Scope:** existing evidence and required pre-operational evidence.

## Existing datasets

| Capability | Dataset/evidence | Scale and labels | Status |
|---|---|---|---|
| Retrieval baseline | `data/evaluation/retrieval_benchmark.json` | 4 hand-authored synthetic cases | Diagnostic |
| Adversarial retrieval | `data/evaluation/retrieval_benchmark_adversarial.json` | 10 hard synthetic cases; relevant candidate IDs | Diagnostic synthetic |
| Retrieval ranking | `data/evaluation/retrieval_evaluation_v1.json` / `_results.json` | 12 queries, 6 groups, 27 catalog records, 25 unique candidates/query after dedupe; 0–3 graded labels | Fixed-pool synthetic ranking baseline; independent generation recall explicitly not evaluated |
| Proposal similarity | `data/evaluation/similarity_benchmark.json` | 10 pairs; true/false review-worthy overlap labels | Diagnostic, not plagiarism |
| Published literature | Mocked OpenAlex records and synthetic applications in `tests/test_plagiarism_openalex.py` | Synthetic record metadata and one demo proposal | Mocked/unvalidated live source |
| Purpose overlap | Current tests in `tests/test_duplication_detection.py` | Exact/substantial/topic/distractor cases | Text duplication diagnostic, not structured purpose |
| Eligibility/completeness | Synthetic applications and RFP fixtures | Workflow integration cases | Rule correctness for synthetic fixtures only |

## Existing metrics

Baseline and adversarial benchmark results are recorded in `README.md`, `docs/ai-ml/retrieval-evaluation.md` and test artifacts. The fixed-pool v1 result reports recall@5/10/20, precision@5, MRR and nDCG@5/10. These support no production retrieval or duplicate-screening accuracy claim.

Existing tests prove:
- Candidate ranking/lexical/embedding/hybrid/reranker behavior.
- Stable and repeatable synthetic metrics.
- Source and candidate provenance and failure coverage.
- Duplicate exact/substantial/possible heuristic behavior.
- Public/published source metadata handling.
- No live institutional, real-world or comprehensive-source recall evidence.

## Capability-by-capability gap

| Capability | Dataset needed | Positive/negative design | Metrics | Missing evidence |
|---|---|---|---|---|
| Candidate generation recall | Authorized representative proposal/project corpus and external source index | Known relevant records, near-topic negatives, unavailable-source cases | Recall@k, source recall, failure/blocked rate | Independent query generation; current fixed pool and synthetic queries |
| Retrieval ranking | Expert graded proposal-to-record pairs | Relevant, weak, distractor and cross-domain records | nDCG@k, MRR, P@k, calibration | Human relevance adjudication and disjoint call split |
| Purpose-overlap quality | Structured profile gold labels: purpose, objective, beneficiary, intervention, methodology, outputs, outcomes, geography/population and scope | Same topic/different purpose, replication, follow-on, differentiated design, true duplicate | Per-dimension F1, candidate recall, label agreement, false-positive burden | No structured gold set or expert protocol |
| Plagiarism evidence precision/coverage | Authorized source snapshots with copied, paraphrased, quoted/cited, boilerplate and independent passages | Positive/negative/ambiguous; source available/unavailable | Passage precision/recall, source recall, false-positive/negative, coverage | Live source precision/coverage and expert misconduct adjudication |
| Human reviewer agreement | Expert-adjudicated findings and criterion ratings | Independent two-expert plus adjudicator cases | Exact/within-one agreement, weighted kappa/ICC, override, burden | No expert-labelled applications |
| Application assessment reliability | Representative call/rubric/application set | Eligible/ineligible/pending; complete/incomplete; missing/insufficient; 0–4 anchor examples | Criterion exact/within-one agreement, eligibility P/R, false positive/negative, calibration, score/rank stability | No rubric or expert gold set |
| Funding overlap | Authorized award/commitment records with overlapping period/budget/deliverable fields | Different wording, partial and non-overlap | Entity precision/recall, overlap precision/recall, false-positive burden | No institutional award corpus |

## Required data governance

- Written authorization and provenance for source and applicant data.
- Data card: collection, allowed uses, retention, personal/sensitive fields, languages, geography and source versions.
- Label guide and independent expert adjudication.
- Disjoint train/validation/test splits by applicant, institution and time/call where possible.
- Leakage review for duplicate proposals, shared metadata and public papers.
- Protected subgroup/context slices only under lawful, consented governance.
- Prohibit protected-attribute inference; do not label protected traits automatically.

## Reproducibility requirements

- Freeze dataset IDs, SHA-256, label schema and labeler/adjudicator protocol.
- Pin model/provider, revision, prompt/config and calculator/reranker versions.
- Record candidate pool construction and live-source retrieval coverage.
- Store test results and environment metadata.
- Report confidence intervals or uncertainty when sample size supports it.
- Separate source-retrieval recall from ranking within supplied pools.

## Operational thresholds

Do not tune production thresholds from:
- 4-case or 10-case retrieval sets.
- 10 pair similarity fixtures.
- Mocked OpenAlex responses.
- Synthetic demo applications.

Before thresholds, approve:
- Error-cost and false-negative/positive policy.
- Reviewer workload limit and escalation categories.
- Minimum recall/precision for each capability.
- Human adjudication protocol and fallback behavior.

## Known failure patterns

- Lexical overlap misses semantic rewrites.
- Embedding passage similarity can confuse topic and purpose.
- Reranker logit is relevance, not probability or misconduct.
- Publication abstract-only matching lacks full-text coverage.
- HTML/PDF source retrieval may miss or misidentify passages.
- Generic methodology and institutional boilerplate cause false positives.
- Candidate ranking tie and input-order behavior can affect results.
- Source failure is not no-match.
