from dataclasses import dataclass

from ml.semantic_matching.hybrid import TextEmbedder, rank_candidates
from services.ingestion.chunking import chunk_text
from services.ingestion.document import ExtractedDocument


@dataclass(frozen=True)
class EvidenceCandidate:
    chunk_id: str
    page_number: int
    text: str
    score: float
    rank: int
    lexical_score: float
    semantic_score: float | None
    method: str


def _page_chunks(document: ExtractedDocument) -> list[tuple[str, int, str]]:
    chunks: list[tuple[str, int, str]] = []
    for page in document.pages:
        if not page.text.strip():
            continue
        page_chunks = chunk_text(
            page.text,
            source_id=f"{document.source_id}:p{page.page_number}",
        )
        chunks.extend(
            (chunk.chunk_id, page.page_number, chunk.text)
            for chunk in page_chunks
        )
    return chunks


def select_evidence(
    query: str,
    document: ExtractedDocument,
    *,
    embedder: TextEmbedder | None = None,
    top_k: int = 3,
) -> list[EvidenceCandidate]:
    chunks = _page_chunks(document)
    candidates = [(chunk_id, text) for chunk_id, _, text in chunks]
    ranked = rank_candidates(query, candidates, embedder=embedder, top_k=top_k)
    metadata = {chunk_id: (page_number, text) for chunk_id, page_number, text in chunks}
    return [
        EvidenceCandidate(
            chunk_id=item.candidate_id,
            page_number=metadata[item.candidate_id][0],
            text=metadata[item.candidate_id][1],
            score=item.fused_score,
            rank=item.rank,
            lexical_score=item.lexical_score,
            semantic_score=item.semantic_score,
            method=item.method,
        )
        for item in ranked
    ]
