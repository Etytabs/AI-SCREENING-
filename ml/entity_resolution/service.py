from dataclasses import dataclass


@dataclass(frozen=True)
class EntityMatch:
    left_id: str
    right_id: str
    score: float
    matched_fields: tuple[str, ...]


def match_authors(
    left_id: str,
    left_name: str,
    right_id: str,
    right_name: str,
) -> EntityMatch:
    def normalize(value: str) -> str:
        return " ".join(value.lower().split())
    left, right = normalize(left_name), normalize(right_name)
    score = 1.0 if left == right else 0.0
    fields = ("name",) if score == 1.0 else ()
    return EntityMatch(left_id, right_id, score, fields)
