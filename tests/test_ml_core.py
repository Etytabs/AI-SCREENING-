from ml.duplicate_detection.service import find_candidate
from ml.eligibility.rules import (
    STATUS_FAIL,
    STATUS_PASS,
    STATUS_REVIEW,
    STATUS_UNKNOWN,
    EligibilityRule,
    evaluate_rules,
)
from ml.entity_resolution.service import match_authors
from ml.evaluation.metrics import binary_accuracy
from ml.plagiarism.overlap import token_overlap
from ml.semantic_matching.embedding import cosine_similarity


def test_cosine_similarity_identical_vectors():
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0


def test_duplicate_candidate():
    result = find_candidate("a", "same publication", "b", "same publication")
    assert result.similarity == 1.0


def test_author_match():
    result = match_authors("a", "Jane Doe", "b", "jane doe")
    assert result.score == 1.0
    assert result.matched_fields == ("name",)


def test_overlap():
    result = token_overlap("AI research platform", "AI research")
    assert result.shared_tokens == 2
    assert result.overlap_ratio > 0


def test_accuracy():
    assert binary_accuracy([True, False, True], [True, True, True]) == 2 / 3


def test_eligibility_missing_values_are_not_failures():
    rules = [
        EligibilityRule("C01", "Institution", "eligible_institution", True, missing_status=STATUS_UNKNOWN),
        EligibilityRule("C02", "Scope", "within_scope", True, missing_status=STATUS_REVIEW),
    ]
    result = evaluate_rules({}, rules)

    assert [item.status for item in result] == [STATUS_UNKNOWN, STATUS_REVIEW]
    assert [item.passed for item in result] == [None, None]


def test_eligibility_distinguishes_pass_and_fail():
    rules = [EligibilityRule("C01", "Institution", "eligible_institution", True)]
    result = evaluate_rules({"eligible_institution": False}, rules)

    assert result[0].status == STATUS_FAIL
    assert result[0].passed is False

    result = evaluate_rules({"eligible_institution": True}, rules)
    assert result[0].status == STATUS_PASS
    assert result[0].passed is True
