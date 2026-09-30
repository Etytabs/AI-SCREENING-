from dataclasses import dataclass
from typing import Protocol


DEFAULT_RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class CrossEncoderReranker(Protocol):
    model_name: str

    def score(self, query: str, candidates: list[tuple[str, str]]) -> list[float]:
        ...


class SentenceTransformerCrossEncoder:
    def __init__(
        self,
        model_name: str = DEFAULT_RERANKER_MODEL,
        revision: str | None = None,
    ) -> None:
        self.model_name = model_name
        self.revision = revision
        self._model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import CrossEncoder

            kwargs = {"revision": self.revision} if self.revision else {}
            self._model = CrossEncoder(self.model_name, **kwargs)
        return self._model

    def score(self, query: str, candidates: list[tuple[str, str]]) -> list[float]:
        if not candidates:
            return []
        pairs = [(query, text) for _, text in candidates]
        scores = self._load().predict(pairs)
        return [float(score) for score in scores]


@dataclass(frozen=True)
class RerankedCandidate:
    candidate_id: str
    reranker_score: float
    first_stage_score: float
    rank: int
    method: str


def rerank_candidates(
    query: str,
    candidates: list[tuple[str, str, float]],
    *,
    reranker: CrossEncoderReranker,
    top_k: int = 5,
) -> list[RerankedCandidate]:
    if top_k < 1:
        raise ValueError("top_k must be positive")
    if not candidates:
        return []

    pairs = [(candidate_id, text) for candidate_id, text, _ in candidates]
    scores = reranker.score(query, pairs)
    if len(scores) != len(candidates):
        raise ValueError("reranker must return one score per candidate")

    ranked = sorted(
        zip(candidates, scores),
        key=lambda item: item[1],
        reverse=True,
    )
    return [
        RerankedCandidate(
            candidate_id=candidate_id,
            reranker_score=float(score),
            first_stage_score=first_stage_score,
            rank=rank,
            method=f"cross_encoder:{reranker.model_name}",
        )
        for rank, ((candidate_id, _, first_stage_score), score) in enumerate(
            ranked[:top_k],
            start=1,
        )
    ]
