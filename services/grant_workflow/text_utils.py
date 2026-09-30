"""Deterministic text helpers shared by RFP extraction and screening."""
import re
from dataclasses import dataclass
from itertools import pairwise

from services.evidence.citations import CitationLocator, validate_citation
from services.ingestion.document import ExtractedDocument, ExtractedPage

STOPWORDS = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "been", "by", "can", "each", "for", "from", "has",
    "have", "in", "into", "is", "it", "its", "of", "on", "or", "our", "that", "the", "their", "them",
    "these", "this", "those", "to", "was", "we", "were", "which", "will", "with", "within", "per",
    "any", "all", "least", "one", "more", "than", "not", "must", "shall", "should", "may", "other",
    "such", "also", "both", "only",
})

_SENTENCE = re.compile(r"(?<=[.!?;])\s+(?=[A-Z0-9(])")
_NUMBERED_HEADING = re.compile(r"^(\d+(?:\.\d+)*)[.)]?\s+([A-Z][^.!?]{1,80})$")


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE.split(text) if s.strip()]


def is_heading(line: str) -> bool:
    if len(line) > 90 or line.endswith((".", ";", ",", ":")):
        return False
    if _NUMBERED_HEADING.match(line):
        return True
    letters = [c for c in line if c.isalpha()]
    return len(line.split()) <= 8 and bool(letters) and all(c.isupper() for c in letters)


def heading_label(line: str) -> str:
    match = _NUMBERED_HEADING.match(line)
    return match.group(2).strip() if match else line.strip()


@dataclass(frozen=True)
class LineContext:
    page_number: int
    line: str
    section: str | None


def iter_lines(document: ExtractedDocument) -> list[LineContext]:
    section: str | None = None
    result: list[LineContext] = []
    for page in document.pages:
        for line in page.lines:
            if is_heading(line):
                section = heading_label(line)
                continue
            result.append(LineContext(page.page_number, line, section))
    return result


def _section_before(page: ExtractedPage, offset: int, fallback: str | None) -> str | None:
    position, section = 0, fallback
    for line in page.lines:
        if position > offset:
            break
        if is_heading(line):
            section = heading_label(line)
        position += len(line) + 1
    return section


@dataclass(frozen=True)
class LocatedSpan:
    page_number: int
    section: str | None
    start: int
    end: int
    text: str
    citation_locator: str
    citation_valid: bool


def locate_span(document: ExtractedDocument, snippet: str, *, version: int = 1) -> LocatedSpan | None:
    """Find an exact span in the document and validate it with the existing citation checker."""
    snippet = snippet.strip()
    if not snippet:
        return None
    carried: str | None = None
    for page in document.pages:
        index = page.text.find(snippet)
        if index < 0:
            index = page.text.lower().find(snippet.lower())
        if index >= 0:
            text = page.text[index:index + len(snippet)]
            citation = CitationLocator(document.source_id, version, page.page_number, index, index + len(text), text)
            return LocatedSpan(
                page.page_number,
                _section_before(page, index, carried),
                index,
                index + len(text),
                text,
                citation.locator,
                validate_citation(document, citation),
            )
        for line in page.lines:
            if is_heading(line):
                carried = heading_label(line)
    return None


_CURRENCY = r"(RWF|FRW|USD|US\$|\$|EUR|€|GBP|£|KES|UGX|TZS)"
_NUMBER = r"(\d{1,3}(?:[,\s]\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
_AMOUNT_PATTERNS = (
    re.compile(_CURRENCY + r"\s?" + _NUMBER + r"\s*(million|m\b|k\b|thousand)?", re.IGNORECASE),
    re.compile(_NUMBER + r"\s*(million|m\b|k\b|thousand)?\s*" + _CURRENCY, re.IGNORECASE),
)
_CURRENCY_ALIASES = {"FRW": "RWF", "US$": "USD", "$": "USD", "€": "EUR", "£": "GBP"}


@dataclass(frozen=True)
class Amount:
    value: float
    currency: str
    text: str


def _scale(unit: str | None) -> float:
    unit = (unit or "").lower()
    if unit in {"million", "m"}:
        return 1_000_000
    if unit in {"k", "thousand"}:
        return 1_000
    return 1


def parse_amounts(text: str) -> list[Amount]:
    amounts: list[tuple[int, Amount]] = []
    for pattern_index, pattern in enumerate(_AMOUNT_PATTERNS):
        for match in pattern.finditer(text):
            if pattern_index == 0:
                currency, number, unit = match.group(1), match.group(2), match.group(3)
            else:
                number, unit, currency = match.group(1), match.group(2), match.group(3)
            value = float(re.sub(r"[,\s]", "", number)) * _scale(unit)
            code = _CURRENCY_ALIASES.get(currency.upper(), currency.upper())
            amounts.append((match.start(), Amount(value, code, match.group().strip())))
    amounts.sort(key=lambda item: item[0])
    return [amount for _, amount in amounts]


_DURATION = re.compile(r"(\d+(?:\.\d+)?)\s*(?:-\s*)?(months?|years?)\b", re.IGNORECASE)


@dataclass(frozen=True)
class Duration:
    months: float
    text: str


def parse_durations(text: str) -> list[Duration]:
    result = []
    for match in _DURATION.finditer(text):
        value = float(match.group(1))
        months = value * 12 if match.group(2).lower().startswith("year") else value
        result.append(Duration(months, match.group()))
    return result


def content_words(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z\-]+", text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 2]


def shared_concepts(left: str, right: str, limit: int = 6) -> list[str]:
    """Shared content bigrams (then unigrams) as human-readable matching concepts."""
    def bigrams(words: list[str]) -> list[str]:
        return [f"{a} {b}" for a, b in pairwise(words)]

    left_words, right_words = content_words(left), content_words(right)
    right_bigrams = set(bigrams(right_words))
    concepts: list[str] = []
    for bigram in bigrams(left_words):
        if bigram in right_bigrams and bigram not in concepts:
            concepts.append(bigram)
    if len(concepts) < limit:
        covered = {word for concept in concepts for word in concept.split()}
        right_set = set(right_words)
        for word in left_words:
            if word in right_set and word not in covered and word not in concepts and len(word) > 4:
                concepts.append(word)
            if len(concepts) >= limit:
                break
    return concepts[:limit]


def normalize_for_match(text: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", " ", text.lower()).split())
