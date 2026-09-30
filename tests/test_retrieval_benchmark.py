import json
from pathlib import Path

import pytest

from ml.evaluation.benchmark import BenchmarkCase, evaluate_benchmark
from ml.semantic_matching.hybrid import rank_candidates_semantic
from ml.semantic_matching.reranker import (
    DEFAULT_RERANKER_MODEL,
    RerankerConfig,
    rerank_candidates,
)
from scripts.evaluate_retrieval import evaluate_dataset


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


class BenchmarkReranker:
    model_name = "benchmark-cross-encoder-v1"

    def score(self, query: str, candidates: list[tuple[str, str]]) -> list[float]:
        query_terms = set(query.lower().split())
        return [
            float(len(query_terms & set(text.lower().split())))
            for _, text in candidates
        ]


def load_cases(path: str = "data/evaluation/retrieval_benchmark.json") -> list[BenchmarkCase]:
    data = json.loads(Path(path).read_text())
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


def test_cross_encoder_reranker_changes_order_using_pair_scores():
    reranked = rerank_candidates(
        "crop disease detection",
        [
            ("a", "unrelated crop topic", 0.9),
            ("b", "crop disease detection", 0.4),
        ],
        reranker=BenchmarkReranker(),
        top_k=2,
    )
    assert [item.candidate_id for item in reranked] == ["b", "a"]
    assert reranked[0].method == "cross_encoder:benchmark-cross-encoder-v1"
    assert reranked[0].first_stage_score == 0.4


def test_hybrid_reranked_uses_first_stage_pool():
    cases = load_cases()
    result = evaluate_benchmark(
        cases,
        method="hybrid_reranked",
        embedder=BenchmarkEmbedder(),
        reranker=BenchmarkReranker(),
        k=5,
        rerank_k=3,
    )
    assert result.query_count == 4
    assert 0.0 <= result.metrics.mrr <= 1.0


def test_reranker_config_defaults_to_disabled(monkeypatch):
    monkeypatch.delenv("AI_SCREENING_RERANKER_ENABLED", raising=False)
    monkeypatch.delenv("AI_SCREENING_RERANKER_MODEL", raising=False)
    monkeypatch.delenv("AI_SCREENING_RERANKER_REVISION", raising=False)
    config = RerankerConfig.from_env()
    assert config.enabled is False
    assert config.model_name == DEFAULT_RERANKER_MODEL
    assert config.revision is None


def test_benchmark_runner_reports_disabled_models(monkeypatch):
    monkeypatch.setenv("AI_SCREENING_EMBEDDINGS_ENABLED", "false")
    monkeypatch.setenv("AI_SCREENING_RERANKER_ENABLED", "false")
    result = evaluate_dataset(
        Path("data/evaluation/retrieval_benchmark_adversarial.json"),
        methods=["lexical", "embedding", "hybrid", "hybrid_reranked"],
        k=5,
        rerank_k=5,
    )
    assert result["strategies"]["lexical"]["status"] == "completed"
    assert result["strategies"]["embedding"]["status"] == "not_run"
    assert result["strategies"]["hybrid"]["status"] == "not_run"
    assert result["strategies"]["hybrid_reranked"]["status"] == "not_run"


def test_adversarial_benchmark_has_harder_cases():
    cases = load_cases("data/evaluation/retrieval_benchmark_adversarial.json")
    assert len(cases) == 10
    assert any(
        case.query.lower().split()[0] not in case.candidates[0][1].lower()
        for case in cases
    )
    assert any(len(case.relevant_candidate_ids) > 1 for case in cases)
    assert all(len(case.candidates) >= 5 for case in cases)
