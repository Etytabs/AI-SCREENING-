from dataclasses import dataclass

@dataclass(frozen=True)
class OverlapResult:
    overlap_ratio: float
    shared_tokens: int
    method: str

def token_overlap(left: str, right: str) -> OverlapResult:
    left_tokens, right_tokens = set(left.lower().split()), set(right.lower().split())
    shared = left_tokens & right_tokens
    denominator = min(len(left_tokens), len(right_tokens))
    ratio = len(shared) / denominator if denominator else 0.0
    return OverlapResult(ratio, len(shared), "set_token_overlap")
