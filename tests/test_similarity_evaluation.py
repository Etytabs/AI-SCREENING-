from pathlib import Path

from scripts.evaluate_similarity import evaluate_dataset


def test_synthetic_similarity_benchmark_reports_false_positive_and_negative_cases():
    result = evaluate_dataset(Path("data/evaluation/similarity_benchmark.json"))

    assert result["status"] == "SYNTHETIC_DIAGNOSTIC_ONLY"
    assert result["case_count"] == 10
    assert result["metrics"]["true_positive"] + result["metrics"]["false_negative"] == 4
    assert result["metrics"]["false_positive"] + result["metrics"]["true_negative"] == 6
    assert result["metrics"]["precision"] <= 1
    assert result["metrics"]["recall"] <= 1
    assert any(item["category"] == "asymmetric_source_application_overlap" for item in result["cases"])
