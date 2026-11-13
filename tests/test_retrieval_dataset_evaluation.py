import copy
import hashlib
import json
from pathlib import Path

import pytest

from ml.evaluation.retrieval import graded_ndcg_at_k
from ml.evaluation.retrieval_dataset import (
    deduplicate_candidates,
    expand_judgments,
    load_dataset,
    validate_dataset,
)
from ml.semantic_matching.hybrid import rank_candidates
from ml.semantic_matching.service import compare_texts
from scripts.evaluate_retrieval_dataset import evaluate_dataset
from services.research_sources.models import record_deduplication_key

DATASET = Path("data/evaluation/retrieval_evaluation_v1.json")


def test_expanded_synthetic_dataset_has_complete_graded_rationales():
    dataset = load_dataset(DATASET)
    assert dataset["status"] == "SYNTHETIC_EVALUATION_ONLY"
    assert len(dataset["candidates"]) == 27
    assert len(dataset["cases"]) == 6
    assert sum(len(case["query_variants"]) for case in dataset["cases"]) == 12

    for case in dataset["cases"]:
        labels = expand_judgments(case, dataset["candidates"])
        assert set(labels) == {candidate["candidate_id"] for candidate in dataset["candidates"]}
        assert all(0 <= label["grade"] <= 3 and label["rationale"] for label in labels.values())


def test_dataset_validation_rejects_missing_rationale_and_invalid_grade():
    dataset = json.loads(DATASET.read_text())
    invalid_grade = copy.deepcopy(dataset)
    invalid_grade["cases"][0]["judgments"][0]["grade"] = 4
    with pytest.raises(ValueError, match="grade must be an integer from 0 to 3"):
        validate_dataset(invalid_grade)

    missing_rationale = copy.deepcopy(dataset)
    missing_rationale["cases"][0]["judgments"][0]["rationale"] = " "
    with pytest.raises(ValueError, match="non-empty relevance rationale"):
        validate_dataset(missing_rationale)


def test_doi_duplicates_collapse_but_distinct_near_duplicate_is_retained():
    dataset = load_dataset(DATASET)
    case = dataset["cases"][0]
    labels = expand_judgments(case, dataset["candidates"])
    candidates, unique_labels = deduplicate_candidates(dataset["candidates"], labels)
    candidate_ids = {candidate["candidate_id"] for candidate in candidates}

    assert len(dataset["candidates"]) == 27
    assert len(candidates) == 25
    assert "PUB-AGR-01-DUP" not in candidate_ids
    assert "PUB-AGR-04" in candidate_ids
    assert unique_labels["PUB-AGR-01"]["grade"] == 3
    assert record_deduplication_key("a", "https://doi.org/10.5555/x") == (
        record_deduplication_key("b", "10.5555/x")
    )


def test_graded_ndcg_uses_gain_by_relevance_grade():
    ordered = graded_ndcg_at_k(
        ["high", "weak", "not-relevant"],
        {"high": 3, "weak": 1, "not-relevant": 0},
        3,
    )
    reversed_relevance = graded_ndcg_at_k(
        ["weak", "high", "not-relevant"],
        {"high": 3, "weak": 1, "not-relevant": 0},
        3,
    )
    assert ordered == 1.0
    assert 0.0 < reversed_relevance < ordered

    with pytest.raises(ValueError, match="positive relevance grade"):
        graded_ndcg_at_k(["irrelevant"], {"irrelevant": 0}, 1)
    with pytest.raises(ValueError, match="non-negative integers"):
        graded_ndcg_at_k(["invalid"], {"invalid": "high"}, 1)


def test_missing_metadata_and_abstracts_are_supported_without_dropping_candidates():
    dataset = load_dataset(DATASET)
    candidates = {candidate["candidate_id"]: candidate for candidate in dataset["candidates"]}

    assert candidates["PUB-MAT-04"]["title"]
    assert candidates["PUB-MAT-04"]["abstract"] is None
    assert candidates["PUB-EDU-04"]["title"] is None
    assert candidates["PUB-EDU-04"]["abstract"] is None

    result = evaluate_dataset(DATASET)
    assert result["dataset_summary"]["unique_works_per_query"] == 25
    assert result["dataset_summary"]["relevance_label_counts"] == {
        "0": 264,
        "1": 12,
        "2": 12,
        "3": 12,
    }


