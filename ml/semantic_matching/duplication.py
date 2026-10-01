"""Deterministic proposal matching, separate from shared eligibility similarity.

Scores are overlap measures, not calibrated probabilities. All narrative text is
examined; an inverted passage index avoids the former first-250-sentences limit.
"""
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass

EXACT = "EXACT_DUPLICATE"
SUBSTANTIAL = "SUBSTANTIAL_SIMILARITY"
POSSIBLE = "POSSIBLE_SIMILARITY"
NONE = "NO_SIGNIFICANT_SIMILARITY"
SEVERITY = {EXACT: 3, SUBSTANTIAL: 2, POSSIBLE: 1, NONE: 0}

_WORDS = re.compile(r"[^\W_]+", re.UNICODE)
_BREAK = re.compile(r"[\n\r\f]+|(?<=[.!?;])\s+")
_ADMIN = re.compile(
    r"^(?:title|project title|applicant|applicant name|email|telephone|phone|address|"
    r"institution(?: type)?|country|domain|requested amount|duration|reference|"
    r"application reference|principal investigator|organisation|organization)\s*:", re.I,
)
_FORM = re.compile(
    r"^(?:(?:please\s+)?(?:describe|provide|enter|insert|list|outline|summarise|summarize)\b|"
    r"(?:i|we)\s+(?:hereby\s+)?(?:declare|certify)\b|"
    r"(?:this (?:proposal|document) is|synthetic demonstration)\b|"
    r"informed consent will be obtained\b)", re.I,
)
_HEADINGS = frozenset({
    "summary", "abstract", "objectives", "methodology", "research question", "dataset",
    "expected outcomes", "workplan", "declaration", "budget", "background",
    "application and intervention", "intervention and partners", "ethics clearance plan",
})
_STOP = frozenset("""
a an and are as at be been being by can could did do does for from had has have how
i if in into is it its may might more most must no not of on or our shall should
so such than that the their them these they this those through to under up used
using was we were what when where whether which while who will with within would
you your each all any both only also one two per least other then there about
project proposal research study work approach methodology objective objectives
aim aims include includes including develop developed development use uses
planned plan planning activity activities outcome outcomes result results
funding grant applicant application institution duration months year years
""".split())


def normalized_words(text: str) -> tuple[str, ...]:
    return tuple(_WORDS.findall(unicodedata.normalize("NFKC", text).casefold()))


def _content(text: str) -> tuple[str, ...]:
    return tuple(word for word in normalized_words(text) if len(word) > 2 and word not in _STOP)


@dataclass(frozen=True)
class Passage:
    text: str
    terms: tuple[str, ...]


@dataclass
class ProposalProfile:
    normalized: tuple[str, ...]
    terms: tuple[str, ...]
    passages: list[Passage]
    shingles: dict[tuple[str, ...], list[int]]
    passage_index: dict[str, set[int]]

    @property
    def assessable(self) -> bool:
        return len(self.terms) >= 8 and len(set(self.terms)) >= 6


def profile_proposal(text: str) -> ProposalProfile:
    passages: list[Passage] = []
    all_terms: list[str] = []
    shingles: dict[tuple[str, ...], list[int]] = defaultdict(list)
    passage_index: dict[str, set[int]] = defaultdict(set)
    for segment in _BREAK.split(text):
        segment = segment.strip()
        heading = re.sub(r"^\d+[.)]?\s*", "", segment).strip().casefold()
        if not segment or _ADMIN.match(segment) or _FORM.match(segment) or heading in _HEADINGS:
            continue
        words = list(_WORDS.finditer(segment))
        if not words:
            continue
        # Long, punctuation-free PDF paragraphs are covered with overlapping windows.
        for start in range(0, len(words), 60):
            end = min(start + 90, len(words))
            snippet = segment[words[start].start():words[end - 1].end()]
            terms = _content(snippet)
            if len(terms) >= 4:
                index = len(passages)
                passages.append(Passage(snippet, terms))
                for term in set(terms):
                    passage_index[term].add(index)
            if end == len(words):
                break
        terms = _content(segment)
        offset = len(all_terms)
        all_terms.extend(terms)
        for index in range(len(terms) - 2):
            shingles[terms[index:index + 3]].append(offset + index)
    return ProposalProfile(normalized_words(text), tuple(all_terms), passages, dict(shingles), dict(passage_index))


