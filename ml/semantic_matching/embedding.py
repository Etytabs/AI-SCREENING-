import math
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ml.semantic_matching.hybrid import TextEmbedder


DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


@dataclass(frozen=True)
class EmbeddingConfig:
    model_name: str = DEFAULT_EMBEDDING_MODEL
    enabled: bool = False

    @classmethod
    def from_env(cls) -> "EmbeddingConfig":
        enabled = os.getenv("AI_SCREENING_EMBEDDINGS_ENABLED", "false").strip().lower()
        return cls(
            model_name=os.getenv("AI_SCREENING_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL).strip()
            or DEFAULT_EMBEDDING_MODEL,
            enabled=enabled in {"1", "true", "yes", "on"},
        )


def embedding_model_name(config: EmbeddingConfig | None = None) -> str:
    return (config or EmbeddingConfig()).model_name


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        raise ValueError("Vectors must have the same non-zero dimension.")
    dot = sum(a * b for a, b in zip(left, right))
    norm_left = math.sqrt(sum(a * a for a in left))
    norm_right = math.sqrt(sum(b * b for b in right))
    if norm_left == 0 or norm_right == 0:
        return 0.0
    return dot / (norm_left * norm_right)


@lru_cache(maxsize=4)
def create_embedder(config: EmbeddingConfig) -> "TextEmbedder | None":
    if not config.enabled:
        return None
    from ml.semantic_matching.hybrid import SentenceTransformerEmbedder

    return SentenceTransformerEmbedder(model_name=config.model_name)


def get_runtime_embedder() -> "TextEmbedder | None":
    return create_embedder(EmbeddingConfig.from_env())
