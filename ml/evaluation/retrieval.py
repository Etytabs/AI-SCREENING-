import math
from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalMetrics:
    recall_at_k: float
    precision_at_k: float
    mrr: float
    ndcg_at_k: float


def _validate_retrieval_inputs(ranked_ids: list[str], relevant_ids: set[str], k: int) -> None:
    if k < 1:
        raise ValueError("k must be positive")
    if len(set(ranked_ids)) != len(ranked_ids):
        raise ValueError("ranked_ids must not contain duplicates")
    if not relevant_ids:
        raise ValueError("relevant_ids must not be empty")


def recall_at_k(ranked_ids: list[str], relevant_ids: set[str], k: int) -> float:
    _validate_retrieval_inputs(ranked_ids, relevant_ids, k)
    return len(set(ranked_ids[:k]) & relevant_ids) / len(relevant_ids)


def precision_at_k(ranked_ids: list[str], relevant_ids: set[str], k: int) -> float:
    _validate_retrieval_inputs(ranked_ids, relevant_ids, k)
    return len(set(ranked_ids[:k]) & relevant_ids) / k


def mean_reciprocal_rank(ranked_ids: list[str], relevant_ids: set[str]) -> float:
    if not relevant_ids:
        raise ValueError("relevant_ids must not be empty")
    if len(set(ranked_ids)) != len(ranked_ids):
        raise ValueError("ranked_ids must not contain duplicates")
    for rank, candidate_id in enumerate(ranked_ids, start=1):
        if candidate_id in relevant_ids:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(ranked_ids: list[str], relevant_ids: set[str], k: int) -> float:
    _validate_retrieval_inputs(ranked_ids, relevant_ids, k)
    ideal_hits = min(len(relevant_ids), k)
    ideal_dcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
    dcg = sum(
        1.0 / math.log2(rank + 1)
        for rank, candidate_id in enumerate(ranked_ids[:k], start=1)
        if candidate_id in relevant_ids
    )
    return dcg / ideal_dcg if ideal_dcg else 0.0


def graded_ndcg_at_k(ranked_ids: list[str], relevance_by_id: dict[str, int], k: int) -> float:
    if k < 1:
        raise ValueError("k must be positive")
    if len(set(ranked_ids)) != len(ranked_ids):
        raise ValueError("ranked_ids must not contain duplicates")
    if not relevance_by_id:
        raise ValueError("relevance_by_id must contain a positive relevance grade")
    if any(type(grade) is not int or grade < 0 for grade in relevance_by_id.values()):
        raise ValueError("relevance grades must be non-negative integers")
    if not any(grade > 0 for grade in relevance_by_id.values()):
        raise ValueError("relevance_by_id must contain a positive relevance grade")
    if any(candidate_id not in relevance_by_id for candidate_id in ranked_ids):
        raise ValueError("ranked_ids must be present in relevance_by_id")

    gains = [2**grade - 1 for grade in relevance_by_id.values()]
    ideal_dcg = sum(
        gain / math.log2(rank + 1)
        for rank, gain in enumerate(sorted(gains, reverse=True)[:k], start=1)
    )
    dcg = sum(
        (2**relevance_by_id[candidate_id] - 1) / math.log2(rank + 1)
        for rank, candidate_id in enumerate(ranked_ids[:k], start=1)
    )
    return dcg / ideal_dcg if ideal_dcg else 0.0


def evaluate_retrieval(
    ranked_ids: list[str],
    relevant_ids: set[str],
    *,
    k: int = 5,
) -> RetrievalMetrics:
    return RetrievalMetrics(
        recall_at_k=recall_at_k(ranked_ids, relevant_ids, k),
        precision_at_k=precision_at_k(ranked_ids, relevant_ids, k),
        mrr=mean_reciprocal_rank(ranked_ids, relevant_ids),
        ndcg_at_k=ndcg_at_k(ranked_ids, relevant_ids, k),
    )
