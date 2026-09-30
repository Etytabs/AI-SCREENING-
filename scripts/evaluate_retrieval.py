import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from ml.evaluation.benchmark import BenchmarkCase, evaluate_benchmark
from ml.semantic_matching.embedding import EmbeddingConfig, get_runtime_embedder


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
) -> dict:
    data = json.loads(dataset_path.read_text())
    cases = load_cases(dataset_path)
    config = EmbeddingConfig.from_env()
    embedder = get_runtime_embedder()

    results = {
        "schema_version": "0.1",
        "dataset_id": data["dataset_id"],
        "evaluated_at_utc": datetime.now(UTC).isoformat(),
        "k": k,
        "embedding": {
            "enabled": config.enabled,
            "model": config.model_name if config.enabled else None,
            "revision": config.revision,
        },
        "strategies": {},
    }

    for method in methods:
        if method in {"embedding", "hybrid"} and embedder is None:
            results["strategies"][method] = {
                "status": "not_run",
                "reason": "Embedding runtime is disabled. Set AI_SCREENING_EMBEDDINGS_ENABLED=true.",
            }
            continue

        result = evaluate_benchmark(cases, method=method, embedder=embedder, k=k)
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
    parser = argparse.ArgumentParser(description="Evaluate AI-SCREENING retrieval strategies.")
    parser.add_argument("--dataset", default="data/evaluation/retrieval_benchmark.json")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument(
        "--methods",
        nargs="+",
        choices=("lexical", "embedding", "hybrid"),
        default=("lexical", "embedding", "hybrid"),
    )
    parser.add_argument("--output", default="data/evaluation/retrieval_results.json")
    args = parser.parse_args()

    results = evaluate_dataset(Path(args.dataset), methods=args.methods, k=args.k)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
