from dataclasses import dataclass

from ml.semantic_matching.hybrid import TextEmbedder, rank_candidates
from services.ingestion.document import ExtractedDocument


@dataclass(frozen=True)
class EvidenceCandidate:
    chunk_id: str
    page_number: int
    text: str
    score: float
    rank: int


def select_evidence(
    query: str,
    document: ExtractedDocument,
    *,
    embedder: TextEmbedder | None = None,
    top_k: int = 3,
) -> list[EvidenceCandidate]:
    candidates = [
        (f"{document.source_id}:p{page.page_number}", page.text)
        for page in document.pages
        if page.text.strip()
    ]
    ranked = rank_candidates(query, candidates, embedder=embedder, top_k=top_k)
    by_id = {candidate_id: text for candidate_id, text in candidates}
    return [
        EvidenceCandidate(
            chunk_id=item.candidate_id,
            page_number=int(item.candidate_id.rsplit("p", 1)[1]),
            text=by_id[item.candidate_id],
            score=item.fused_score,
            rank=item.rank,
        )
        for item in ranked
    ]
