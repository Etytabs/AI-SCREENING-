import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from ml.evaluation.benchmark import BenchmarkCase, evaluate_benchmark
from ml.semantic_matching.embedding import EmbeddingConfig, get_runtime_embedder
from ml.semantic_matching.reranker import RerankerConfig, get_runtime_reranker


def load_cases(path: Path) -> list[BenchmarkCase]:
    data = json.loads(path.read_text())
    return [
        BenchmarkCase(
            query_id=item["query_id"],
            query=item["query"],
            candidates=tuple(
                (candidate["candidate_id"], candidate["text"])
                for candidate in item["candidates"]
            ),
            relevant_candidate_ids=frozenset(item["relevant_candidate_ids"]),
        )
        for item in data["cases"]
    ]


def evaluate_dataset(
    dataset_path: Path,
    *,
    methods: list[str],
    k: int,
    rerank_k: int,
) -> dict:
    data = json.loads(dataset_path.read_text())
    cases = load_cases(dataset_path)
    embedding_config = EmbeddingConfig.from_env()
    reranker_config = RerankerConfig.from_env()
    embedder = get_runtime_embedder()
    reranker = get_runtime_reranker()

    results = {
        "schema_version": "0.2",
        "dataset_id": data["dataset_id"],
        "evaluated_at_utc": datetime.now(UTC).isoformat(),
        "k": k,
        "rerank_k": rerank_k,
        "embedding": {
            "enabled": embedding_config.enabled,
            "model": embedding_config.model_name if embedding_config.enabled else None,
            "revision": embedding_config.revision,
        },
        "reranker": {
            "enabled": reranker_config.enabled,
            "model": reranker_config.model_name if reranker_config.enabled else None,
            "revision": reranker_config.revision,
        },
        "strategies": {},
    }

    for method in methods:
        if method in {"embedding", "hybrid", "hybrid_reranked"} and embedder is None:
            results["strategies"][method] = {
                "status": "not_run",
                "reason": (
                    "Embedding runtime is disabled. "
                    "Set AI_SCREENING_EMBEDDINGS_ENABLED=true."
                ),
            }
            continue
        if method == "hybrid_reranked" and reranker is None:
            results["strategies"][method] = {
                "status": "not_run",
                "reason": (
                    "Cross-encoder runtime is disabled. "
                    "Set AI_SCREENING_RERANKER_ENABLED=true."
                ),
            }
            continue

        result = evaluate_benchmark(
            cases,
            method=method,
            embedder=embedder,
            reranker=reranker,
            k=k,
            rerank_k=rerank_k,
        )
        results["strategies"][method] = {
            "status": "completed",
            "query_count": result.query_count,
            "recall_at_k": result.metrics.recall_at_k,
            "precision_at_k": result.metrics.precision_at_k,
            "mrr": result.metrics.mrr,
            "ndcg_at_k": result.metrics.ndcg_at_k,
        }

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate shakaHive retrieval strategies.")
    parser.add_argument("--dataset", default="data/evaluation/retrieval_benchmark.json")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--rerank-k", type=int, default=5)
    parser.add_argument(
        "--methods",
        nargs="+",
        choices=("lexical", "embedding", "hybrid", "hybrid_reranked"),
        default=("lexical", "embedding", "hybrid", "hybrid_reranked"),
    )
    parser.add_argument("--output", default="data/evaluation/retrieval_results.json")
    args = parser.parse_args()

    results = evaluate_dataset(
        Path(args.dataset),
        methods=args.methods,
        k=args.k,
        rerank_k=args.rerank_k,
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
