from dataclasses import dataclass
import math


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
