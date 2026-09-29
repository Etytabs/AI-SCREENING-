from ml.entity_resolution.service import match_authors
from ml.semantic_matching.service import compare_texts

def reconcile_text(left_id: str, left: str, right_id: str, right: str) -> dict:
    match = compare_texts(left, right)
    return {
        "left_record_id": left_id,
        "right_record_id": right_id,
        "similarity": match.score,
        "method": match.method,
        "explanation": match.explanation,
    }

def reconcile_publication(
    left_id: str,
    left_title: str,
    left_author: str,
    right_id: str,
    right_title: str,
    right_author: str,
) -> dict:
    title_match = compare_texts(left_title, right_title)
    author_match = match_authors(left_id, left_author, right_id, right_author)
    return {
        "left_record_id": left_id,
        "right_record_id": right_id,
        "title_similarity": title_match.score,
        "author_similarity": author_match.score,
        "matched_author_fields": list(author_match.matched_fields),
    }
