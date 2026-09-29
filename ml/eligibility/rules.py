from dataclasses import dataclass


@dataclass(frozen=True)
class EligibilityCheck:
    criterion: str
    passed: bool
    evidence: str


def evaluate_rules(
    attributes: dict[str, object],
    rules: dict[str, object],
) -> list[EligibilityCheck]:
    results = []
    for criterion, expected in rules.items():
        actual = attributes.get(criterion)
        results.append(
            EligibilityCheck(
                criterion=criterion,
                passed=actual == expected,
                evidence=f"observed={actual!r}; expected={expected!r}",
            )
        )
    return results
