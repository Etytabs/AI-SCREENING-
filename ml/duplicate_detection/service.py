from dataclasses import dataclass
from ml.semantic_matching.service import compare_texts

@dataclass(frozen=True)
class DuplicateCandidate:
    left_id: str
    right_id: str
    similarity: float
    method: str

def find_candidate(left_id: str, left_text: str, right_id: str, right_text: str) -> DuplicateCandidate:
    result = compare_texts(left_text, right_text)
    return DuplicateCandidate(left_id, right_id, result.score, result.method)
