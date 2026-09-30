"""Novelty signal engine.

Produces an AI-assisted novelty *signal* by comparing what an application proposes
(per dimension) against an authorized comparison universe. The output is evidence for
reviewer inspection; it is never a claim of scientific novelty.
"""
import re
from dataclasses import dataclass

from ml.scoring.confidence import calibrate_confidence
from ml.semantic_matching.hybrid import TextEmbedder, rank_candidates

HIGH = "HIGH_NOVELTY_SIGNAL"
MEDIUM = "MEDIUM_NOVELTY_SIGNAL"
LOW = "LOW_NOVELTY_SIGNAL"
REVIEW_REQUIRED = "REVIEW_REQUIRED"

DIMENSION_CUES: dict[str, tuple[str, ...]] = {
    "research_question": ("research question", "we ask", "aims to", "objective", "hypothes", "investigate", "whether"),
    "methodology": ("methodology", "method", "approach", "study design", "we will use", "sampling", "survey"),
    "technology": ("technology", "sensor", "platform", "software", "device", "satellite", "drone", "mobile", "iot"),
    "application": ("application", "use case", "end users", "farmers", "households", "communities", "deploy", "beneficiar"),
    "context": ("district", "province", "region", "rural", "urban", "setting", "watershed", "basin", "catchment"),
    "dataset": ("dataset", "data set", "data collection", "records", "images", "observations", "census"),
    "intervention": ("intervention", "treatment", "programme", "program", "training", "pilot"),
    "model": ("model", "algorithm", "classifier", "neural", "regression", "simulation", "forecast"),
}

# (high_below, medium_below) similarity thresholds per scoring method.
THRESHOLDS = {"lexical": (0.15, 0.45), "hybrid": (0.45, 0.7)}
MIN_DIMENSIONS = 3

_SENTENCE = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class DimensionSignal:
    dimension: str
    statement: str
    max_similarity: float | None
    closest_source_id: str | None
    closest_statement: str | None
    signal: str


@dataclass(frozen=True)
class NoveltyAssessment:
    signal: str
    dimensions: tuple[DimensionSignal, ...]
    compared_sources: int
    method: str
    confidence: float | None
    explanation: str


def split_dimensions(text: str) -> dict[str, str]:
    found: dict[str, list[str]] = {}
    for sentence in _SENTENCE.split(text):
        lower = sentence.lower()
        for dimension, cues in DIMENSION_CUES.items():
            if any(cue in lower for cue in cues):
                found.setdefault(dimension, []).append(sentence.strip())
    return {dimension: " ".join(sentences) for dimension, sentences in found.items()}


def _signal(similarity: float, method: str) -> str:
    high_below, medium_below = THRESHOLDS[method]
    if similarity < high_below:
        return HIGH
    if similarity < medium_below:
        return MEDIUM
    return LOW


def assess_novelty(
    text: str,
    comparison_universe: list[tuple[str, str]],
    *,
    embedder: TextEmbedder | None = None,
) -> NoveltyAssessment:
    method = "hybrid" if embedder is not None else "lexical"
    method_label = f"novelty_dimensions_v0.1:{method}"
    dimensions = split_dimensions(text)

    if not comparison_universe:
        return NoveltyAssessment(
            REVIEW_REQUIRED, (), 0, method_label, None,
            "No authorized comparison sources were available; novelty cannot be assessed. "
            "This is not evidence of novelty.",
        )
    if len(dimensions) < MIN_DIMENSIONS:
        return NoveltyAssessment(
            REVIEW_REQUIRED, (), len(comparison_universe), method_label, None,
            f"Only {len(dimensions)} of {len(DIMENSION_CUES)} novelty dimensions could be "
            "identified in the application text; reviewer assessment required.",
        )

    universe_dimensions = [(source_id, split_dimensions(body)) for source_id, body in comparison_universe]
    signals: list[DimensionSignal] = []
    for dimension, statement in dimensions.items():
        candidates = [
            (source_id, parts[dimension])
            for source_id, parts in universe_dimensions
            if dimension in parts
        ]
        if not candidates:
            signals.append(DimensionSignal(dimension, statement, None, None, None, HIGH))
            continue
        best = rank_candidates(statement, candidates, embedder=embedder, top_k=1)[0]
        closest = dict(candidates)[best.candidate_id]
        signals.append(DimensionSignal(
            dimension, statement, round(best.fused_score, 4), best.candidate_id, closest,
            _signal(best.fused_score, method),
        ))

    scored = [s.max_similarity for s in signals if s.max_similarity is not None]
    mean_similarity = sum(scored) / len(scored) if scored else 0.0
    overall = _signal(mean_similarity, method)
    agreement = sum(s.signal == overall for s in signals) / len(signals)
    confidence = calibrate_confidence(
        model_score=0.75 if method == "hybrid" else 0.55,
        evidence_strength=len(dimensions) / len(DIMENSION_CUES),
        agreement=agreement,
    )
    return NoveltyAssessment(
        overall, tuple(signals), len(comparison_universe), method_label, confidence,
        f"Mean closest-match similarity {mean_similarity:.2f} across {len(signals)} dimensions "
        f"compared with {len(comparison_universe)} authorized records. This is a screening "
        "signal for reviewer inspection, not a determination of scientific novelty.",
    )
