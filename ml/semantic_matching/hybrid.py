from dataclasses import dataclass
from typing import Protocol

from ml.semantic_matching.embedding import cosine_similarity
from ml.semantic_matching.service import compare_texts


class TextEmbedder(Protocol):
    model_name: str

    def encode(self, texts: list[str]) -> list[list[float]]:
        ...


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", revision: str | None = None) -> None:
        self.model_name = model_name
        self.revision = revision
        self._model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            kwargs = {"revision": self.revision} if self.revision else {}
            self._model = SentenceTransformer(self.model_name, **kwargs)
        return self._model

    def encode(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._load().encode(texts, normalize_embeddings=True)
        return [vector.tolist() for vector in vectors]


@dataclass(frozen=True)
class HybridMatch:
    lexical_score: float
    semantic_score: float | None
    fused_score: float
    method: str
    explanation: str


def hybrid_compare(
    left: str,
    right: str,
    *,
    embedder: TextEmbedder | None = None,
    lexical_weight: float = 0.35,
    semantic_weight: float = 0.65,
) -> HybridMatch:
    if not 0.0 <= lexical_weight <= 1.0:
        raise ValueError("lexical_weight must be between 0 and 1")
    if not 0.0 <= semantic_weight <= 1.0:
        raise ValueError("semantic_weight must be between 0 and 1")
    if abs((lexical_weight + semantic_weight) - 1.0) > 1e-9:
        raise ValueError("lexical_weight and semantic_weight must sum to 1")

    lexical = compare_texts(left, right)
    if embedder is None:
        return HybridMatch(
            lexical_score=lexical.score,
            semantic_score=None,
            fused_score=lexical.score,
            method="lexical_only",
            explanation="Semantic model unavailable; lexical score is retained explicitly.",
        )

    vectors = embedder.encode([left, right])
    if len(vectors) != 2:
        raise ValueError("embedder must return one vector per input text")
    semantic = cosine_similarity(vectors[0], vectors[1])
    semantic = max(0.0, min(1.0, semantic))
    fused = (lexical.score * lexical_weight) + (semantic * semantic_weight)
    return HybridMatch(
        lexical_score=lexical.score,
        semantic_score=semantic,
        fused_score=fused,
        method=f"hybrid:{embedder.model_name}",
        explanation="Fused lexical overlap with sentence-embedding cosine similarity.",
    )


@dataclass(frozen=True)
class RankedCandidate:
    candidate_id: str
    lexical_score: float
    semantic_score: float | None
    fused_score: float
    rank: int
    method: str


def rank_candidates(
    query: str,
    candidates: list[tuple[str, str]],
    *,
    embedder: TextEmbedder | None = None,
    top_k: int = 10,
    lexical_weight: float = 0.35,
    semantic_weight: float = 0.65,
) -> list[RankedCandidate]:
    if top_k < 1:
        raise ValueError("top_k must be positive")
    if not 0.0 <= lexical_weight <= 1.0:
        raise ValueError("lexical_weight must be between 0 and 1")
    if not 0.0 <= semantic_weight <= 1.0:
        raise ValueError("semantic_weight must be between 0 and 1")
    if abs((lexical_weight + semantic_weight) - 1.0) > 1e-9:
        raise ValueError("lexical_weight and semantic_weight must sum to 1")

    if embedder is None:
        ranked = [
            (candidate_id, hybrid_compare(query, text, embedder=None, lexical_weight=lexical_weight, semantic_weight=semantic_weight))
            for candidate_id, text in candidates
        ]
    else:
        texts = [query, *(text for _, text in candidates)]
        vectors = embedder.encode(texts)
        if len(vectors) != len(texts):
            raise ValueError("embedder must return one vector per input text")
        query_vector = vectors[0]
        ranked = []
        for index, (candidate_id, text) in enumerate(candidates, start=1):
            lexical = compare_texts(query, text)
            semantic = max(0.0, min(1.0, cosine_similarity(query_vector, vectors[index])))
            fused = (lexical.score * lexical_weight) + (semantic * semantic_weight)
            ranked.append((candidate_id, HybridMatch(lexical.score, semantic, fused, f"hybrid:{embedder.model_name}", "Fused lexical overlap with sentence-embedding cosine similarity.")))

    ranked.sort(key=lambda item: item[1].fused_score, reverse=True)
    return [
        RankedCandidate(candidate_id, match.lexical_score, match.semantic_score, match.fused_score, index, match.method)
        for index, (candidate_id, match) in enumerate(ranked[:top_k], start=1)
    ]
