from dataclasses import dataclass

from ml.evaluation.retrieval import RetrievalMetrics, evaluate_retrieval
from ml.semantic_matching.hybrid import TextEmbedder, rank_candidates, rank_candidates_semantic


@dataclass(frozen=True)
class BenchmarkCase:
    query_id: str
    query: str
    candidates: tuple[tuple[str, str], ...]
    relevant_candidate_ids: frozenset[str]


@dataclass(frozen=True)
class BenchmarkResult:
    method: str
    k: int
    query_count: int
    metrics: RetrievalMetrics


def rank_benchmark_case(
    case: BenchmarkCase,
    *,
    method: str,
    embedder: TextEmbedder | None = None,
    k: int = 5,
) -> list[str]:
    if method == "lexical":
        ranked = rank_candidates(case.query, list(case.candidates), embedder=None, top_k=k)
    elif method == "embedding":
        if embedder is None:
            raise ValueError("embedding evaluation requires an embedder")
        ranked = rank_candidates_semantic(case.query, list(case.candidates), embedder=embedder, top_k=k)
    elif method == "hybrid":
        if embedder is None:
            raise ValueError("hybrid evaluation requires an embedder")
        ranked = rank_candidates(case.query, list(case.candidates), embedder=embedder, top_k=k)
    else:
        raise ValueError(f"unsupported retrieval method: {method}")
    return [item.candidate_id for item in ranked]


def evaluate_benchmark(
    cases: list[BenchmarkCase],
    *,
    method: str,
    embedder: TextEmbedder | None = None,
    k: int = 5,
) -> BenchmarkResult:
    if not cases:
        raise ValueError("cases must not be empty")
    per_case = [
        evaluate_retrieval(
            rank_benchmark_case(case, method=method, embedder=embedder, k=k),
            set(case.relevant_candidate_ids),
            k=k,
        )
        for case in cases
    ]
    count = len(per_case)
    metrics = RetrievalMetrics(
        recall_at_k=sum(item.recall_at_k for item in per_case) / count,
        precision_at_k=sum(item.precision_at_k for item in per_case) / count,
        mrr=sum(item.mrr for item in per_case) / count,
        ndcg_at_k=sum(item.ndcg_at_k for item in per_case) / count,
    )
    return BenchmarkResult(method=method, k=k, query_count=count, metrics=metrics)
