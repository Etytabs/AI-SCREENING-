import json
from pathlib import Path
from typing import Any

from services.research_sources.models import record_deduplication_key


def load_dataset(path: Path) -> dict[str, Any]:
    dataset = json.loads(path.read_text())
    validate_dataset(dataset)
    return dataset


def validate_dataset(dataset: dict[str, Any]) -> None:
    if dataset.get("schema_version") != "1.0":
        raise ValueError("unsupported retrieval evaluation dataset schema")
    if dataset.get("status") != "SYNTHETIC_EVALUATION_ONLY":
        raise ValueError("retrieval evaluation dataset must be marked synthetic")
    candidates = dataset.get("candidates")
    cases = dataset.get("cases")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("dataset candidates must be a non-empty list")
    if not isinstance(cases, list) or not cases:
        raise ValueError("dataset cases must be a non-empty list")

    candidate_ids: set[str] = set()
    for candidate in candidates:
        candidate_id = candidate.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id.strip():
            raise ValueError("each candidate must have a non-empty candidate_id")
        if candidate_id in candidate_ids:
            raise ValueError(f"duplicate candidate_id: {candidate_id}")
        candidate_ids.add(candidate_id)
        for field in ("title", "abstract", "doi"):
            if candidate.get(field) is not None and not isinstance(candidate[field], str):
                raise ValueError(f"{candidate_id}.{field} must be a string or null")

    case_ids: set[str] = set()
    query_ids: set[str] = set()
    for case in cases:
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id.strip() or case_id in case_ids:
            raise ValueError("each case must have a unique non-empty case_id")
        case_ids.add(case_id)
        _validate_judgment(case.get("default_judgment"), case_id)
        variants = case.get("query_variants")
        if not isinstance(variants, list) or not variants:
            raise ValueError(f"{case_id} must have at least one query variant")
        for variant in variants:
            query_id = variant.get("query_id")
            text = variant.get("text")
            if not isinstance(query_id, str) or not query_id.strip() or query_id in query_ids:
                raise ValueError(f"{case_id} has a missing or duplicate query_id")
            if not isinstance(text, str) or not text.strip():
                raise ValueError(f"{query_id} must have non-empty query text")
            query_ids.add(query_id)

        judgments = case.get("judgments")
        if not isinstance(judgments, list):
            raise ValueError(f"{case_id}.judgments must be a list")
        judgment_ids: set[str] = set()
        for judgment in judgments:
            candidate_id = judgment.get("candidate_id")
            if candidate_id not in candidate_ids:
                raise ValueError(f"{case_id} references unknown candidate {candidate_id!r}")
            if candidate_id in judgment_ids:
                raise ValueError(f"{case_id} has duplicate judgment for {candidate_id}")
            judgment_ids.add(candidate_id)
            _validate_judgment(judgment, f"{case_id}/{candidate_id}")

        labels = {
            candidate_id: {
                "grade": case["default_judgment"]["grade"],
                "rationale": case["default_judgment"]["rationale"],
            }
            for candidate_id in candidate_ids
        }
        labels.update({item["candidate_id"]: item for item in judgments})
        duplicate_labels: dict[str, int] = {}
        for candidate in candidates:
            key = record_deduplication_key(candidate["candidate_id"], candidate.get("doi"))
            grade = labels[candidate["candidate_id"]]["grade"]
            if key in duplicate_labels and duplicate_labels[key] != grade:
                raise ValueError(
                    f"{case_id} assigns inconsistent relevance to duplicate work {key}"
                )
            duplicate_labels[key] = grade

    declared = dataset.get("construction", {})
    if declared.get("catalog_record_count") != len(candidates):
        raise ValueError("construction.catalog_record_count does not match candidate catalog")
    unique_count = len({
        record_deduplication_key(item["candidate_id"], item.get("doi"))
        for item in candidates
    })
    if declared.get("unique_work_count") != unique_count:
        raise ValueError("construction.unique_work_count does not match deduplicated catalog")
    if declared.get("query_group_count") != len(cases):
        raise ValueError("construction.query_group_count does not match cases")
    if declared.get("query_variant_count") != len(query_ids):
        raise ValueError("construction.query_variant_count does not match query variants")


def _validate_judgment(judgment: Any, label: str) -> None:
    if not isinstance(judgment, dict):
        raise ValueError(f"{label} must have a relevance judgment")
    grade = judgment.get("grade")
    if type(grade) is not int or grade not in range(4):
        raise ValueError(f"{label} relevance grade must be an integer from 0 to 3")
    rationale = judgment.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        raise ValueError(f"{label} must have a non-empty relevance rationale")


def expand_judgments(case: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    labels = {
        candidate["candidate_id"]: dict(case["default_judgment"])
        for candidate in candidates
    }
    labels.update({item["candidate_id"]: item for item in case["judgments"]})
    return labels


def deduplicate_candidates(
    candidates: list[dict[str, Any]],
    labels: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    unique: list[dict[str, Any]] = []
    deduplicated_labels: dict[str, dict[str, Any]] = {}
    seen: dict[str, str] = {}
    for candidate in candidates:
        candidate_id = candidate["candidate_id"]
        key = record_deduplication_key(candidate_id, candidate.get("doi"))
        if key in seen:
            canonical_id = seen[key]
            if labels[candidate_id]["grade"] != deduplicated_labels[canonical_id]["grade"]:
                raise ValueError(f"duplicate work {key} has conflicting relevance grades")
            continue
        seen[key] = candidate_id
        unique.append(candidate)
        deduplicated_labels[candidate_id] = labels[candidate_id]
    return unique, deduplicated_labels
