import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from ml.evaluation.retrieval import (
    graded_ndcg_at_k,
    mean_reciprocal_rank,
    precision_at_k,
    recall_at_k,
)
from ml.evaluation.retrieval_dataset import (
    deduplicate_candidates,
    expand_judgments,
    load_dataset,
)
from ml.semantic_matching.hybrid import rank_candidates

DEFAULT_DATASET = Path("data/evaluation/retrieval_evaluation_v1.json")
RETRIEVAL_DEPTH = 20


def _rounded(value: float) -> float:
    return round(value, 6)


def _candidate_text(candidate: dict[str, Any]) -> str:
    return " ".join(
        part.strip()
        for part in (candidate.get("title") or "", candidate.get("abstract") or "")
        if part and part.strip()
    )


def _pairwise_order_agreement(first: list[str], second: list[str]) -> float:
    first_rank = {candidate_id: rank for rank, candidate_id in enumerate(first)}
    second_rank = {candidate_id: rank for rank, candidate_id in enumerate(second)}
    agreements = total = 0
    for index, left in enumerate(first):
        for right in first[index + 1:]:
            total += 1
            agreements += (first_rank[left] < first_rank[right]) == (
                second_rank[left] < second_rank[right]
            )
    return agreements / total if total else 1.0


def _tie_groups(scored: list[Any]) -> list[list[str]]:
    groups: dict[float, list[str]] = defaultdict(list)
    for item in scored:
        groups[item.fused_score].append(item.candidate_id)
    return [candidate_ids for candidate_ids in groups.values() if len(candidate_ids) > 1]


