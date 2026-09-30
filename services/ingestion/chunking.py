from dataclasses import dataclass
import hashlib


@dataclass(frozen=True)
class DocumentChunk:
    chunk_id: str
    source_id: str
    text: str
    ordinal: int


def chunk_text(
    text: str,
    source_id: str,
    max_chars: int = 1200,
    overlap_words: int = 30,
) -> list[DocumentChunk]:
    if max_chars <= 0 or overlap_words < 0:
        raise ValueError("max_chars must be positive and overlap_words non-negative")
    words = text.split()
    chunks, start, ordinal = [], 0, 0
    while start < len(words):
        current, size, end = [], 0, start
        while end < len(words):
            extra = len(words[end]) + (1 if current else 0)
            if current and size + extra > max_chars:
                break
            current.append(words[end])
            size += extra
            end += 1
        chunk = " ".join(current)
        digest = hashlib.sha256(
            f"{source_id}:{ordinal}:{chunk}".encode()
        ).hexdigest()[:16]
        chunks.append(DocumentChunk(digest, source_id, chunk, ordinal))
        if end >= len(words):
            break
        start = max(start + 1, end - overlap_words)
        ordinal += 1
    return chunks
