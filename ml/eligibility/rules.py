import dataclasses


STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_UNKNOWN = "UNKNOWN"
STATUS_REVIEW = "REVIEW"


@dataclasses.dataclass(frozen=True)
class EligibilityRule:
    criterion_id: str
    label: str
    field: str
    expected: object
    evidence_required: bool = True
    missing_status: str = STATUS_UNKNOWN


@dataclasses.dataclass(frozen=True)
class EligibilityCheck:
    criterion: str
    label: str
    status: str
    passed: bool | None
    evidence: str
    observed: object = None


def _validate_rule(rule: EligibilityRule) -> None:
    if rule.missing_status not in {STATUS_UNKNOWN, STATUS_REVIEW}:
        raise ValueError("missing_status must be UNKNOWN or REVIEW")


def evaluate_rules(
    attributes: dict[str, object],
    rules: list[EligibilityRule] | dict[str, object],
) -> list[EligibilityCheck]:
    if isinstance(rules, dict):
        rules = [
            EligibilityRule(
                criterion_id=criterion,
                label=criterion,
                field=criterion,
                expected=expected,
            )
            for criterion, expected in rules.items()
        ]

    results: list[EligibilityCheck] = []
    for rule in rules:
        _validate_rule(rule)
        if rule.field not in attributes or attributes[rule.field] is None:
            results.append(
                EligibilityCheck(
                    criterion=rule.criterion_id,
                    label=rule.label,
                    status=rule.missing_status,
                    passed=None,
                    observed=None,
                    evidence=f"no observed value for field={rule.field!r}",
                )
            )
            continue

        actual = attributes[rule.field]
        passed = actual == rule.expected
        status = STATUS_PASS if passed else STATUS_FAIL
        results.append(
            EligibilityCheck(
                criterion=rule.criterion_id,
                label=rule.label,
                status=status,
                passed=passed,
                observed=actual,
                evidence=(
                    f"observed={actual!r}; expected={rule.expected!r}; "
                    f"field={rule.field!r}"
                ),
            )
        )
    return results
