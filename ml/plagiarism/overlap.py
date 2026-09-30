import re
from dataclasses import dataclass


@dataclass(frozen=True)
class OverlapResult:
    overlap_ratio: float
    shared_tokens: int
    method: str


def token_overlap(left: str, right: str) -> OverlapResult:
    left_tokens, right_tokens = set(left.lower().split()), set(right.lower().split())
    shared = left_tokens & right_tokens
    denominator = min(len(left_tokens), len(right_tokens))
    ratio = len(shared) / denominator if denominator else 0.0
    return OverlapResult(ratio, len(shared), "set_token_overlap")


@dataclass(frozen=True)
class SharedPassage:
    left_text: str
    right_text: str
    word_count: int
    exact: bool


@dataclass(frozen=True)
class PassageOverlap:
    passages: tuple[SharedPassage, ...]
    left_coverage: float
    method: str


_WORD = re.compile(r"\S+")


def _normalize_word(word: str) -> str:
    return re.sub(r"[^\w]", "", word.lower())


def shared_passages(left: str, right: str, *, shingle_size: int = 8) -> PassageOverlap:
    """Find maximal word runs shared by two texts using word shingles.

    Words are compared after lowercasing and stripping punctuation, so a passage is
    reported as ``exact`` only when the original surface text is identical.
    """
    if shingle_size < 2:
        raise ValueError("shingle_size must be at least 2")
    left_spans = [(m.group(), m.start(), m.end()) for m in _WORD.finditer(left)]
    right_spans = [(m.group(), m.start(), m.end()) for m in _WORD.finditer(right)]
    left_words = [_normalize_word(w) for w, _, _ in left_spans]
    right_words = [_normalize_word(w) for w, _, _ in right_spans]
    if len(left_words) < shingle_size or len(right_words) < shingle_size:
        return PassageOverlap((), 0.0, f"word_shingle_{shingle_size}")

    right_index: dict[tuple[str, ...], list[int]] = {}
    for i in range(len(right_words) - shingle_size + 1):
        right_index.setdefault(tuple(right_words[i:i + shingle_size]), []).append(i)

    covered = [False] * len(left_words)
    passages: list[SharedPassage] = []
    i = 0
    while i <= len(left_words) - shingle_size:
        starts = right_index.get(tuple(left_words[i:i + shingle_size]))
        if not starts:
            i += 1
            continue
        best_len, best_j = 0, starts[0]
        for j in starts:
            length = 0
            while (
                i + length < len(left_words)
                and j + length < len(right_words)
                and left_words[i + length] == right_words[j + length]
            ):
                length += 1
            if length > best_len:
                best_len, best_j = length, j
        left_text = left[left_spans[i][1]:left_spans[i + best_len - 1][2]]
        right_text = right[right_spans[best_j][1]:right_spans[best_j + best_len - 1][2]]
        passages.append(SharedPassage(left_text, right_text, best_len, left_text == right_text))
        for k in range(i, i + best_len):
            covered[k] = True
        i += best_len

    coverage = sum(covered) / len(left_words)
    return PassageOverlap(tuple(passages), coverage, f"word_shingle_{shingle_size}")
