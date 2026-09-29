from dataclasses import dataclass

@dataclass(frozen=True)
class MatchResult:
    score: float
    method: str
    explanation: str

def compare_texts(left: str, right: str) -> MatchResult:
    a, b = set(left.lower().split()), set(right.lower().split())
    union = a | b
    score = len(a & b) / len(union) if union else 0.0
    return MatchResult(
        score=score,
        method="token_jaccard_baseline",
        explanation="Baseline lexical overlap; production can use embeddings.",
    )