def _dice(left: set, right: set) -> float:
    return 2 * len(left & right) / (len(left) + len(right)) if left and right else 0.0


def _best_passages(left: ProposalProfile, right: ProposalProfile) -> tuple[str | None, str | None]:
    best = None
    best_score = (-1.0, -1)
    for passage in left.passages:
        terms = set(passage.terms)
        hits: dict[int, int] = defaultdict(int)
        for term in terms:
            for index in right.passage_index.get(term, ()):
                hits[index] += 1
        # Candidate generation examines the entire source, while bounding pair scoring.
        candidates = sorted(hits, key=lambda index: (-hits[index], index))[:8]
        left_shingles = set(zip(passage.terms, passage.terms[1:], passage.terms[2:]))
        for index in candidates:
            other = right.passages[index]
            right_shingles = set(zip(other.terms, other.terms[1:], other.terms[2:]))
            shared = len(left_shingles & right_shingles)
            score = (0.7 * _dice(left_shingles, right_shingles) + 0.3 * _dice(terms, set(other.terms)), shared)
            if score > best_score:
                best_score = score
                best = (passage.text, other.text)
    if best is not None:
        return best
    return (left.passages[0].text if left.passages else None,
            right.passages[0].text if right.passages else None)


@dataclass(frozen=True)
class DuplicationScore:
    match_type: str
    score: float
    lexical_score: float
    query_coverage: float
    source_coverage: float
    shared_terms: int
    shared_shingles: int
    query_passage: str | None
    source_passage: str | None
    query_positions: frozenset[int] = frozenset()
    query_terms: int = 0


def compare_proposals(query: ProposalProfile, source: ProposalProfile) -> DuplicationScore:
    shared = set(query.shingles) & set(source.shingles)
    query_positions, source_positions = set(), set()
    for shingle in shared:
        for position in query.shingles[shingle]:
            query_positions.update(range(position, position + 3))
        for position in source.shingles[shingle]:
            source_positions.update(range(position, position + 3))
    query_coverage = len(query_positions) / len(query.terms) if query.terms else 0.0
    source_coverage = len(source_positions) / len(source.terms) if source.terms else 0.0
    word_dice = _dice(set(query.terms), set(source.terms))
    shared_terms = len(set(query.terms) & set(source.terms))
    covered = min(len(query_positions), len(source_positions))
    low, high = sorted((query_coverage, source_coverage))
    score = 0.35 * word_dice + 0.65 * high
    match_type = NONE
    if query.assessable and source.assessable:
        if query.normalized == source.normalized:
            match_type, score = EXACT, 1.0
            query_coverage = source_coverage = 1.0
        elif shared_terms >= 12 and covered >= 20 and (low >= 0.5 or (high >= 0.8 and covered >= 30)):
            match_type = SUBSTANTIAL
        elif shared_terms >= 8 and len(shared) >= 4 and ((covered >= 12 and high >= 0.25) or covered >= 40):
            match_type = POSSIBLE
        else:
            query_pairs = set(zip(query.terms, query.terms[1:]))
            source_pairs = set(zip(source.terms, source.terms[1:]))
            # Reworded proposals need several specific phrase anchors, not topic alone.
            if shared_terms >= 20 and word_dice >= 0.72 and len(query_pairs & source_pairs) >= 6:
                match_type = POSSIBLE
    query_passage, source_passage = _best_passages(query, source)
    return DuplicationScore(match_type, score, word_dice, query_coverage, source_coverage,
                            shared_terms, len(shared), query_passage, source_passage,
                            frozenset(query_positions), len(query.terms))