def test_retrieval_and_ranking_metrics_are_reported_separately_and_repeatably():
    first = evaluate_dataset(DATASET)
    second = evaluate_dataset(DATASET)

    assert first == second
    assert first["ranked_pool_recall_metrics"] == {
        "recall_at_5": 0.833333,
        "recall_at_10": 0.916667,
        "recall_at_20": 0.944445,
    }
    assert set(first["ranking_metrics"]) == {
        "precision_at_5",
        "mrr",
        "ndcg_at_5",
        "ndcg_at_10",
    }
    assert first["ranking_metrics"] == {
        "precision_at_5": 0.5,
        "mrr": 1.0,
        "ndcg_at_5": 0.831415,
        "ndcg_at_10": 0.864974,
    }
    assert first["evaluation_scope"] == {
        "fixed_candidate_pool_supplied_directly": True,
        "independent_candidate_generation_evaluated": False,
        "live_source_retrieval_recall_evaluated": False,
    }
    assert first["selection_depth_statistics"]["ranked_pool_fraction_at_20"] == 0.8
    assert "candidate_coverage_at_20" not in json.dumps(first)
    assert "relevant_candidate_retrieval_rate_at_20" not in json.dumps(first)
    for query in first["queries"]:
        relevant_count = query["positive_candidate_count"]
        top_20 = query["top_20"]
        for k in (5, 10, 20):
            hits = sum(item["grade"] > 0 for item in top_20[:k])
            assert query["ranked_pool_recall_metrics"][f"recall_at_{k}"] == pytest.approx(
                hits / relevant_count
            )
    assert first["ranking_consistency"]["all_repeated_runs_identical"] is True
    assert first["ranking_consistency"]["input_order_sensitive_tie_query_count"] > 0
    assert first["false_positives_at_5"]
    assert first["false_negatives_at_20"]
    assert len(first["queries"]) == 12


def test_result_artifact_and_docs_use_fixed_pool_terminology():
    artifact_path = Path("data/evaluation/retrieval_evaluation_v1_results.json")
    docs_path = Path("docs/ai-ml/retrieval-evaluation.md")
    artifact = json.loads(artifact_path.read_text())
    docs = " ".join(docs_path.read_text().split())

    assert artifact == evaluate_dataset(DATASET)
    assert artifact["dataset_sha256"] == hashlib.sha256(DATASET.read_bytes()).hexdigest()
    assert artifact["dataset_sha256"] == (
        "e79358fb35bb37f2e12adc7e435b38d0a056a67d3c5222ab3f5e1b6a6dc59a6a"
    )
    assert "ranked_pool_recall_metrics" in docs
    assert "ranked_pool_fraction_at_20" in docs
    assert "Independent candidate generation and live-source retrieval recall have not been evaluated." in docs
    assert "Independent candidate generation and live-source retrieval recall have not been evaluated." in (
        artifact["interpretation"]
    )
    assert "not a retrieval-quality measure" in (
        artifact["selection_depth_statistics"]["interpretation"]
    )
    assert "candidate_generation_metrics" not in json.dumps(artifact)
    assert "candidate_coverage_at_20" not in docs


def test_equal_scores_are_stable_for_fixed_input_and_follow_input_order():
    candidates = [("b", ""), ("a", "")]
    first = rank_candidates("no matching terms", candidates, top_k=2)
    repeat = rank_candidates("no matching terms", candidates, top_k=2)
    reversed_input = rank_candidates(
        "no matching terms",
        list(reversed(candidates)),
        top_k=2,
    )

    assert [item.candidate_id for item in first] == ["b", "a"]
    assert [item.candidate_id for item in repeat] == ["b", "a"]
    assert [item.candidate_id for item in reversed_input] == ["a", "b"]
    assert first[0].fused_score == first[1].fused_score == 0.0


def test_difficult_negative_and_low_overlap_positive_are_present():
    dataset = load_dataset(DATASET)
    case = next(case for case in dataset["cases"] if case["case_id"] == "agriculture")
    labels = {item["candidate_id"]: item for item in case["judgments"]}
    candidates = {item["candidate_id"]: item for item in dataset["candidates"]}

    assert labels["PUB-AGR-04"]["grade"] == 0
    assert "High lexical overlap" in labels["PUB-AGR-04"]["rationale"]
    assert labels["PUB-AGR-02"]["grade"] == 2
    assert "farmer" in candidates["PUB-AGR-02"]["abstract"].lower()
    query = case["query_variants"][0]["text"]
    paraphrase_text = (
        candidates["PUB-AGR-02"]["title"] + " " + candidates["PUB-AGR-02"]["abstract"]
    )
    relevant_score = compare_texts(query, paraphrase_text).score
    difficult_negative_score = compare_texts(
        query,
        candidates["PUB-AGR-04"]["title"] + " " + candidates["PUB-AGR-04"]["abstract"],
    ).score
    assert relevant_score < compare_texts(
        query,
        candidates["PUB-AGR-01"]["title"] + " " + candidates["PUB-AGR-01"]["abstract"],
    ).score
    assert difficult_negative_score == pytest.approx(relevant_score)
