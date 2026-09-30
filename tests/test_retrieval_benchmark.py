import json
from pathlib import Path

import pytest

from ml.evaluation.benchmark import BenchmarkCase, evaluate_benchmark
from ml.semantic_matching.hybrid import rank_candidates_semantic


class BenchmarkEmbedder:
    model_name = "benchmark-embedder-v1"

    def encode(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            lowered = text.lower()
            if "maize" in lowered or "crop disease" in lowered:
                vectors.append([1.0, 0.0, 0.0])
            elif "maternal" in lowered:
                vectors.append([0.0, 1.0, 0.0])
            elif "water quality" in lowered:
                vectors.append([0.0, 0.0, 1.0])
            else:
                vectors.append([0.0, 0.0, 0.0])
        return vectors


def load_cases() -> list[BenchmarkCase]:
    data = json.loads(Path("data/evaluation/retrieval_benchmark.json").read_text())
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


def test_benchmark_uses_actual_lexical_pipeline():
    result = evaluate_benchmark(load_cases(), method="lexical", k=5)
    assert result.query_count == 4
    assert result.metrics.recall_at_k == 1.0
    assert result.metrics.mrr == pytest.approx(1.0)


def test_embedding_and_hybrid_share_real_ranking_interfaces():
    embedder = BenchmarkEmbedder()
    embedding = evaluate_benchmark(load_cases(), method="embedding", embedder=embedder, k=5)
    hybrid = evaluate_benchmark(load_cases(), method="hybrid", embedder=embedder, k=5)
    assert embedding.query_count == hybrid.query_count == 4
    assert embedding.metrics.recall_at_k == 1.0
    assert hybrid.metrics.recall_at_k == 1.0


def test_semantic_ranker_produces_embedding_method():
    ranked = rank_candidates_semantic(
        "machine learning crop disease",
        [("a", "crop disease"), ("b", "maternal health")],
        embedder=BenchmarkEmbedder(),
        top_k=2,
    )
    assert ranked[0].candidate_id == "a"
    assert ranked[0].method == "embedding:benchmark-embedder-v1"