def evaluate_dataset(dataset_path: Path) -> dict[str, Any]:
    dataset = load_dataset(dataset_path)
    raw_candidates = dataset["candidates"]
    query_results: list[dict[str, Any]] = []
    label_counts: Counter[int] = Counter()
    false_positives: list[dict[str, Any]] = []
    false_negatives: list[dict[str, Any]] = []
    totals: Counter[str] = Counter()
    consistency_scores: list[float] = []
    tie_sensitive_query_count = 0

    for case in dataset["cases"]:
        expanded_labels = expand_judgments(case, raw_candidates)
        candidates, labels = deduplicate_candidates(raw_candidates, expanded_labels)
        relevance = {
            candidate_id: judgment["grade"]
            for candidate_id, judgment in labels.items()
        }
        candidate_pairs = [
            (candidate["candidate_id"], _candidate_text(candidate))
            for candidate in candidates
        ]
        for variant in case["query_variants"]:
            ranked = rank_candidates(
                variant["text"],
                candidate_pairs,
                embedder=None,
                top_k=len(candidate_pairs),
            )
            ranked_ids = [item.candidate_id for item in ranked]
            repeat = rank_candidates(
                variant["text"],
                candidate_pairs,
                embedder=None,
                top_k=len(candidate_pairs),
            )
            repeat_is_identical = [
                (item.candidate_id, item.fused_score) for item in ranked
            ] == [(item.candidate_id, item.fused_score) for item in repeat]

            reversed_ranked = rank_candidates(
                variant["text"],
                list(reversed(candidate_pairs)),
                embedder=None,
                top_k=len(candidate_pairs),
            )
            reversed_ids = [item.candidate_id for item in reversed_ranked]
            agreement = _pairwise_order_agreement(ranked_ids, reversed_ids)
            consistency_scores.append(agreement)
            ties = _tie_groups(ranked)
            reversed_positions = {
                candidate_id: rank for rank, candidate_id in enumerate(reversed_ids)
            }
            ranked_positions = {
                candidate_id: rank for rank, candidate_id in enumerate(ranked_ids)
            }
            sensitive_ties = [
                group for group in ties
                if any(
                    ranked_positions[left] < ranked_positions[right]
                    and reversed_positions[left] > reversed_positions[right]
                    for index, left in enumerate(group)
                    for right in group[index + 1:]
                )
            ]
            tie_sensitive_query_count += bool(sensitive_ties)

            positive_ids = {
                candidate_id for candidate_id, grade in relevance.items() if grade > 0
            }
            top_20 = ranked_ids[:RETRIEVAL_DEPTH]
            top_5 = ranked_ids[:5]
            relevant_retrieved = len(set(top_20) & positive_ids)
            metric_row = {
                "recall_at_5": _rounded(recall_at_k(ranked_ids, positive_ids, 5)),
                "recall_at_10": _rounded(recall_at_k(ranked_ids, positive_ids, 10)),
                "recall_at_20": _rounded(recall_at_k(ranked_ids, positive_ids, 20)),
                "candidate_coverage_at_20": _rounded(len(top_20) / len(candidates)),
                "relevant_candidate_retrieval_rate_at_20": _rounded(
                    relevant_retrieved / len(positive_ids)
                ),
                "precision_at_5": _rounded(precision_at_k(ranked_ids, positive_ids, 5)),
                "mrr": _rounded(mean_reciprocal_rank(ranked_ids, positive_ids)),
                "ndcg_at_5": _rounded(graded_ndcg_at_k(ranked_ids, relevance, 5)),
                "ndcg_at_10": _rounded(graded_ndcg_at_k(ranked_ids, relevance, 10)),
            }
            for candidate_id, grade in relevance.items():
                label_counts[grade] += 1
            for candidate_id in top_5:
                if relevance[candidate_id] == 0:
                    false_positives.append({
                        "query_id": variant["query_id"],
                        "candidate_id": candidate_id,
                        "grade": 0,
                        "rationale": labels[candidate_id]["rationale"],
                        "rank": ranked_ids.index(candidate_id) + 1,
                    })
            for candidate_id in positive_ids - set(top_20):
                false_negatives.append({
                    "query_id": variant["query_id"],
                    "candidate_id": candidate_id,
                    "grade": relevance[candidate_id],
                    "rationale": labels[candidate_id]["rationale"],
                })
            totals.update(metric_row)
            query_results.append({
                "query_id": variant["query_id"],
                "query_type": variant["type"],
                "candidate_count": len(candidates),
                "positive_candidate_count": len(positive_ids),
                "metrics": metric_row,
                "ranking_consistency": {
                    "repeat_is_identical": repeat_is_identical,
                    "pairwise_order_agreement_vs_reversed_input": _rounded(agreement),
                    "tie_group_count": len(ties),
                    "input_order_sensitive_tie_group_count": len(sensitive_ties),
                },
                "top_20": [
                    {
                        "candidate_id": item.candidate_id,
                        "grade": relevance[item.candidate_id],
                        "score": _rounded(item.fused_score),
                    }
                    for item in ranked[:RETRIEVAL_DEPTH]
                ],
            })

    query_count = len(query_results)
    average_metrics = {
        key: _rounded(totals[key] / query_count)
        for key in (
            "recall_at_5",
            "recall_at_10",
            "recall_at_20",
            "candidate_coverage_at_20",
            "relevant_candidate_retrieval_rate_at_20",
            "precision_at_5",
            "mrr",
            "ndcg_at_5",
            "ndcg_at_10",
        )
    }
    return {
        "schema_version": "1.0",
        "dataset_id": dataset["dataset_id"],
        "dataset_sha256": hashlib.sha256(dataset_path.read_bytes()).hexdigest(),
        "status": "SYNTHETIC_BASELINE_ONLY",
        "configuration": {
            "ranker": "ml.semantic_matching.hybrid.rank_candidates",
            "method": "token_jaccard_baseline",
            "candidate_text": "title and abstract concatenated; absent fields omitted",
            "candidate_depth": RETRIEVAL_DEPTH,
            "ranking_metrics_depth": [5, 10],
            "relevance_positive_threshold": 1,
            "ndcg_gain": "2^grade - 1",
            "tie_breaking": "stable input order from existing rank_candidates implementation",
            "deduplication": "shared research-record DOI/record-ID key; duplicate labels must agree",
        },
        "dataset_summary": {
            "query_count": query_count,
            "query_group_count": len(dataset["cases"]),
            "catalog_record_count": len(raw_candidates),
            "unique_candidate_count": dataset["construction"]["unique_work_count"],
            "unique_candidates_returned_at_20_across_queries": len({
                item["candidate_id"] for result in query_results
                for item in result["top_20"]
            }),
            "unique_works_per_query": query_results[0]["candidate_count"],
            "candidates_per_query_min": min(row["candidate_count"] for row in query_results),
            "candidates_per_query_max": max(row["candidate_count"] for row in query_results),
            "relevance_label_counts": {
                str(grade): label_counts[grade] for grade in range(4)
            },
        },
        "candidate_generation_metrics": {
            key: average_metrics[key]
            for key in (
                "recall_at_5",
                "recall_at_10",
                "recall_at_20",
                "candidate_coverage_at_20",
                "relevant_candidate_retrieval_rate_at_20",
            )
        },
        "ranking_metrics": {
            key: average_metrics[key]
            for key in ("precision_at_5", "mrr", "ndcg_at_5", "ndcg_at_10")
        },
        "ranking_consistency": {
            "all_repeated_runs_identical": all(
                row["ranking_consistency"]["repeat_is_identical"]
                for row in query_results
            ),
            "mean_pairwise_order_agreement_vs_reversed_input": _rounded(
                sum(consistency_scores) / len(consistency_scores)
            ),
            "input_order_sensitive_tie_query_count": tie_sensitive_query_count,
            "tie_group_count": sum(
                row["ranking_consistency"]["tie_group_count"] for row in query_results
            ),
        },
        "false_positives_at_5": false_positives,
        "false_negatives_at_20": false_negatives,
        "queries": query_results,
        "interpretation": (
            "These deterministic metrics evaluate a fixed synthetic candidate pool and "
            "the existing lexical ranker only. They do not measure live OpenAlex query "
            "recall, scientific relevance, institutional performance, plagiarism, or "
            "funding decisions."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate the deterministic synthetic graded retrieval dataset."
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = evaluate_dataset(args.dataset)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(rendered, end="")


if __name__ == "__main__":
    main()
