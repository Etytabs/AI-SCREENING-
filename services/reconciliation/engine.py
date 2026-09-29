from ml.semantic_matching.service import MatchResult, compare_texts

def reconcile_text(left_id: str, left: str, right_id: str, right: str) -> dict:
    match: MatchResult = compare_texts(left, right)
    return {
        "left_record_id": left_id,
        "right_record_id": right_id,
        "similarity": match.score,
        "method": match.method,
        "explanation": match.explanation,
    }
