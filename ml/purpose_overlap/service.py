import re
from dataclasses import dataclass
from difflib import SequenceMatcher


DIMENSIONS = (
    "research_problem",
    "objectives",
    "beneficiaries",
    "intervention",
    "methodology",
    "outputs",
    "outcomes",
    "geography_scope",
)

_HEADINGS = {
    "research_problem": ("research problem", "problem statement", "background", "rationale"),
    "objectives": ("objective", "objectives", "aim", "aims", "research question"),
    "beneficiaries": ("beneficiaries", "target population", "participants", "community"),
    "intervention": ("intervention", "solution", "approach", "application", "proposed solution"),
    "methodology": ("methodology", "methods", "method", "study design"),
    "outputs": ("outputs", "deliverables", "products"),
    "outcomes": ("outcomes", "expected outcomes", "impact"),
    "geography_scope": ("geography", "location", "scope", "study area"),
}

_STOP = frozenset("""
a an and are as at be been by for from had has have in is it its of on or
the their they this to was were with will would we our us project proposal research
study using use used develop develop improved improve objective objectives result
results work activity activities
""".split())


@dataclass(frozen=True)
class DimensionEvidence:
    dimension: str
    left_text: str
    right_text: str
    similarity: float
    status: str


@dataclass(frozen=True)
class PurposeOverlapResult:
    disposition: str
    confidence: str
    dimensions: tuple[DimensionEvidence, ...]
    summary: str
    limitations: tuple[str, ...]
    method: str


def _words(text: str) -> set[str]:
    words = re.findall(r"[^\W_]+", text.casefold(), flags=re.UNICODE)
    return {word for word in words if len(word) > 2 and word not in _STOP}


def _jaccard(left: str, right: str) -> float:
    a, b = _words(left), _words(right)
    if not a or not b:
        return 0.0
    union = a | b
    return len(a & b) / len(union) if union else 0.0


def _heading_pattern() -> tuple[re.Pattern[str], dict[str, str]]:
    aliases = {
        alias: dimension
        for dimension, terms in _HEADINGS.items()
        for alias in terms
    }
    alternatives = "|".join(
        re.escape(alias) for alias in sorted(aliases, key=len, reverse=True)
    )
    pattern = re.compile(
        rf"(?im)(?:^|[\n;,.]\s*)(?:\d+[.)]?\s*)?(?P<heading>{alternatives})\s*:\s*"
    )
    return pattern, aliases


_HEADING_PATTERN, _HEADING_DIMENSIONS = _heading_pattern()


def profile(text: str) -> dict[str, str]:
    """Extract explicitly labelled sections without borrowing adjacent sections.

    Only labelled headings are used. Unstructured text is deliberately left
    unassigned rather than guessed into a research dimension.
    """
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    matches = list(_HEADING_PATTERN.finditer(normalized))
    extracted = {dimension: "" for dimension in DIMENSIONS}

    for index, match in enumerate(matches):
        dimension = _HEADING_DIMENSIONS[match.group("heading").casefold()]
        end = matches[index + 1].start() if index + 1 < len(matches) else len(normalized)
        value = normalized[match.end():end].strip(" \t\n\r:;,.")
        if value and not extracted[dimension]:
            extracted[dimension] = value[:5000]

    return extracted


def compare_purposes(left_text: str, right_text: str) -> PurposeOverlapResult:
    left = profile(left_text)
    right = profile(right_text)
    evidence: list[DimensionEvidence] = []
    similarities: dict[str, float] = {}
    for dimension in DIMENSIONS:
        ltext, rtext = left[dimension], right[dimension]
        if ltext and rtext:
            score = max(_jaccard(ltext, rtext), SequenceMatcher(None, ltext.lower(), rtext.lower()).ratio())
            score = round(min(1.0, score), 4)
            status = "SIMILAR" if score >= 0.55 else "DIFFERENT" if score >= 0.25 else "DISTINCT"
        else:
            score = 0.0
            status = "NOT_PROVIDED"
        similarities[dimension] = score
        evidence.append(DimensionEvidence(dimension, ltext, rtext, score, status))

    provided = sum(bool(left[d]) and bool(right[d]) for d in DIMENSIONS)
    problem = similarities["research_problem"]
    objective = similarities["objectives"]
    intervention = similarities["intervention"]
    methodology = similarities["methodology"]
    strong = sum(score >= 0.55 for score in similarities.values())

    if provided < 2:
        disposition = "INSUFFICIENT_EVIDENCE"
        confidence = "LOW"
    elif strong >= 3 and objective >= 0.55 and intervention >= 0.55 and methodology >= 0.55:
        disposition = "POTENTIAL_OVERLAP"
        confidence = "MEDIUM"
    elif problem >= 0.25 and objective >= 0.25 and intervention >= 0.35:
        disposition = "POTENTIAL_OVERLAP"
        confidence = "LOW"
    elif problem >= 0.55 and (objective < 0.55 or intervention < 0.55):
        if strong >= 1:
            disposition = "DIFFERENTIATED_FOLLOW_ON"
            confidence = "MEDIUM"
        else:
            disposition = "SIMILAR_TOPIC_DIFFERENT_PURPOSE"
            confidence = "LOW"
    elif problem >= 0.35 or strong >= 2:
        disposition = "SIMILAR_TOPIC_DIFFERENT_PURPOSE"
        confidence = "MEDIUM"
    else:
        disposition = "DISTINCT_PROJECT"
        confidence = "MEDIUM"

    summary = (
        f"{disposition.replace('_', ' ').title()} based on deterministic section-level comparison. "
        f"{strong} dimension(s) met the 0.55 similarity threshold."
    )
    limitations = (
        "This is an evidence-assistive heuristic, not a trained purpose classifier.",
        "Missing or unstructured sections are reported as not provided and are not inferred.",
        "A reviewer must distinguish replication, follow-on, overlap and independent work.",
    )
    if provided < 4:
        limitations += ("Only a subset of purpose dimensions was available from the supplied text.",)
    return PurposeOverlapResult(
        disposition=disposition,
        confidence=confidence,
        dimensions=tuple(evidence),
        summary=summary,
        limitations=limitations,
        method="deterministic_section_jaccard_v1",
    )
