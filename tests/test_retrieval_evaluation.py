import json
from pathlib import Path

import pytest

from ml.evaluation.retrieval import (
    evaluate_retrieval,
    mean_reciprocal_rank,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)


def test_retrieval_metrics_for_known_ranking():
    ranked = ["a", "b", "c", "d"]
    relevant = {"c", "d"}

    assert recall_at_k(ranked, relevant, 3) == 0.5
    assert precision_at_k(ranked, relevant, 3) == pytest.approx(1 / 3)
    assert mean_reciprocal_rank(ranked, relevant) == pytest.approx(1 / 3)
    assert ndcg_at_k(ranked, relevant, 3) == pytest.approx(0.3065735963827292)


def test_evaluate_retrieval_returns_all_metrics():
    result = evaluate_retrieval(["a", "b", "c"], {"b"}, k=2)

    assert result.recall_at_k == 1.0
    assert result.precision_at_k == 0.5
    assert result.mrr == 0.5
    assert result.ndcg_at_k == pytest.approx(0.6309297535714575)


def test_retrieval_metrics_validate_inputs():
    with pytest.raises(ValueError):
        recall_at_k(["a", "a"], {"a"}, 2)
    with pytest.raises(ValueError):
        precision_at_k(["a"], set(), 1)
    with pytest.raises(ValueError):
        ndcg_at_k(["a"], {"a"}, 0)


def test_synthetic_benchmark_is_present_and_labelled():
    path = Path("data/evaluation/retrieval_benchmark.json")
    data = json.loads(path.read_text())

    assert data["status"] == "SYNTHETIC_DEMO_ONLY"
    assert len(data["cases"]) == 4
    assert all(case["relevant_candidate_ids"] for case in data["cases"])
