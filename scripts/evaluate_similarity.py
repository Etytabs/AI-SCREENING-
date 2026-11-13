import argparse
import json
from pathlib import Path

from ml.semantic_matching.duplication import compare_proposals, profile_proposal


def evaluate_dataset(dataset_path: Path) -> dict:
    dataset = json.loads(dataset_path.read_text())
    cases = dataset["cases"]
    if not cases:
        raise ValueError("similarity dataset must contain cases")

    results = []
    true_positive = false_positive = false_negative = true_negative = 0
    for case in cases:
        score = compare_proposals(
            profile_proposal(case["application_text"]),
            profile_proposal(case["source_text"]),
        )
        predicted = score.match_type != "NO_SIGNIFICANT_SIMILARITY"
        expected = case["expected_signal"]
        if expected and predicted:
            true_positive += 1
        elif expected:
            false_negative += 1
        elif predicted:
            false_positive += 1
        else:
            true_negative += 1
        results.append({
            "case_id": case["case_id"],
            "category": case["category"],
            "expected_signal": expected,
            "predicted_signal": predicted,
            "match_type": score.match_type,
            "score": round(score.score, 4),
            "application_coverage": round(score.query_coverage, 4),
            "source_coverage": round(score.source_coverage, 4),
        })

    predicted_positive = true_positive + false_positive
    actual_positive = true_positive + false_negative
    return {
        "schema_version": "0.1",
        "dataset_id": dataset["dataset_id"],
        "status": dataset["status"],
        "case_count": len(cases),
        "category_counts": {
            category: sum(1 for case in cases if case["category"] == category)
            for category in sorted({case["category"] for case in cases})
        },
        "metrics": {
            "precision": true_positive / predicted_positive if predicted_positive else 0.0,
            "recall": true_positive / actual_positive if actual_positive else 0.0,
            "true_positive": true_positive,
            "false_positive": false_positive,
            "false_negative": false_negative,
            "true_negative": true_negative,
        },
        "mean_application_coverage": sum(
            item["application_coverage"] for item in results
        ) / len(results),
        "mean_source_coverage": sum(
            item["source_coverage"] for item in results
        ) / len(results),
        "false_positive_case_ids": [
            item["case_id"] for item in results
            if not item["expected_signal"] and item["predicted_signal"]
        ],
        "false_negative_case_ids": [
            item["case_id"] for item in results
            if item["expected_signal"] and not item["predicted_signal"]
        ],
        "cases": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate synthetic proposal similarity cases.")
    parser.add_argument("--dataset", default="data/evaluation/similarity_benchmark.json")
    parser.add_argument("--output")
    args = parser.parse_args()

    result = evaluate_dataset(Path(args.dataset))
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered)
    print(rendered, end="")


if __name__ == "__main__":
    main()
