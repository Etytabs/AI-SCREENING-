import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol

DEFAULT_RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


@dataclass(frozen=True)
class RerankerConfig:
    model_name: str = DEFAULT_RERANKER_MODEL
    revision: str | None = None
    enabled: bool = False

    @classmethod
    def from_env(cls) -> "RerankerConfig":
        enabled = os.getenv("AI_SCREENING_RERANKER_ENABLED", "false").strip().lower()
        revision = os.getenv("AI_SCREENING_RERANKER_REVISION", "").strip() or None
        return cls(
            model_name=(
                os.getenv("AI_SCREENING_RERANKER_MODEL", DEFAULT_RERANKER_MODEL).strip()
                or DEFAULT_RERANKER_MODEL
            ),
            revision=revision,
            enabled=enabled in {"1", "true", "yes", "on"},
        )


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


@lru_cache(maxsize=2)
def create_reranker(config: RerankerConfig) -> CrossEncoderReranker | None:
    if not config.enabled:
        return None
    return SentenceTransformerCrossEncoder(
        model_name=config.model_name,
        revision=config.revision,
    )


def get_runtime_reranker() -> CrossEncoderReranker | None:
    return create_reranker(RerankerConfig.from_env())


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
